#!/usr/bin/env python3
"""
Environment Setup Script

This script helps you set up your environment variables for AutoMailHelpdesk.
It copies the env.example file to .env and guides you through the setup process.
"""

import os
import shutil
import sys

def copy_env_example():
    """Copy env.example to .env if .env doesn't exist."""
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled.")
            return False
    
    try:
        shutil.copy('env.example', '.env')
        print("✅ Created .env file from env.example")
        return True
    except FileNotFoundError:
        print("❌ env.example file not found!")
        return False
    except Exception as e:
        print(f"❌ Error copying file: {e}")
        return False

def show_setup_instructions():
    """Show setup instructions to the user."""
    print("\n" + "="*60)
    print("🚀 AutoMailHelpdesk Environment Setup")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. ✅ .env file created with your Gmail API credentials")
    print("2. 🔐 Run Gmail authentication to get tokens:")
    print("   python scripts/gmail_auth.py")
    print("3. 📝 Update .env file with the tokens from tokens.json")
    print("4. 🔧 Configure other required services (Odoo, Google AI, etc.)")
    print("5. 🚀 Start your application!")
    
    print("\n📁 Files created/modified:")
    print("   ✅ .env (environment variables)")
    print("   📄 env.example (template with your credentials)")
    print("   🔧 scripts/gmail_auth.py (authentication script)")
    
    print("\n🔑 Required Environment Variables:")
    print("   GMAIL_CLIENT_ID ✅ (already set)")
    print("   GMAIL_CLIENT_SECRET ✅ (already set)")
    print("   GMAIL_REFRESH_TOKEN ⏳ (run gmail_auth.py)")
    print("   GMAIL_ACCESS_TOKEN ⏳ (run gmail_auth.py)")
    print("   GOOGLE_API_KEY ⏳ (set your Google AI API key)")
    print("   DATABASE_URL ⏳ (set your MySQL connection)")
    print("   REDIS_URL ⏳ (set your Redis connection)")
    print("   ODOO_* ⏳ (set your Odoo credentials)")

def check_required_files():
    """Check if required files exist."""
    required_files = [
        'env.example',
        'scripts/gmail_auth.py',
        'src/settings.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found")
    return True

def main():
    """Main setup function."""
    print("🔧 AutoMailHelpdesk Environment Setup")
    print("="*50)
    
    # Check required files
    if not check_required_files():
        print("❌ Setup failed: Missing required files")
        sys.exit(1)
    
    # Copy env.example to .env
    if not copy_env_example():
        print("❌ Setup failed: Could not create .env file")
        sys.exit(1)
    
    # Show instructions
    show_setup_instructions()
    
    print("\n🎉 Environment setup completed!")
    print("💡 Run 'python scripts/gmail_auth.py' to get your Gmail tokens")

if __name__ == '__main__':
    main() 