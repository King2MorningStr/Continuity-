"""Tests for Script Builder."""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from udac_portal.platform_registry import CHATGPT, CLAUDE
from udac_portal.script_builder import PortalScriptBuilder


class TestPortalScriptBuilder(unittest.TestCase):
    """Test PortalScriptBuilder."""
    
    def test_build_observation_script(self):
        """Test building observation script."""
        script = PortalScriptBuilder.build(CHATGPT)
        
        # Check script contains key elements
        self.assertIn("UDACBridge", script)
        self.assertIn("MutationObserver", script)
        self.assertIn("observeUserMessages", script)
        self.assertIn("observeAiMessages", script)
        self.assertIn(CHATGPT.input_selector, script)
    
    def test_build_script_for_different_platforms(self):
        """Test scripts are customized per platform."""
        chatgpt_script = PortalScriptBuilder.build(CHATGPT)
        claude_script = PortalScriptBuilder.build(CLAUDE)
        
        # Scripts should contain platform-specific selectors
        self.assertIn(CHATGPT.user_message_selector, chatgpt_script)
        self.assertIn(CLAUDE.user_message_selector, claude_script)
        
        # Scripts should be different
        self.assertNotEqual(chatgpt_script, claude_script)
    
    def test_build_send_prompt_script(self):
        """Test building send prompt script."""
        test_text = "Hello, this is a test prompt"
        script = PortalScriptBuilder.build_send_prompt_script(CHATGPT, test_text)
        
        # Check script contains key elements
        self.assertIn(test_text, script)
        self.assertIn(CHATGPT.input_selector, script)
        self.assertIn("dispatchEvent", script)
    
    def test_build_send_prompt_escapes_special_chars(self):
        """Test that special characters are escaped."""
        test_text = "Test with `backticks` and $dollar and \\backslash"
        script = PortalScriptBuilder.build_send_prompt_script(CHATGPT, test_text)
        
        # Should not break JavaScript
        self.assertIn("\\`", script)  # Backticks escaped
        self.assertIn("\\$", script)  # Dollar escaped
        self.assertIn("\\\\", script)  # Backslash escaped
    
    def test_build_get_input_content_script(self):
        """Test building get input content script."""
        script = PortalScriptBuilder.build_get_input_content_script(CHATGPT)
        
        self.assertIn(CHATGPT.input_selector, script)
        self.assertIn("return", script)
    
    def test_build_clear_input_script(self):
        """Test building clear input script."""
        script = PortalScriptBuilder.build_clear_input_script(CHATGPT)
        
        self.assertIn(CHATGPT.input_selector, script)
        self.assertIn("innerHTML", script)
    
    def test_build_check_page_ready_script(self):
        """Test building page ready check script."""
        script = PortalScriptBuilder.build_check_page_ready_script()
        
        self.assertIn("ready", script)
        self.assertIn("loading", script)


if __name__ == '__main__':
    unittest.main()
