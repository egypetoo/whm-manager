#!/usr/bin/env python3
# === WHM Manager Script Runner ===

import sys
import os

def show_menu():
    """Display the main menu"""
    print("🚀 WHM Manager Scripts")
    print("=" * 50)
    print("Select the script you want to run:")
    print()
    print("1. 📋 ACCOUNTS & DOMAINS MANAGEMENT")
    print("2. 📧 EMAIL MANAGEMENT & MONITORING")
    print("3. 🖥️ SERVER MONITORING & SITE CHECK")
    print("4. 🔧 SERVER STATUS CHECK")
    print("5. 📊 VIEW LOGS")
    print("0. 🚪 EXIT")
    print("=" * 50)

def run_script(script_name):
    """Run the selected script"""
    try:
        if script_name == "accounts":
            print("\n🚀 Running Accounts & Domains Management Script...")
            os.system("python3 accounts_domains_script.py")
        elif script_name == "email":
            print("\n🚀 Running Email Management & Monitoring Script...")
            os.system("python3 email_management_script.py")
        elif script_name == "monitoring":
            print("\n🚀 Running Server Monitoring & Site Check Script...")
            os.system("python3 server_monitoring_script.py")
        elif script_name == "status":
            print("\n🚀 Checking Server Status...")
            os.system("python3 -c \"from common_functions import *; servers = load_servers_config(); display_server_status(servers)\"")
        elif script_name == "logs":
            print("\n🚀 Viewing Logs...")
            os.system("python3 -c \"from common_functions import *; show_logs()\"")
        else:
            print("❌ Invalid Option!")
    except Exception as e:
        print(f"❌ Error running script: {str(e)}")

def main():
    """The main function"""
    while True:
        show_menu()
        choice = input("\nSelect Script Number: ").strip()
        
        if choice == "1":
            run_script("accounts")
        elif choice == "2":
            run_script("email")
        elif choice == "3":
            run_script("monitoring")
        elif choice == "4":
            run_script("status")
        elif choice == "5":
            run_script("logs")
        elif choice == "0":
            print("👋 Bye!")
            break
        else:
            print("❌ Invalid Option! Please select a number from 0 to 5")
        
        input("\nPress Enter to return to the main menu...")

if __name__ == "__main__":
    main()
