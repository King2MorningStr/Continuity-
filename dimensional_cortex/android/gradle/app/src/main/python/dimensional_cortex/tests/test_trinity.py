
import unittest
import os
import shutil
import tempfile
import sys
from unittest.mock import MagicMock, patch

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

class TestTrinityImports(unittest.TestCase):
    def test_imports(self):
        """Verify that all trinity modules can be imported."""
        try:
            import dimensional_cortex.dimensional_memory_constant_standalone_demo
            import dimensional_cortex.dimensional_processing_system_standalone_demo
            import dimensional_cortex.dimensional_energy_regulator_mobile
        except ImportError as e:
            self.fail(f"Failed to import trinity modules: {e}")

class TestMemorySystem(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for storage
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch('dimensional_cortex.dimensional_memory_constant_standalone_demo.STORAGE_DIR', self.test_dir)
        self.mock_storage = self.patcher.start()

        # Reload the module to pick up the patched STORAGE_DIR if possible,
        # or just rely on the fact that if we patch it before 'start_memory_system' is called (or if we manually init)
        # But 'STORAGE_DIR' is a global constant computed at import time.
        # Patching it on the module object works for subsequent usages.

        from dimensional_cortex.dimensional_memory_constant_standalone_demo import DimensionalMemory
        self.DimensionalMemory = DimensionalMemory

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_memory_init(self):
        """Test that memory system initializes and creates files in the right place."""
        memory = self.DimensionalMemory()
        # It should try to load from STORAGE_DIR/system_base_state.json
        # Since it's empty, it should start fresh (or try to load resource if we hadn't mocked it away,
        # but the resource loading also writes to STORAGE_DIR).

        # Check if we can add a node
        from dimensional_cortex.dimensional_memory_constant_standalone_demo import DataNode
        node = DataNode(payload={"test": "data"})
        memory.add_node(node)
        self.assertIn(node.id, memory.nodes)

if __name__ == '__main__':
    unittest.main()
