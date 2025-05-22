#!/usr/bin/env python3
"""
Run only conversation-related tests
"""
import sys
import os
import subprocess

def main():
    """Run conversation tests only"""
    # Add project root to Python path
    script_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, script_dir)
    
    # Conversation test files
    conversation_tests = [
        "tests/test_conversation_models.py",
        "tests/test_conversation_service.py", 
        "tests/test_conversation_router.py",
        "tests/test_conversation_ai_skills.py",
        "tests/test_conversation_integration.py"
    ]
    
    print("Running C1 Conversational Memory Tests")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ pytest not found. Please install with: pip install pytest pytest-asyncio")
        return 1
    
    # Run each test file
    all_passed = True
    
    for test_file in conversation_tests:
        if not os.path.exists(test_file):
            print(f"⚠️  Test file not found: {test_file}")
            continue
            
        print(f"\n🧪 Running {test_file}...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, "-v", "--tb=short"
            ], capture_output=False, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
            else:
                print(f"❌ {test_file} - FAILED")
                all_passed = False
                
        except subprocess.TimeoutExpired:
            print(f"⏱️  {test_file} - TIMEOUT")
            all_passed = False
        except Exception as e:
            print(f"⚠️  {test_file} - ERROR: {e}")
            all_passed = False
    
    # Run all conversation tests together
    print(f"\n🧪 Running all conversation tests together...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
        ] + conversation_tests + ["-v", "--tb=short"], 
        capture_output=False, timeout=300)
        
        if result.returncode == 0:
            print("✅ All conversation tests - PASSED")
        else:
            print("❌ Some conversation tests - FAILED")
            all_passed = False
            
    except Exception as e:
        print(f"⚠️  Error running combined tests: {e}")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All C1 Conversational Memory tests PASSED!")
        print("\nFeatures tested:")
        print("  ✅ Conversation Models (Pydantic validation)")
        print("  ✅ Conversation Service (CRUD operations)")
        print("  ✅ Conversation Router (API endpoints)")
        print("  ✅ Conversation AI Skills (Response generation)")
        print("  ✅ Conversation Integration (End-to-end flows)")
        print(f"\nTotal test methods: 130+")
        return 0
    else:
        print("❌ Some conversation tests failed. Check output above.")
        print("\nIf tests are failing due to missing dependencies, install with:")
        print("  pip install -r requirements.txt")
        print("  pip install pytest pytest-asyncio pytest-mock")
        return 1

if __name__ == "__main__":
    sys.exit(main())