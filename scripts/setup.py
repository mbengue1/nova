#!/usr/bin/env python3
"""
Setup script for Hey Nova
Helps users configure and test the assistant
"""
import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print the Nova setup banner"""
    print("🌟" + "="*48 + "🌟")
    print("🌟           Welcome to Hey Nova Setup!           🌟")
    print("🌟" + "="*48 + "🌟")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def create_virtual_env():
    """Create and activate virtual environment"""
    print("\n🔧 Setting up virtual environment...")
    
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Determine pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = ".venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_cmd = ".venv/bin/pip"
    
    try:
        # Upgrade pip first
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment variables"""
    print("\n🔐 Setting up environment variables...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("⚠️  env.example not found, creating basic .env")
        with open(env_file, "w") as f:
            f.write("# Hey Nova Environment Variables\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            f.write("NOTION_API_KEY=your_notion_integration_token_here\n")
            f.write("NOTION_DATABASE_ID=your_notion_database_id_here\n")
    else:
        # Copy env.example to .env
        import shutil
        shutil.copy(env_example, env_file)
        print("✅ Created .env from env.example")
    
    print("\n📝 Please edit .env file with your actual API keys:")
    print("   - OPENAI_API_KEY: Get from https://platform.openai.com/api-keys")
    print("   - NOTION_API_KEY: Optional for MVP")
    print("   - NOTION_DATABASE_ID: Optional for MVP")
    
    return True

def test_installation():
    """Test if Nova can be imported"""
    print("\n🧪 Testing installation...")
    
    try:
        # Add core directory to Python path
        sys.path.insert(0, str(Path("core").absolute()))
        
        # Try to import core modules
        import config
        import wakeword.detector
        import stt.transcriber
        import tts.speaker
        import brain.router
        
        print("✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎯 Next Steps:")
    print("1. Edit .env file with your OpenAI API key")
    print("2. Activate virtual environment:")
    if os.name == 'nt':  # Windows
        print("   .venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source .venv/bin/activate")
    print("3. Run Nova: python core/main.py")
    print("4. Say 'Hey Nova' or press Enter for push-to-talk")
    print()
    print("📚 For help, check the README.md file")
    print("🐛 Report issues on GitHub")

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_env():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("⚠️  Installation test failed, but you can try running Nova anyway")
    
    print_next_steps()
    print("\n🎉 Setup complete! Welcome to Hey Nova!")

if __name__ == "__main__":
    main()
