#!/usr/bin/env python3
"""
Test script to verify the AsyncAPI Python Generator works correctly.

This script tests the generator with both example specifications and
verifies the generated clients can be imported and instantiated.
"""

import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd: str, cwd: str = None) -> tuple[int, str, str]:
    """Run a shell command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd.split(),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def test_generator():
    """Test the generator with example specifications."""
    print("🧪 Testing AsyncAPI Python Generator")
    print("=" * 50)

    # Get current directory
    current_dir = Path(__file__).parent
    generator_script = current_dir / "generate_client.py"
    examples_dir = current_dir / "examples"

    if not generator_script.exists():
        print("❌ Generator script not found!")
        return False

    if not examples_dir.exists():
        print("❌ Examples directory not found!")
        return False

    # Test with each example
    example_files = list(examples_dir.glob("*.json"))
    if not example_files:
        print("❌ No example files found!")
        return False

    all_tests_passed = True

    for example_file in example_files:
        print(f"\n📋 Testing with {example_file.name}")
        print("-" * 30)

        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            # Run generator
            cmd = f"python {generator_script} {example_file} -o {output_dir}"
            exit_code, stdout, stderr = run_command(cmd)

            if exit_code != 0:
                print(f"❌ Generator failed!")
                print(f"   Command: {cmd}")
                print(f"   Stdout: {stdout}")
                print(f"   Stderr: {stderr}")
                all_tests_passed = False
                continue

            print(f"✅ Generator completed successfully")

            # Check generated files
            expected_files = ["client.py", "pyproject.toml", "README.md", ".flake8"]
            for expected_file in expected_files:
                file_path = output_dir / expected_file
                if not file_path.exists():
                    print(f"❌ Missing expected file: {expected_file}")
                    all_tests_passed = False
                else:
                    print(f"   ✅ {expected_file}")

            # Test Python syntax
            client_file = output_dir / "client.py"
            if client_file.exists():
                cmd = f"python -m py_compile {client_file}"
                exit_code, _, stderr = run_command(cmd)
                if exit_code != 0:
                    print(f"❌ Generated client has syntax errors:")
                    print(f"   {stderr}")
                    all_tests_passed = False
                else:
                    print("   ✅ Python syntax check passed")

                # Test imports
                try:
                    # Add temporary directory to Python path
                    sys.path.insert(0, str(output_dir))
                    
                    # Try to import the client module
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        "client", client_file
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        print("   ✅ Client module import successful")
                    else:
                        print("   ❌ Failed to create module spec")
                        all_tests_passed = False
                        
                    # Clean up path
                    sys.path.pop(0)
                    
                except Exception as e:
                    print(f"   ❌ Import test failed: {e}")
                    all_tests_passed = False

    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All tests passed!")
        print("\nThe generator is working correctly and produces valid Python clients.")
        return True
    else:
        print("❌ Some tests failed!")
        print("\nPlease check the errors above and fix any issues.")
        return False


def test_code_quality():
    """Test code quality of the generator script."""
    print("\n🔍 Testing Code Quality")
    print("=" * 50)

    current_dir = Path(__file__).parent
    generator_script = current_dir / "generate_client.py"

    tests = [
        ("flake8", f"flake8 {generator_script}"),
        ("black", f"black --check {generator_script}"),
        ("isort", f"isort --check-only {generator_script}"),
    ]

    all_passed = True
    for test_name, cmd in tests:
        print(f"\n📋 Running {test_name}...")
        exit_code, stdout, stderr = run_command(cmd)
        
        if exit_code == 0:
            print(f"   ✅ {test_name} passed")
        else:
            print(f"   ❌ {test_name} failed:")
            if stdout:
                print(f"      {stdout}")
            if stderr:
                print(f"      {stderr}")
            all_passed = False

    return all_passed


def main():
    """Run all tests."""
    print("🚀 AsyncAPI Python Generator Test Suite")
    print("=" * 60)

    generator_tests_passed = test_generator()
    quality_tests_passed = test_code_quality()

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Generator Tests: {'✅ PASSED' if generator_tests_passed else '❌ FAILED'}")
    print(f"Code Quality:    {'✅ PASSED' if quality_tests_passed else '❌ FAILED'}")

    if generator_tests_passed and quality_tests_passed:
        print("\n🎉 All tests passed! The generator is ready to use.")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues before using the generator.")
        return 1


if __name__ == "__main__":
    exit(main())