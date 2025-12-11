from ..core.platform_registry import AiWebPlatform
from ..core.session_manager import SessionManager

class PortalJsBridge:
    """
    Handles the logic for messages received from the JavaScript environment.
    In the native Android architecture, this would be an object with @JavascriptInterface methods.
    In Toga, this acts as the handler delegate for those events.
    """
    def __init__(self, platform: AiWebPlatform, session_manager: SessionManager):
        self.platform = platform
        self.session_manager = session_manager

    def on_platform_user_message_detected(self, text: str):
        """Called when the user types directly into the platform UI (or via DOM observation)."""
        self.session_manager.on_platform_user_message(self.platform.id, text)

    def on_platform_ai_message_detected(self, text: str):
        """Called when the AI generates a response."""
        self.session_manager.on_platform_ai_message(self.platform.id, text)

    def on_live_transcript_chunk_detected(self, text: str):
        """Called when a live transcript chunk is captured."""
        self.session_manager.on_live_transcript_chunk(self.platform.id, text)

    def on_live_mode_state_changed(self, active: bool):
        """Called when live mode is toggled."""
        self.session_manager.on_live_mode_changed(self.platform.id, active)
