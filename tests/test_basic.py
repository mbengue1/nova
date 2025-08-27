"""
Basic tests for Hey Nova MVP
Tests core functionality without requiring audio hardware
"""
import sys
import unittest
from pathlib import Path

# Add core directory to Python path
sys.path.insert(0, str(Path("core").absolute()))

class TestNovaConfig(unittest.TestCase):
    """Test configuration functionality"""
    
    def test_config_import(self):
        """Test that config can be imported"""
        try:
            import config
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import config: {e}")
    
    def test_config_instance(self):
        """Test that config instance exists"""
        import config
        self.assertIsNotNone(config.config)
        self.assertIsInstance(config.config.wake_word, str)

class TestNovaBrain(unittest.TestCase):
    """Test brain/router functionality"""
    
    def test_brain_import(self):
        """Test that brain can be imported"""
        try:
            import brain.router
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import brain: {e}")
    
    def test_brain_creation(self):
        """Test that brain can be created"""
        try:
            from brain.router import NovaBrain
            brain = NovaBrain()
            self.assertIsNotNone(brain)
        except Exception as e:
            self.fail(f"Failed to create brain: {e}")
    
    def test_skill_patterns(self):
        """Test that skill patterns are defined"""
        try:
            from brain.router import NovaBrain
            brain = NovaBrain()
            self.assertIsNotNone(brain.skill_patterns)
            self.assertIn('app_control', brain.skill_patterns)
            self.assertIn('system_info', brain.skill_patterns)
        except Exception as e:
            self.fail(f"Failed to test skill patterns: {e}")

class TestTextProcessing(unittest.TestCase):
    """Test text processing without audio"""
    
    def test_app_control_parsing(self):
        """Test app control command parsing"""
        try:
            from brain.router import NovaBrain
            brain = NovaBrain()
            
            # Test app opening commands
            response = brain.process_input("open VS Code")
            self.assertIsNotNone(response)
            self.assertIn("VS Code", response)
            
        except Exception as e:
            self.fail(f"Failed to test app control: {e}")
    
    def test_system_info_parsing(self):
        """Test system info command parsing"""
        try:
            from brain.router import NovaBrain
            brain = NovaBrain()
            
            # Test time/date commands
            response = brain.process_input("what time is it")
            self.assertIsNotNone(response)
            self.assertIn("time", response.lower())
            
        except Exception as e:
            self.fail(f"Failed to test system info: {e}")
    
    def test_math_parsing(self):
        """Test math command parsing"""
        try:
            from brain.router import NovaBrain
            brain = NovaBrain()
            
            # Test math commands
            response = brain.process_input("what is 5 plus 3")
            self.assertIsNotNone(response)
            self.assertIn("8", response)
            
        except Exception as e:
            self.fail(f"Failed to test math: {e}")

def run_tests():
    """Run all tests"""
    print("🧪 Running Hey Nova tests...")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNovaConfig)
    suite.addTests(loader.loadTestsFromTestCase(TestNovaBrain))
    suite.addTests(loader.loadTestsFromTestCase(TestTextProcessing))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 Test Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
