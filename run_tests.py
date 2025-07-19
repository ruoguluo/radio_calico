#!/usr/bin/env python3
"""
Test runner for Radio Calico application.

This script runs all tests and provides a summary of results.
"""

import os
import sys
import unittest


def run_tests():
    """Run all tests and return results."""
    # Add current directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Discover and run all tests
    loader = unittest.TestLoader()
    suite = loader.discover(".", pattern="test_*.py")

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")

    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
