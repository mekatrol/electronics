import unittest
from unittest.mock import patch

from kipy.errors import ApiError

from modules.shared.kicad_ipc import retry_when_kicad_busy


class RetryWhenKiCadBusyTests(unittest.TestCase):
    def test_retries_busy_responses_until_operation_succeeds(self):
        outcomes = iter(
            [
                ApiError("KiCad is busy and cannot respond to API requests right now"),
                ApiError("KiCad is busy and cannot respond to API requests right now"),
                "zones",
            ]
        )

        def operation():
            outcome = next(outcomes)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        with (
            patch("modules.shared.kicad_ipc.time.sleep") as sleep,
            patch("modules.shared.kicad_ipc.print"),
        ):
            self.assertEqual(
                retry_when_kicad_busy(operation, attempts=6, delay_seconds=0.5),
                "zones",
            )
        self.assertEqual(sleep.call_count, 2)

    def test_does_not_retry_unrelated_api_errors(self):
        error = ApiError("document is unavailable")

        with (
            patch("modules.shared.kicad_ipc.time.sleep") as sleep,
            self.assertRaisesRegex(ApiError, "document is unavailable"),
        ):
            retry_when_kicad_busy(
                lambda: (_ for _ in ()).throw(error),
                attempts=6,
                delay_seconds=0.5,
            )
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
