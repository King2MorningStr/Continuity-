from dataclasses import dataclass
from typing import Optional

@dataclass
class AiWebPlatform:
    id: str
    name: str
    base_url: str
    input_selector: str
    send_selector: Optional[str]
    user_message_selector: str
    ai_message_selector: str
    transcript_selector: Optional[str] = None
    live_mode_indicator_selector: Optional[str] = None

class PlatformRegistry:
    def __init__(self):
        self.platforms = {}
        self._initialize_defaults()

    def _initialize_defaults(self):
        # Example default platforms
        self.register(AiWebPlatform(
            id="chatgpt",
            name="ChatGPT",
            base_url="https://chat.openai.com",
            input_selector="#prompt-textarea",
            send_selector="[data-testid='send-button']",
            user_message_selector=".user-message", # Placeholder
            ai_message_selector=".ai-message" # Placeholder
        ))
        self.register(AiWebPlatform(
            id="claude",
            name="Claude",
            base_url="https://claude.ai",
            input_selector=".ProseMirror",
            send_selector="button[aria-label='Send']",
            user_message_selector=".font-user-message", # Placeholder
            ai_message_selector=".font-claude-message" # Placeholder
        ))
        self.register(AiWebPlatform(
            id="gemini",
            name="Gemini",
            base_url="https://gemini.google.com",
            input_selector=".ql-editor",
            send_selector=".send-button",
            user_message_selector=".user-query", # Placeholder
            ai_message_selector=".model-response" # Placeholder
        ))

    def register(self, platform: AiWebPlatform):
        self.platforms[platform.id] = platform

    def get(self, platform_id: str) -> Optional[AiWebPlatform]:
        return self.platforms.get(platform_id)

    def get_all(self):
        return list(self.platforms.values())
