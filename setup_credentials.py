#!/usr/bin/env python3
"""
Setup script to create credentials.json file
Run this script to set up your credentials securely
"""

import json
import os

def create_credentials_file():
    """Create credentials.json file with user input"""
    
    print("🔐 AI Agents - Credentials Setup")
    print("=" * 40)
    print("This script will create a secure credentials.json file")
    print("Your passwords will NOT be stored in the executable!")
    print()
    
    # Get credentials from user
    credentials = {}
    
    print("Enter your passwords (press Enter to skip):")
    print()
    
    credentials['RKRK_PASS'] = input("Rakuraku Password: ").strip()
    credentials['GOQ_PASS'] = input("GoQ Password: ").strip()
    credentials['O_PASS'] = input("Orange Password: ").strip()
    credentials['O_MAIL_PASS'] = input("Email Password: ").strip()
    credentials['GEMINI_API'] = input("Gemini API Key: ").strip()
    
    # Save to file
    try:
        with open('credentials.json', 'w', encoding='utf-8') as f:
            json.dump(credentials, f, indent=4, ensure_ascii=False)
        
        print()
        print("✅ credentials.json created successfully!")
        print("🔒 Your passwords are now stored securely outside the executable")
        print()
        print("📝 Next steps:")
        print("   1. Run the main application")
        print("   2. Keep credentials.json secure and private")
        print("   3. Don't share credentials.json with others")
        
    except Exception as e:
        print(f"❌ Error creating credentials.json: {e}")

def create_from_template():
    """Create credentials.json from template with current values"""
    
    # Current passwords (replace with actual values)
    credentials = {
        "RKRK_PASS": "first-123",
        "GOQ_PASS": "HCnet2483", 
        "O_PASS": "first160DWS5",
        "O_MAIL_PASS": "saFQnDvy0CtN",
        "GEMINI_API": "AIzaSyC7qH4wZ1lyQgftw1CJ7yPHTfPvJ-0SJHg"
    }
    
    try:
        with open('credentials.json', 'w', encoding='utf-8') as f:
            json.dump(credentials, f, indent=4, ensure_ascii=False)
        
        print("✅ credentials.json created with current passwords")
        print("🔒 Passwords are now stored securely outside the executable")
        
    except Exception as e:
        print(f"❌ Error creating credentials.json: {e}")

if __name__ == "__main__":
    print("Choose setup method:")
    print("1. Interactive setup (enter passwords manually)")
    print("2. Use current passwords from config")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        create_credentials_file()
    elif choice == "2":
        create_from_template()
    else:
        print("Invalid choice. Exiting.")