"""Tests for Continuity Engine."""

import unittest
import sys
import os
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock storage dir before importing
import udac_portal.continuity_engine as ce
TEST_DIR = tempfile.mkdtemp()
ce.STORAGE_DIR = TEST_DIR

from udac_portal.continuity_engine import ContinuityEngine, ContinuitySettings
from udac_portal.entitlement_engine import ENTITLEMENTS

class TestContinuitySettings(unittest.TestCase):
    """Test ContinuitySettings dataclass."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = ContinuitySettings()
        self.assertEqual(settings.injection_strength, 5)
        self.assertTrue(settings.continuity_enabled)
        self.assertFalse(settings.platform_isolation_mode)
        self.assertTrue(settings.cross_platform_insights)


class TestContinuityEngine(unittest.TestCase):
    """Test ContinuityEngine."""
    
    def setUp(self):
        """Set up test engine."""
        self.engine = ContinuityEngine()
        # Mock Premium for tests to avoid entitlements issues
        ENTITLEMENTS.set_tier("PREMIUM")
    
    def tearDown(self):
        """Clean up."""
        self.engine.clear_all_data()
        ENTITLEMENTS.set_tier("FREE") # Reset
    
    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        self.assertIsNotNone(self.engine.settings)
        self.assertEqual(len(self.engine.global_threads), 0)
    
    def test_enrich_input_disabled(self):
        """Test enrichment when disabled."""
        self.engine.update_settings(continuity_enabled=False)
        
        payload = self.engine.enrich_input("chatgpt", "Hello, how are you?")
        
        self.assertEqual(payload.final_prompt_text, "Hello, how are you?")
        self.assertEqual(payload.tokens_added, 0)
        self.assertEqual(payload.continuity_summary, "")
    
    def test_enrich_input_enabled(self):
        """Test enrichment when enabled."""
        self.engine.update_settings(continuity_enabled=True, injection_strength=5)
        
        # First message - no context yet
        payload1 = self.engine.enrich_input("chatgpt", "Hello, how are you?")
        self.assertIn("Hello, how are you?", payload1.final_prompt_text)
        
        # Record a response
        self.engine.record_output("chatgpt", "I'm doing well, thank you for asking!")
        
        # Second message - might have context
        payload2 = self.engine.enrich_input("chatgpt", "What's the weather like?")
        self.assertIn("What's the weather like?", payload2.final_prompt_text)
    
    def test_record_output(self):
        """Test recording AI output."""
        self.engine.enrich_input("chatgpt", "Test question")
        self.engine.record_output("chatgpt", "Test response about Python programming")
        
        # Check that topics are extracted
        self.assertIn("python", self.engine.user_profile["topics_of_interest"])
    
    def test_get_or_create_thread(self):
        """Test thread creation."""
        thread = self.engine.get_or_create_thread("chatgpt")
        
        self.assertEqual(thread.platform_id, "chatgpt")
        self.assertEqual(len(thread.turns), 0)
    
    def test_platform_isolation_mode(self):
        """Test platform isolation mode."""
        self.engine.update_settings(platform_isolation_mode=True)
        
        # Create threads on different platforms
        thread1 = self.engine.get_or_create_thread("chatgpt")
        thread2 = self.engine.get_or_create_thread("claude")
        
        # They should be in separate containers
        self.assertIn("chatgpt", self.engine.platform_threads)
        self.assertIn("claude", self.engine.platform_threads)
    
    def test_update_settings(self):
        """Test updating settings."""
        self.engine.update_settings(
            injection_strength=8,
            continuity_enabled=False
        )
        
        self.assertEqual(self.engine.settings.injection_strength, 8)
        self.assertFalse(self.engine.settings.continuity_enabled)
    
    def test_get_stats(self):
        """Test getting stats."""
        self.engine.enrich_input("chatgpt", "Test")
        self.engine.record_output("chatgpt", "Response")
        
        stats = self.engine.get_stats()
        
        self.assertIn("enabled", stats)
        self.assertIn("injection_strength", stats)
        self.assertIn("total_threads", stats)
    
    def test_clear_all_data(self):
        """Test clearing all data."""
        # Add some data
        self.engine.enrich_input("chatgpt", "Test")
        self.engine.record_output("chatgpt", "Response")
        
        # Clear
        self.engine.clear_all_data()
        
        # Verify cleared
        self.assertEqual(len(self.engine.global_threads), 0)
        self.assertEqual(len(self.engine.cross_platform_memory), 0)


class TestCrossplatformMemory(unittest.TestCase):
    """Test cross-platform memory features."""
    
    def setUp(self):
        """Set up test engine."""
        ENTITLEMENTS.set_tier("PREMIUM")
        self.engine = ContinuityEngine()
        self.engine.update_settings(cross_platform_insights=True)
    
    def tearDown(self):
        """Clean up."""
        self.engine.clear_all_data()
        ENTITLEMENTS.set_tier("FREE")
    
    def test_cross_platform_memory_building(self):
        """Test that cross-platform memory is built."""
        # Interact on ChatGPT
        self.engine.enrich_input("chatgpt", "Tell me about Python")
        self.engine.record_output("chatgpt", "Python is a programming language")
        
        # Interact on Claude
        self.engine.enrich_input("claude", "Tell me about JavaScript")
        self.engine.record_output("claude", "JavaScript is for web development")
        
        # Check cross-platform memory
        self.assertGreater(len(self.engine.cross_platform_memory), 0)


# Cleanup temp dir after all tests
def tearDownModule():
    shutil.rmtree(TEST_DIR, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
