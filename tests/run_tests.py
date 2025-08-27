#!/usr/bin/env python3
"""
Test Runner for Nova Regression Tests

This script provides a command-line interface for running Nova's test suite:
1. Discovers and runs all tests in the tests directory
2. Supports running specific test patterns
3. Configurable verbosity for detailed test output
4. Returns appropriate exit codes for CI/CD integration

Usage:
  # Run all tests
  $ python tests/run_tests.py
  
  # Run specific test
  $ python tests/run_tests.py test_audio_pipeline.AudioPipelineTests.test_stt_initialization
  
  # Run with verbose output
  $ python tests/run_tests.py --verbose

The runner automatically adds the project root to the Python path,
ensuring that all Nova modules can be imported correctly during testing.
"""
import os
import sys
import unittest
import argparse

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests(test_pattern=None, verbose=False):
    """Run all tests matching the pattern"""
    # Discover and run tests
    loader = unittest.TestLoader()
    
    if test_pattern:
        suite = loader.loadTestsFromName(test_pattern)
    else:
        # Run all tests in the tests directory
        suite = loader.discover(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Nova regression tests")
    parser.add_argument("test_pattern", nargs="?", help="Specific test pattern to run (e.g., 'test_audio_pipeline.AudioPipelineTests.test_stt_initialization')")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Run tests and exit with appropriate code
    sys.exit(run_tests(args.test_pattern, args.verbose))
