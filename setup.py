"""
Setup script for Multi-Agent Web Development System
"""

import os
import subprocess
import sys


def main():
    """Run setup steps"""
    print("=" * 80)
    print("🚀 Multi-Agent System Setup")
    print("=" * 80)
    
    # Step 1: Check Python version
    print("\n1️⃣ Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Step 2: Install dependencies
    print("\n2️⃣ Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Step 3: Check environment variables
    print("\n3️⃣ Checking environment variables...")
    api_key = os.getenv('NVIDIA_API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        print("⚠️  NVIDIA_API_KEY not set or using placeholder")
        print("   Please set your API key in .env file:")
        print("   NVIDIA_API_KEY=your-actual-key")
    else:
        print("✅ NVIDIA_API_KEY is set")
    
    # Step 4: Create directories
    print("\n4️⃣ Creating directories...")
    os.makedirs("generated_projects", exist_ok=True)
    print("✅ Directories created")
    
    # Step 5: Test imports
    print("\n5️⃣ Testing imports...")
    try:
        from agents import BaseAgent
        from orchestration import WorkflowOrchestrator
        from antigravity.llm.kimi_adapter import KimiAdapter
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    
    # Step 6: Run quick test
    print("\n6️⃣ Running quick test...")
    try:
        from orchestration.state_manager import StateManager
        sm = StateManager(db_path="test_setup.db")
        workflow = sm.create_workflow("test-setup", "Test prompt")
        sm.delete_workflow("test-setup")
        os.remove("test_setup.db")
        print("✅ Quick test passed")
    except Exception as e:
        print(f"⚠️  Quick test failed: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Setup complete!")
    print("=" * 80)
    print("\n📚 Next steps:")
    print("   1. Set your NVIDIA_API_KEY in .env file")
    print("   2. Run: python demo.py")
    print("   3. Or: python api/cli.py create \"Your app idea\" --watch")
    print("   4. Or: python api/api_server.py")
    print("\n📖 Documentation:")
    print("   - README_MULTIAGENT.md - Complete system overview")
    print("   - QUICKSTART.md - Quick start guide")
    print("\n")


if __name__ == '__main__':
    main()
