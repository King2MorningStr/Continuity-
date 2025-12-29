import unittest

from udac_portal.session_manager import SessionManager
from udac_portal.interaction_logger import InteractionLogger


class _FakeLogger:
    def __init__(self):
        self.events = []
        self.shutdown_called = False

    def log_session_start(self, platform_id: str, thread_id: str):
        self.events.append(("start", platform_id, thread_id))

    def log_session_end(self, platform_id: str, thread_id: str):
        self.events.append(("end", platform_id, thread_id))

    def shutdown(self):
        self.shutdown_called = True


class TestSessionRecording(unittest.TestCase):
    def test_session_start_and_end_are_logged(self):
        manager = SessionManager()
        fake_logger = _FakeLogger()
        manager._logger = fake_logger

        session = manager.start_session("chatgpt")

        self.assertEqual(len(fake_logger.events), 1)
        self.assertEqual(fake_logger.events[0][0], "start")
        self.assertEqual(fake_logger.events[0][1], "chatgpt")
        self.assertEqual(fake_logger.events[0][2], session.thread_id)

        manager.shutdown()

        self.assertTrue(fake_logger.shutdown_called)
        self.assertEqual(fake_logger.events[-1][0], "end")
        self.assertEqual(fake_logger.events[-1][1], "chatgpt")

    def test_injection_delivery_event_records_context(self):
        logger = InteractionLogger()

        logger.log_injection_delivery(
            platform_id="claude",
            enriched_text="hello with context",
            tokens_added=42,
            thread_id="claude_1",
            context_sources=["chatgpt", "claude"],
            success=True,
        )

        self.assertGreaterEqual(len(logger.events), 1)
        event = logger.events[-1]
        self.assertEqual(event.event_type, "injection_delivery")
        self.assertEqual(event.platform_id, "claude")
        self.assertEqual(event.tokens_added, 42)
        self.assertListEqual(event.context_sources, ["chatgpt", "claude"])


if __name__ == "__main__":
    unittest.main()
