"""
Platform Registry - AI Platform Definitions
============================================
Defines all supported AI platforms and their DOM selectors for message capture/injection.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
import json
import os
from pathlib import Path

# Try to import platformdirs, fallback to temp directory
try:
    from platformdirs import user_data_dir
    APP_NAME = "UDAC Portal"
    APP_AUTHOR = "Sunni"
    STORAGE_DIR = user_data_dir(APP_NAME, APP_AUTHOR)
except ImportError:
    # Fallback when platformdirs not available
    import tempfile
    STORAGE_DIR = os.path.join(tempfile.gettempdir(), "udac_portal")
try:
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)
except Exception:
    pass  # Silent fail - will try again when actually needed


@dataclass
class AiWebPlatform:
    """Descriptor for an AI web platform."""
    id: str
    name: str
    base_url: str
    icon: str  # Emoji or icon identifier
    
    # DOM Selectors for interaction
    input_selector: str
    send_selector: Optional[str] = None
    user_message_selector: str = ""
    ai_message_selector: str = ""
    transcript_selector: Optional[str] = None
    live_mode_indicator_selector: Optional[str] = None
    
    # Platform state
    enabled: bool = True
    supports_voice: bool = False
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "icon": self.icon,
            "input_selector": self.input_selector,
            "send_selector": self.send_selector,
            "user_message_selector": self.user_message_selector,
            "ai_message_selector": self.ai_message_selector,
            "transcript_selector": self.transcript_selector,
            "live_mode_indicator_selector": self.live_mode_indicator_selector,
            "enabled": self.enabled,
            "supports_voice": self.supports_voice,
        }
    
    @staticmethod
    def from_dict(data: dict) -> "AiWebPlatform":
        return AiWebPlatform(**data)


# ============================================================================
# DEFAULT PLATFORM DEFINITIONS
# ============================================================================

CHATGPT = AiWebPlatform(
    id="chatgpt",
    name="ChatGPT",
    base_url="https://chatgpt.com",
    icon="🤖",
    input_selector="textarea#prompt-textarea || div#prompt-textarea[contenteditable=\"true\"] || textarea[id=\"prompt-textarea\"] || div[contenteditable=\"true\"][data-testid=\"prompt-textarea\"]",
    send_selector="button[data-testid=\"send-button\"] || button[aria-label=\"Send prompt\"] || button[type=\"submit\"]",
    user_message_selector="div[data-message-author-role=\"user\"] || article [data-message-author-role=\"user\"]",
    ai_message_selector="div[data-message-author-role=\"assistant\"] || article [data-message-author-role=\"assistant\"]",
    transcript_selector="div[class*=\"transcript\"] || div[aria-live][class*=\"voice\"]",
    live_mode_indicator_selector="button[aria-label*=\"voice\"] || button[class*=\"voice\"] || button[aria-label*=\"mic\"]",
    supports_voice=True,
)

CLAUDE = AiWebPlatform(
    id="claude",
    name="Claude",
    base_url="https://claude.ai",
    icon="🧠",
    input_selector="div[contenteditable=\"true\"][class*=\"ProseMirror\"] || fieldset div[contenteditable=\"true\"] || div[contenteditable=\"true\"][role=\"textbox\"]",
    send_selector="button[aria-label=\"Send Message\"] || button[class*=\"send\"] || button[type=\"submit\"]",
    user_message_selector="div[data-testid=\"user-message\"] || div[class*=\"human-message\"] || div[role=\"article\"][data-author=\"human\"]",
    ai_message_selector="div[data-testid=\"assistant-message\"] || div[class*=\"assistant-message\"] || div[role=\"article\"][data-author=\"assistant\"]",
    supports_voice=False,
)

GEMINI = AiWebPlatform(
    id="gemini",
    name="Gemini",
    base_url="https://gemini.google.com/app",
    icon="✨",
    input_selector="div[contenteditable=\"true\"][aria-label*=\"prompt\"] || rich-textarea div[contenteditable=\"true\"] || div[role=\"textbox\"][contenteditable=\"true\"]",
    send_selector="button[aria-label*=\"Send\"] || button[mattooltip=\"Send message\"] || button[type=\"submit\"]",
    user_message_selector="message-content[class*=\"user\"] || div[class*=\"user-message\"] || div[aria-label*=\"You\"]",
    ai_message_selector="message-content[class*=\"model\"] || div[class*=\"model-response\"] || div[aria-label*=\"Gemini\"]",
    supports_voice=True,
)

PERPLEXITY = AiWebPlatform(
    id="perplexity",
    name="Perplexity",
    base_url="https://www.perplexity.ai",
    icon="🔍",
    input_selector="textarea[placeholder*=\"Ask\"] || textarea[class*=\"search\"] || textarea",
    send_selector="button[type=\"submit\"] || button[aria-label*=\"Submit\"] || button[aria-label*=\"Search\"]",
    user_message_selector="div[class*=\"user-query\"] || div[class*=\"question\"]",
    ai_message_selector="div[class*=\"prose\"] || div[class*=\"answer\"] || main div[class*=\"markdown\"]",
    supports_voice=False,
)

COPILOT = AiWebPlatform(
    id="copilot",
    name="Microsoft Copilot",
    base_url="https://copilot.microsoft.com",
    icon="🪟",
    input_selector="textarea[id*=\"searchbox\"] || cib-serp[mode=\"conversation\"] textarea || textarea",
    send_selector="button[aria-label*=\"Submit\"] || button[class*=\"submit\"] || button[type=\"submit\"]",
    user_message_selector="cib-message[type=\"user\"] || div[class*=\"user-message\"]",
    ai_message_selector="cib-message[type=\"bot\"] || div[class*=\"bot-message\"]",
    supports_voice=True,
)


# ============================================================================
# PLATFORM REGISTRY CLASS
# ============================================================================

class PlatformRegistry:
    """Manages all registered AI platforms."""
    
    def __init__(self):
        self.platforms: Dict[str, AiWebPlatform] = {}
        self._load_defaults()
        self._load_user_overrides()
    
    def _load_defaults(self):
        """Load default platform definitions."""
        defaults = [CHATGPT, CLAUDE, GEMINI, PERPLEXITY, COPILOT]
        for platform in defaults:
            self.platforms[platform.id] = platform
    
    def _load_user_overrides(self):
        """Load user customizations from storage."""
        overrides_file = os.path.join(STORAGE_DIR, "platform_overrides.json")
        if os.path.exists(overrides_file):
            try:
                with open(overrides_file, 'r') as f:
                    overrides = json.load(f)
                for pid, data in overrides.items():
                    if pid in self.platforms:
                        # Update existing platform
                        for key, value in data.items():
                            if hasattr(self.platforms[pid], key):
                                setattr(self.platforms[pid], key, value)
                    else:
                        # New custom platform
                        self.platforms[pid] = AiWebPlatform.from_dict(data)
            except Exception as e:
                print(f"[PlatformRegistry] Error loading overrides: {e}")
    
    def save_overrides(self):
        """Save user customizations."""
        overrides_file = os.path.join(STORAGE_DIR, "platform_overrides.json")
        data = {pid: p.to_dict() for pid, p in self.platforms.items()}
        with open(overrides_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_platform(self, platform_id: str) -> Optional[AiWebPlatform]:
        """Get platform by ID."""
        return self.platforms.get(platform_id)
    
    def get_enabled_platforms(self) -> List[AiWebPlatform]:
        """Get all enabled platforms."""
        return [p for p in self.platforms.values() if p.enabled]
    
    def get_all_platforms(self) -> List[AiWebPlatform]:
        """Get all platforms."""
        return list(self.platforms.values())
    
    def toggle_platform(self, platform_id: str, enabled: bool):
        """Enable or disable a platform."""
        if platform_id in self.platforms:
            self.platforms[platform_id].enabled = enabled
            self.save_overrides()
    
    def add_custom_platform(self, platform: AiWebPlatform):
        """Add a custom platform."""
        self.platforms[platform.id] = platform
        self.save_overrides()
    
    def update_selectors(self, platform_id: str, selectors: dict):
        """Update DOM selectors for a platform."""
        if platform_id in self.platforms:
            for key, value in selectors.items():
                if hasattr(self.platforms[platform_id], key):
                    setattr(self.platforms[platform_id], key, value)
            self.save_overrides()


# Global registry instance
REGISTRY = PlatformRegistry()
