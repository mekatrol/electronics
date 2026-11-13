"""Asynchronous, bounded, process-group-aware module execution."""

from __future__ import annotations

import asyncio
import os
import signal
from collections.abc import Callable
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
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        """Schedule a validated command and return immediately to the caller."""
        self.store.save(record)
        task = asyncio.create_task(
            self._execute(record, command, cwd, timeout, mutates_kicad, on_finished)
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
        on_finished: Callable[[], None] | None,
    ) -> None:
        lock = self._mutation_lock if mutates_kicad else _NullAsyncLock()
        try:
            async with self._limit, lock:
                record.status = RunStatus.RUNNING
                record.started_at = datetime.now(UTC)
                self.store.save(record)
                with (
                    self.store.stdout(record.id).open("wb") as stdout,
                    self.store.stderr(record.id).open("wb") as stderr,
                ):
                    # A new session lets cancellation and timeout terminate the entire
                    # descendant process group rather than leaving tool children behind.
                    process = await asyncio.create_subprocess_exec(
                        *command,
                        cwd=cwd,
                        stdout=stdout,
                        stderr=stderr,
                        start_new_session=True,
                    )
                    self._processes[record.id] = process
                    try:
                        record.exit_code = await asyncio.wait_for(
                            process.wait(), timeout
                        )
                        record.status = (
                            RunStatus.SUCCEEDED
                            if record.exit_code == 0
                            else RunStatus.FAILED
                        )
                    except TimeoutError:
                        os.killpg(process.pid, signal.SIGTERM)
                        await process.wait()
                        record.status = RunStatus.TIMED_OUT
                        record.error_summary = f"Execution exceeded {timeout} seconds."
        except asyncio.CancelledError:
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
            if on_finished:
                on_finished()


class _NullAsyncLock:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_args: object) -> None:
        return None
