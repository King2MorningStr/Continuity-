"""Tests for Platform Registry."""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from udac_portal.platform_registry import (
    PlatformRegistry, AiWebPlatform, CHATGPT, CLAUDE, GEMINI
)


class TestAiWebPlatform(unittest.TestCase):
    """Test AiWebPlatform dataclass."""
    
    def test_platform_creation(self):
        """Test creating a platform."""
        platform = AiWebPlatform(
            id="test",
            name="Test Platform",
            base_url="https://test.ai",
            icon="🧪",
            input_selector="textarea",
        )
        self.assertEqual(platform.id, "test")
        self.assertEqual(platform.name, "Test Platform")
        self.assertTrue(platform.enabled)
    
    def test_platform_to_dict(self):
        """Test platform serialization."""
        platform = CHATGPT
        data = platform.to_dict()
        self.assertEqual(data["id"], "chatgpt")
        self.assertEqual(data["name"], "ChatGPT")
        self.assertIn("input_selector", data)
    
    def test_platform_from_dict(self):
        """Test platform deserialization."""
        data = {
            "id": "custom",
            "name": "Custom AI",
            "base_url": "https://custom.ai",
            "icon": "🤖",
            "input_selector": "input.prompt",
        }
        platform = AiWebPlatform.from_dict(data)
        self.assertEqual(platform.id, "custom")
        self.assertEqual(platform.name, "Custom AI")


class TestPlatformRegistry(unittest.TestCase):
    """Test PlatformRegistry."""
    
    def setUp(self):
        """Set up test registry."""
        self.registry = PlatformRegistry()
    
    def test_default_platforms_loaded(self):
        """Test that default platforms are loaded."""
        platforms = self.registry.get_all_platforms()
        self.assertGreater(len(platforms), 0)
        
        # Check specific platforms exist
        chatgpt = self.registry.get_platform("chatgpt")
        self.assertIsNotNone(chatgpt)
        self.assertEqual(chatgpt.name, "ChatGPT")
        
        claude = self.registry.get_platform("claude")
        self.assertIsNotNone(claude)
        self.assertEqual(claude.name, "Claude")
    
    def test_get_enabled_platforms(self):
        """Test getting enabled platforms."""
        enabled = self.registry.get_enabled_platforms()
        self.assertGreater(len(enabled), 0)
        
        for platform in enabled:
            self.assertTrue(platform.enabled)
    
    def test_toggle_platform(self):
        """Test toggling platform enabled state."""
        self.registry.toggle_platform("chatgpt", False)
        chatgpt = self.registry.get_platform("chatgpt")
        self.assertFalse(chatgpt.enabled)
        
        # Re-enable
        self.registry.toggle_platform("chatgpt", True)
        chatgpt = self.registry.get_platform("chatgpt")
        self.assertTrue(chatgpt.enabled)
    
    def test_add_custom_platform(self):
        """Test adding a custom platform."""
        custom = AiWebPlatform(
            id="custom_test",
            name="Custom Test",
            base_url="https://custom-test.ai",
            icon="🧪",
            input_selector="textarea",
        )
        self.registry.add_custom_platform(custom)
        
        retrieved = self.registry.get_platform("custom_test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Custom Test")


if __name__ == '__main__':
    unittest.main()
