"""Asynchronous, bounded, process-group-aware module execution."""

from __future__ import annotations

import asyncio
import os
import signal
from datetime import UTC, datetime
from pathlib import Path

from .models import RunRecord, RunStatus
from .persistence import RunStore


class ProcessRunner:
    """Run approved commands with timeouts, cancellation, and mutation locking."""

    def __init__(self, store: RunStore, max_concurrent: int = 2):
        self.store = store
        self._limit = asyncio.Semaphore(max_concurrent)
        self._mutation_lock = asyncio.Lock()
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    def submit(
        self,
        record: RunRecord,
        *,
        command: list[str],
        cwd: Path,
        timeout: int,
        mutates_kicad: bool,
    ) -> None:
        """Schedule a validated command and return immediately to the caller."""
        self.store.save(record)
        task = asyncio.create_task(
            self._execute(record, command, cwd, timeout, mutates_kicad)
        )
        self._tasks[record.id] = task

    async def cancel(self, run_id: str) -> RunRecord:
        """Terminate a queued or running process group and return its record."""
        record = self.store.get(run_id)
        if record.status not in (RunStatus.QUEUED, RunStatus.RUNNING):
            return record
        process = self._processes.get(run_id)
        if process and process.returncode is None:
            os.killpg(process.pid, signal.SIGTERM)
        task = self._tasks.get(run_id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        return self.store.get(run_id)

    async def _execute(
        self,
        record: RunRecord,
        command: list[str],
        cwd: Path,
        timeout: int,
        mutates_kicad: bool,
    ) -> None:
        lock = self._mutation_lock if mutates_kicad else _NullAsyncLock()
        try:
            async with self._limit, lock:
                record.status = RunStatus.RUNNING
                record.started_at = datetime.now(UTC)
                self.store.save(record)
                # Pipes keep output ephemeral; a new session lets cancellation and
                # timeout terminate the complete descendant process group.
                process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=cwd,
                    env={
                        **os.environ,
                        "PYTHONPATH": os.pathsep.join(
                            filter(None, (str(cwd), os.environ.get("PYTHONPATH", "")))
                        ),
                    },
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    start_new_session=True,
                )
                self._processes[record.id] = process
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout
                    )
                    self.store.set_output(record.id, stdout, stderr)
                    record.exit_code = process.returncode
                    record.status = (
                        RunStatus.SUCCEEDED
                        if record.exit_code == 0
                        else RunStatus.FAILED
                    )
                except TimeoutError:
                    os.killpg(process.pid, signal.SIGTERM)
                    stdout, stderr = await process.communicate()
                    self.store.set_output(record.id, stdout, stderr)
                    record.status = RunStatus.TIMED_OUT
                    record.error_summary = f"Execution exceeded {timeout} seconds."
        except asyncio.CancelledError:
            cancelled_process = self._processes.get(record.id)
            if cancelled_process is not None:
                stdout, stderr = await cancelled_process.communicate()
                self.store.set_output(record.id, stdout, stderr)
            record.status = RunStatus.CANCELLED
            record.error_summary = "Cancelled by the user."
            raise
        except (OSError, ValueError) as exc:
            record.status = RunStatus.FAILED
            record.error_summary = str(exc)
        finally:
            record.finished_at = datetime.now(UTC)
            self.store.save(record)
            self._processes.pop(record.id, None)
            self._tasks.pop(record.id, None)


class _NullAsyncLock:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_args: object) -> None:
        return None
