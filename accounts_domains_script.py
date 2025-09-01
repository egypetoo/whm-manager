#!/usr/bin/env python3
# === WHM Accounts & Domains Management Script ===

import sys
import os
from datetime import datetime
from fnmatch import fnmatch

# استيراد الدوال المشتركة
from common_functions import *

# === دوال إدارة الحسابات ===
def search_domain_across_servers(domain, servers):
    """البحث عن دومين في جميع السيرفرات"""
    print(f"\n🔍 Searching for domain: {domain}")
    print("=" * 50)
    
    found = False
    for server_name, server in servers.items():
        print(f"🖥️  Checking Server {server_name} ({server['ip']})...")
        
        if test_server_connection(server):
            accounts = list_accounts(server)
            for acct in accounts:
                if acct["domain"].lower() == domain.lower():
                    print(f"✅ Domain found on Server {server_name}!")
                    print(f"📋 Account Details:")
                    print(f"   Domain: {acct['domain']}")
                    print(f"   User: {acct['user']}")
                    print(f"   Email: {acct.get('email', 'N/A')}")
                    print(f"   Package: {acct.get('plan', 'N/A')}")
                    print(f"   Status: {'🔴 Suspended' if acct.get('suspended', 0) == 1 else '🟢 Active'}")
                    print(f"   Creation Date: {datetime.fromtimestamp(int(acct.get('unix_startdate', 0))).strftime('%Y-%m-%d')}")
                    found = True
                    break
            
            if found:
                break
        else:
            print(f"   🔴 Server offline")
    
    if not found:
        print("❌ Domain not found on any server!")

def list_all_domains(servers):
    """عرض جميع الدومينات على جميع السيرفرات"""
    print("\n📋 All Domains Report")
    print("=" * 80)
    
    all_domains = []
    total_accounts = 0
    online_servers = 0
    
    for server_name, server in servers.items():
        print(f"\n🖥️  Server {server_name} ({server['ip']}):")
        
        if test_server_connection(server):
            online_servers += 1
            accounts = list_accounts(server)
            server_accounts = len(accounts)
            total_accounts += server_accounts
            
            print(f"   Status: 🟢 Online")
            print(f"   Accounts: {server_accounts}")
            
            if accounts:
                print(f"   Domains:")
                for acct in accounts:
                    status = "🔴 Suspended" if acct.get('suspended', 0) == 1 else "🟢 Active"
                    print(f"      {acct['domain']} ({acct['user']}) - {status}")
                    all_domains.append({
                        'domain': acct['domain'],
                        'user': acct['user'],
                        'server': server_name,
                        'status': status,
                        'email': acct.get('email', 'N/A'),
                        'package': acct.get('plan', 'N/A'),
                        'creation_date': datetime.fromtimestamp(int(acct.get('unix_startdate', 0))).strftime('%Y-%m-%d')
                    })
        else:
            print(f"   Status: 🔴 Offline")
    
    print(f"\n📊 Summary:")
    print(f"   Total Servers: {len(servers)}")
    print(f"   Online Servers: {online_servers}")
    print(f"   Total Accounts: {total_accounts}")
    print(f"   Total Domains: {len(all_domains)}")
    
    if all_domains and confirm_action("\nExport domains to file?"):
        export_format = input("Export format (1=Excel, 2=CSV, 3=Both): ").strip()
        
        headers = ["Domain", "cPanel User", "Server", "Status", "Email", "Package", "Creation Date", "Export Date"]
        data_rows = []
        
        for domain in all_domains:
            data_rows.append([
                domain['domain'],
                domain['user'],
                domain['server'],
                domain['status'],
                domain['email'],
                domain['package'],
                domain['creation_date'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        if export_format in ["1", "3"]:
            export_to_excel(data_rows, headers, "all_domains", "All Domains")
        if export_format in ["2", "3"]:
            export_to_csv(data_rows, headers, "all_domains")

def advanced_domain_search(servers, pattern=None, date_range=None, min_disk_usage=None, package=None, status=None):
    """بحث متقدم عن الدومينات"""
    print("\n🔍 Searching domains with specified criteria...")
    found_domains = []
    
    for server_name, server in servers.items():
        if test_server_connection(server):
            print(f"Checking Server {server_name}...")
            accounts = list_accounts(server)
            
            for account in accounts:
                match = True
                
                # فحص نمط الدومين (يدعم substring + wildcard)
                if pattern:
                    domain = account['domain'].lower()
                    pat = pattern.lower()
                    if not (pat in domain or fnmatch(domain, pat)):
                        match = False
                
                # فحص نطاق التاريخ
                if date_range and match:
                    try:
                        start_date, end_date = date_range.split(',')
                        start_date = datetime.strptime(start_date.strip(), '%Y-%m-%d')
                        end_date = datetime.strptime(end_date.strip(), '%Y-%m-%d')
                        account_date = datetime.fromtimestamp(int(account.get('unix_startdate', 0)))
                        if not (start_date <= account_date <= end_date):
                            match = False
                    except:
                        match = False
                
                # فحص استخدام القرص
                if min_disk_usage and match:
                    try:
                        if float(account.get('diskused', 0)) < float(min_disk_usage):
                            match = False
                    except:
                        match = False
                
                # فحص الباقة
                if package and match:
                    if account.get('plan', '').lower() != package.lower():
                        match = False
                
                # فحص الحالة
                if status and match:
                    is_suspended = account.get('suspended', 0) == 1
                    if status.lower() == 'active' and is_suspended:
                        match = False
                    elif status.lower() == 'suspended' and not is_suspended:
                        match = False
                
                # لو كل الشروط متحققة
                if match:
                    found_domains.append({
                        'domain': account['domain'],
                        'server': server_name,
                        'status': '🔴 Suspended' if account.get('suspended', 0) == 1 else '🟢 Active',
                        'user': account['user'],
                        'email': account.get('email', 'N/A'),
                        'package': account.get('plan', 'N/A'),
                        'disk_used': account.get('diskused', 'N/A'),
                        'creation_date': datetime.fromtimestamp(int(account.get('unix_startdate', 0))).strftime('%Y-%m-%d')
                    })
    
    return found_domains

def suspend_account_by_domain(domain, servers):
    """تعليق حساب بالدومين"""
    print(f"\n⏸️  Suspending Account for Domain: {domain}")
    print("=" * 50)
    
    # خيارات البحث
    print("\n🔍 Search Options:")
    print("1. 🚀 Fast search (main domains only)")
    print("2. 🧠 Smart search (main domains first, then subdomains if needed)")
    print("3. 🔍 Full search (all domains + subdomains)")
    
    search_choice = input("Choose search type (1-3, default 2): ").strip()
    
    if search_choice == "1":
        search_mode = "fast"
    elif search_choice == "3":
        search_mode = "full"
    else:
        search_mode = "smart"
    
    server, acct, server_name = find_server_by_domain(domain, servers, search_mode=search_mode)
    
    if not server:
        print("❌ Domain not found on any server!")
        return
    
    cpanel_user = acct["user"]
    print(f"✅ Domain found on Server {server_name}")
    print(f"👤 cPanel User: {cpanel_user}")
    
    if acct.get('suspended', 0) == 1:
        print("⚠️  Account is already suspended!")
        return
    
    reason = input("📝 Suspension reason (optional): ").strip() or "Administrative suspension"
    
    if confirm_action(f"Suspend account {cpanel_user} ({domain})?"):
        params = {
            "user": cpanel_user,
            "reason": reason
        }
        
        result = whm_api_call(server, "suspendacct", params)
        
        if "error" not in result:
            print(f"✅ Account {cpanel_user} suspended successfully!")
            logging.info(f"Account suspended: {cpanel_user} ({domain}) - Reason: {reason}")
        else:
            print(f"❌ Failed to suspend account: {result['error']}")

def unsuspend_account_by_domain(domain, servers):
    """إلغاء تعليق حساب بالدومين"""
    print(f"\n▶️  Unsuspending Account for Domain: {domain}")
    print("=" * 50)
    
    # خيارات البحث
    print("\n🔍 Search Options:")
    print("1. 🚀 Fast search (main domains only)")
    print("2. 🧠 Smart search (main domains first, then subdomains if needed)")
    print("3. 🔍 Full search (all domains + subdomains)")
    
    search_choice = input("Choose search type (1-3, default 2): ").strip()
    
    if search_choice == "1":
        search_mode = "fast"
    elif search_choice == "3":
        search_mode = "full"
    else:
        search_mode = "smart"
    
    server, acct, server_name = find_server_by_domain(domain, servers, search_mode=search_mode)
    
    if not server:
        print("❌ Domain not found on any server!")
        return
    
    cpanel_user = acct["user"]
    print(f"✅ Domain found on Server {server_name}")
    print(f"👤 cPanel User: {cpanel_user}")
    
    if acct.get('suspended', 0) == 0:
        print("⚠️  Account is not suspended!")
        return
    
    if confirm_action(f"Unsuspend account {cpanel_user} ({domain})?"):
        params = {
            "user": cpanel_user
        }
        
        result = whm_api_call(server, "unsuspendacct", params)
        
        if "error" not in result:
            print(f"✅ Account {cpanel_user} unsuspended successfully!")
            logging.info(f"Account unsuspended: {cpanel_user} ({domain})")
        else:
            print(f"❌ Failed to unsuspend account: {result['error']}")

def terminate_account_by_domain(domain, servers):
    """حذف حساب بالدومين"""
    print(f"\n🗑️  Terminating Account for Domain: {domain}")
    print("=" * 50)
    
    # خيارات البحث
    print("\n🔍 Search Options:")
    print("1. 🚀 Fast search (main domains only)")
    print("2. 🧠 Smart search (main domains first, then subdomains if needed)")
    print("3. 🔍 Full search (all domains + subdomains)")
    
    search_choice = input("Choose search type (1-3, default 2): ").strip()
    
    if search_choice == "1":
        search_mode = "fast"
    elif search_choice == "3":
        search_mode = "full"
    else:
        search_mode = "smart"
    
    server, acct, server_name = find_server_by_domain(domain, servers, search_mode=search_mode)
    
    if not server:
        print("❌ Domain not found on any server!")
        return
    
    cpanel_user = acct["user"]
    print(f"✅ Domain found on Server {server_name}")
    print(f"👤 cPanel User: {cpanel_user}")
    print(f"📧 Email: {acct.get('email', 'N/A')}")
    print(f"📦 Package: {acct.get('plan', 'N/A')}")
    
    print(f"\n⚠️  WARNING: This will permanently delete the account and ALL its data!")
    print(f"⚠️  This action cannot be undone!")
    
    confirmation = input(f"\nType 'DELETE {domain}' to confirm: ").strip()
    
    if confirmation == f"DELETE {domain}":
        params = {
            "user": cpanel_user,
            "keepdns": "0"
        }
        
        result = whm_api_call(server, "removeacct", params)
        
        if "error" not in result:
            print(f"✅ Account {cpanel_user} terminated successfully!")
            logging.info(f"Account terminated: {cpanel_user} ({domain})")
        else:
            print(f"❌ Failed to terminate account: {result['error']}")
    else:
        print("❌ Termination cancelled")

def change_cpanel_password_menu(domain, servers):
    """قائمة تغيير كلمة مرور cPanel"""
    print("\n🔑 Change cPanel Password")
    print("=" * 50)
    
    # خيارات البحث
    print("\n🔍 Search Options:")
    print("1. 🚀 Fast search (main domains only)")
    print("2. 🧠 Smart search (main domains first, then subdomains if needed)")
    print("3. 🔍 Full search (all domains + subdomains)")
    
    search_choice = input("Choose search type (1-3, default 2): ").strip()
    
    if search_choice == "1":
        search_mode = "fast"
    elif search_choice == "3":
        search_mode = "full"
    else:
        search_mode = "smart"
    
    print(f"\n🔍 Searching for domain: {domain}...")
    server, acct, server_name = find_server_by_domain(domain, servers, search_mode=search_mode)
    
    if not server:
        print("❌ Domain not found on any server!")
        return

    cpanel_user = acct["user"]
    print(f"\n✅ Domain found on Server {server_name}")
    print(f"📋 Domain: {domain}")
    print(f"👤 cPanel User: {cpanel_user}")
    print(f"📧 Email: {acct.get('email', 'N/A')}")
    print(f"📦 Package: {acct.get('plan', 'N/A')}")
    print(f"🖥️  Server: {server_name} ({server['ip']})")
    
    print(f"\n🔐 Password Requirements:")
    print("   - Minimum 8 characters")
    print("   - Use letters, numbers, and symbols")
    print("   - Avoid common words")
    
    # خيار المستخدم
    choice = input("\nDo you want to (1) Enter password manually or (2) Generate random strong password? [1/2]: ").strip()
    
    if choice == "2":
        new_password = generate_strong_password(16)
        print(f"\n✅ Generated strong password: {new_password}")
    else:
        while True:
            new_password = get_secure_password()
            if not new_password:
                print("❌ Password cannot be empty!")
                continue
            
            if len(new_password) < 8:
                print("❌ Password must be at least 8 characters!")
                continue
                
            confirm_password = get_secure_password()
            if new_password != confirm_password:
                print("❌ Passwords do not match!")
                continue
            
            break
    
    print(f"\n📋 Password Change Summary:")
    print(f"   Domain: {domain}")
    print(f"   cPanel User: {cpanel_user}")
    print(f"   Server: {server_name}")
    print(f"   Password Length: {len(new_password)} characters")
    
    if confirm_action(f"Change password for {cpanel_user}?"):
        params = {
            "user": cpanel_user,
            "password": new_password
        }
        
        print(f"\n🔄 Changing password...")
        result = whm_api_call(server, "passwd", params)
        
        if "error" not in result:
            print(f"\n✅ Password changed successfully!")
            print("=" * 50)
            print(f"🌐 Domain: {domain}")
            print(f"👤 cPanel User: {cpanel_user}")
            print(f"🔑 New Password: {new_password}")
            print(f"💻 cPanel URL: https://{domain}:2083")
            print(f"📧 Webmail URL: https://webmail.{domain}")
            print("=" * 50)
            logging.info(f"Password changed for: {cpanel_user} ({domain})")
            
            # اختياري: حفظ المعلومات في ملف
            if confirm_action("Save login details to file?"):
                filename = f"cpanel_login_{domain.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"cPanel Login Details\n")
                        f.write(f"===================\n")
                        f.write(f"Domain: {domain}\n")
                        f.write(f"Username: {cpanel_user}\n")
                        f.write(f"Password: {new_password}\n")
                        f.write(f"cPanel URL: https://{domain}:2083\n")
                        f.write(f"Webmail URL: https://webmail.{domain}\n")
                        f.write(f"Server: {server_name} ({server['ip']})\n")
                        f.write(f"Changed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    print(f"💾 Login details saved to: {filename}")
                except Exception as e:
                    print(f"❌ Error saving file: {str(e)}")
        else:
            print(f"❌ Failed to change password: {result['error']}")

def create_new_account(servers):
    """إنشاء حساب جديد"""
    print("\n➕ Create New Account")
    print("=" * 50)
    
    # عرض السيرفرات المتاحة
    print("Available Servers:")
    online_servers = get_online_servers(servers)
    if not online_servers:
        return
    
    for name, server in online_servers.items():
        print(f"   {name}: {server['ip']} (🟢 Online)")
    
    # اختيار السيرفر
    server_choice = input(f"\nChoose server ({'/'.join(online_servers.keys())}): ").strip()
    if server_choice not in online_servers:
        print("❌ Invalid server choice!")
        return
    
    server = online_servers[server_choice]
    
    # جمع معلومات الحساب
    domain = input("🌐 Domain name: ").strip()
    username = input("👤 Username: ").strip()
    password = get_secure_password()
    email = input("📧 Contact email: ").strip()
    package = input("📦 Package name (optional): ").strip() or "default"
    
    if not all([domain, username, password, email]):
        print("❌ All fields are required!")
        return
    
    print(f"\n📋 Account Details:")
    print(f"   Domain: {domain}")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Package: {package}")
    print(f"   Server: {server_choice}")
    
    if confirm_action("Create this account?"):
        params = {
            "username": username,
            "domain": domain,
            "password": password,
            "contactemail": email,
            "plan": package
        }
        
        result = whm_api_call(server, "createacct", params)
        
        if "error" not in result:
            print(f"✅ Account created successfully!")
            print(f"🌐 Domain: {domain}")
            print(f"👤 Username: {username}")
            print(f"🔑 Password: {password}")
            print(f"📧 Email: {email}")
            logging.info(f"Account created: {username} ({domain}) on server {server_choice}")
        else:
            print(f"❌ Failed to create account: {result['error']}")

def list_server_accounts(servers):
    """عرض حسابات سيرفر محدد"""
    print("\n📋 List Accounts on Server")
    print("=" * 50)
    
    # عرض السيرفرات المتاحة
    print("Available Servers:")
    online_servers = get_online_servers(servers)
    if not online_servers:
        return
    
    for name, server in online_servers.items():
        print(f"   {name}: {server['ip']} (🟢 Online)")
    
    # اختيار السيرفر
    server_choice = input(f"\nChoose server ({'/'.join(online_servers.keys())}): ").strip()
    if server_choice not in online_servers:
        print("❌ Invalid server choice!")
        return
    
    server = online_servers[server_choice]
    print(f"\n📡 Loading accounts from Server {server_choice}...")
    
    accounts = list_accounts(server)
    if not accounts:
        print("❌ No accounts found on this server!")
        return
    
    print(f"\n📊 Server {server_choice} Accounts Report")
    print("=" * 80)
    print(f"Server IP: {server['ip']}")
    print(f"Total Accounts: {len(accounts)}")
    print("=" * 80)
    
    active_count = 0
    suspended_count = 0
    
    print(f"{'#':<3} {'Domain':<25} {'User':<15} {'Status':<12} {'Package':<15} {'Disk (MB)':<10}")
    print("-" * 80)
    
    for i, acct in enumerate(accounts, 1):
        status = "🔴 Suspended" if acct.get('suspended', 0) == 1 else "🟢 Active"
        if acct.get('suspended', 0) == 1:
            suspended_count += 1
        else:
            active_count += 1
        
        disk_used = acct.get('diskused', 'N/A')
        
        print(f"{i:<3} {acct['domain']:<25} {acct['user']:<15} {status:<12} {acct.get('plan', 'N/A'):<15} {disk_used:<10}")
    
    print("-" * 80)
    print(f"Summary: {active_count} Active, {suspended_count} Suspended")
    
    # تصدير القائمة
    if confirm_action("\nExport accounts list?"):
        export_format = input("Export format (1=Excel, 2=CSV, 3=Both): ").strip()
        
        headers = ["Domain", "cPanel User", "Server", "Status", "Email", "Package", "Disk Used", "Creation Date", "Export Date"]
        data_rows = []
        
        for acct in accounts:
            data_rows.append([
                acct['domain'],
                acct['user'],
                server_choice,
                "Suspended" if acct.get('suspended', 0) == 1 else "Active",
                acct.get('email', 'N/A'),
                acct.get('plan', 'N/A'),
                acct.get('diskused', 'N/A'),
                datetime.fromtimestamp(int(acct.get('unix_startdate', 0))).strftime('%Y-%m-%d'),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        if export_format in ["1", "3"]:
            export_to_excel(data_rows, headers, f"accounts_{server_choice}", f"Accounts - {server_choice}")
        if export_format in ["2", "3"]:
            export_to_csv(data_rows, headers, f"accounts_{server_choice}")

def domain_statistics_report(servers):
    """تقرير إحصائيات الدومينات"""
    print("\n📊 Domain Statistics Report")
    print("=" * 50)
    
    total_domains = 0
    total_active = 0
    total_suspended = 0
    server_stats = {}
    package_stats = {}
    
    for server_name, server in servers.items():
        print(f"🖥️  Checking Server {server_name}...")
        
        if test_server_connection(server):
            accounts = list_accounts(server)
            server_domains = len(accounts)
            total_domains += server_domains
            
            active_count = sum(1 for acct in accounts if acct.get('suspended', 0) == 0)
            suspended_count = server_domains - active_count
            
            total_active += active_count
            total_suspended += suspended_count
            
            server_stats[server_name] = {
                'total': server_domains,
                'active': active_count,
                'suspended': suspended_count,
                'ip': server['ip']
            }
            
            # إحصائيات الباقات
            for acct in accounts:
                package = acct.get('plan', 'Unknown')
                if package not in package_stats:
                    package_stats[package] = 0
                package_stats[package] += 1
            
            print(f"   ✅ {server_domains} domains ({active_count} active, {suspended_count} suspended)")
        else:
            print(f"   🔴 Server offline")
            server_stats[server_name] = {
                'total': 0,
                'active': 0,
                'suspended': 0,
                'ip': server['ip'],
                'offline': True
            }
    
    # عرض التقرير الشامل
    print(f"\n📈 Overall Statistics:")
    print("=" * 60)
    print(f"Total Domains: {total_domains}")
    print(f"Active Domains: {total_active} ({(total_active/total_domains)*100:.1f}%)" if total_domains > 0 else "Active Domains: 0")
    print(f"Suspended Domains: {total_suspended} ({(total_suspended/total_domains)*100:.1f}%)" if total_domains > 0 else "Suspended Domains: 0")
    
    print(f"\n🖥️  Server Breakdown:")
    print("-" * 60)
    for server_name, stats in server_stats.items():
        if stats.get('offline'):
            print(f"{server_name} ({stats['ip']}): 🔴 OFFLINE")
        else:
            percentage = (stats['total']/total_domains)*100 if total_domains > 0 else 0
            print(f"{server_name} ({stats['ip']}): {stats['total']} domains ({percentage:.1f}%)")
            print(f"   Active: {stats['active']}, Suspended: {stats['suspended']}")
    
    print(f"\n📦 Package Distribution:")
    print("-" * 60)
    sorted_packages = sorted(package_stats.items(), key=lambda x: x[1], reverse=True)
    for package, count in sorted_packages:
        percentage = (count/total_domains)*100 if total_domains > 0 else 0
        print(f"{package}: {count} domains ({percentage:.1f}%)")

# === دوال إدارة SSH ===
def manage_ssh_menu(domain, servers):
    """قائمة إدارة SSH للحساب"""
    print(f"\n🔑 SSH Management for Domain: {domain}")
    print("=" * 60)
    
    # البحث عن الحساب
    account_info = find_account_by_domain(domain, servers)
    if not account_info:
        print(f"❌ Account not found for domain: {domain}")
        return
    
    server = account_info['server']
    cpanel_user = account_info['user']
    
    print(f"✅ Account found:")
    print(f"   Domain: {domain}")
    print(f"   User: {cpanel_user}")
    print(f"   Server: {account_info['server_name']}")
    
    while True:
        print(f"\n🔑 SSH Management Options:")
        print("1. 🔓 Enable SSH access")
        print("2. 🔒 Disable SSH access")
        print("3. 📋 Check SSH status")
        print("4. 🔑 Manage SSH keys")
        print("5. 📊 SSH connection info")
        print("0. 🔙 Back to main menu")
        
        ssh_choice = input("\nChoose option: ").strip()
        
        if ssh_choice == "1":
            enable_ssh_access(server, cpanel_user, domain)
        elif ssh_choice == "2":
            disable_ssh_access(server, cpanel_user, domain)
        elif ssh_choice == "3":
            check_ssh_status(server, cpanel_user, domain)
        elif ssh_choice == "4":
            manage_ssh_keys(server, cpanel_user, domain)
        elif ssh_choice == "5":
            show_ssh_connection_info(server, cpanel_user, domain)
        elif ssh_choice == "0":
            break
        else:
            print("❌ Invalid option")

def enable_ssh_access(server, cpanel_user, domain):
    """تفعيل SSH للحساب - نسخة محسنة من السكريبت القديم"""
    print(f"\n🔓 Enabling SSH access for {domain}...")
    
    try:
        # استخدام WHM API لتفعيل SSH مع معاملات محسنة
        params = {
            "user": cpanel_user,
            "HASSHELL": 1  # استخدام HASSHELL بدلاً من hasshell
        }
        
        print(f"   🔄 Calling modifyacct API...")
        result = whm_api_call(server, "modifyacct", params)
        
        print(f"   📊 API Response: {result}")
        
        # معالجة محسنة للنتائج
        if isinstance(result, dict):
            # فحص metadata أولاً (الطريقة الأساسية)
            metadata = result.get("metadata")
            if metadata and metadata.get("result") == 1:
                print(f"✅ SSH access enabled successfully for {domain}")
                print(f"   User: {cpanel_user}")
                print(f"   SSH Status: 🔓 Enabled")
                print(f"   Response: {metadata.get('reason', 'Shell access enabled successfully')}")
                
                # عرض تفاصيل الاتصال
                print(f"\n💡 SSH Connection Details:")
                print(f"   Host: {server['ip']}")
                print(f"   Username: {cpanel_user}")
                print(f"   Port: 22 (default)")
                print(f"   Protocol: SSH v2")
                print(f"💻 Example SSH command:")
                print(f"   ssh {cpanel_user}@{server['ip']}")
                print(f"   Note: User may need to set SSH password via cPanel")
                
                logging.info(f"SSH enabled for {domain} ({cpanel_user}) on {server['ip']}")
                return True
                
            elif metadata:
                error_msg = metadata.get("reason", "Operation failed")
                print(f"❌ Failed to enable SSH: {error_msg}")
                return False
            
            # فحص cpanelresult كبديل
            if "cpanelresult" in result:
                cpanel_result = result["cpanelresult"]
                if cpanel_result.get("event", {}).get("result") == 1:
                    print(f"✅ SSH access enabled successfully for {domain}")
                    print(f"   User: {cpanel_user}")
                    print(f"   SSH Status: 🔓 Enabled")
                    logging.info(f"SSH enabled for {domain} ({cpanel_user}) on {server['ip']}")
                    return True
                else:
                    error_msg = cpanel_result.get("event", {}).get("reason", "Operation failed")
                    print(f"❌ Failed to enable SSH: {error_msg}")
                    return False
            
            # فحص الأخطاء المباشرة
            if "error" in result:
                print(f"❌ Failed to enable SSH: {result['error']}")
                return False
        
        print(f"❌ Failed to enable SSH: Unexpected response format")
        return False
            
    except Exception as e:
        print(f"❌ Error enabling SSH: {str(e)}")
        logging.error(f"Error enabling SSH for {domain}: {str(e)}")
        return False

def disable_ssh_access(server, cpanel_user, domain):
    """إلغاء SSH للحساب - نسخة محسنة من السكريبت القديم"""
    print(f"\n🔒 Disabling SSH access for {domain}...")
    
    try:
        # استخدام WHM API لإلغاء SSH مع معاملات محسنة
        params = {
            "user": cpanel_user,
            "HASSHELL": 0  # استخدام HASSHELL بدلاً من hasshell
        }
        
        print(f"   🔄 Calling modifyacct API...")
        result = whm_api_call(server, "modifyacct", params)
        
        print(f"   📊 API Response: {result}")
        
        # معالجة محسنة للنتائج
        if isinstance(result, dict):
            # فحص metadata أولاً (الطريقة الأساسية)
            metadata = result.get("metadata")
            if metadata and metadata.get("result") == 1:
                print(f"✅ SSH access disabled successfully for {domain}")
                print(f"   User: {cpanel_user}")
                print(f"   SSH Status: 🔒 Disabled")
                print(f"   Response: {metadata.get('reason', 'Shell access disabled successfully')}")
                print(f"🔒 User {cpanel_user} no longer has SSH access")
                
                logging.info(f"SSH disabled for {domain} ({cpanel_user}) on {server['ip']}")
                return True
                
            elif metadata:
                error_msg = metadata.get("reason", "Operation failed")
                print(f"❌ Failed to disable SSH: {error_msg}")
                return False
            
            # فحص cpanelresult كبديل
            if "cpanelresult" in result:
                cpanel_result = result["cpanelresult"]
                if cpanel_result.get("event", {}).get("result") == 1:
                    print(f"✅ SSH access disabled successfully for {domain}")
                    print(f"   User: {cpanel_user}")
                    print(f"   SSH Status: 🔒 Disabled")
                    print(f"🔒 User {cpanel_user} no longer has SSH access")
                    logging.info(f"SSH disabled for {domain} ({cpanel_user}) on {server['ip']}")
                    return True
                else:
                    error_msg = cpanel_result.get("event", {}).get("reason", "Operation failed")
                    print(f"❌ Failed to disable SSH: {error_msg}")
                    return False
            
            # فحص الأخطاء المباشرة
            if "error" in result:
                print(f"❌ Failed to disable SSH: {result['error']}")
                return False
        
        print(f"❌ Failed to disable SSH: Unexpected response format")
        return False
            
    except Exception as e:
        print(f"❌ Error disabling SSH: {str(e)}")
        logging.error(f"Error disabling SSH for {domain}: {str(e)}")
        return False

def check_ssh_status(server, cpanel_user, domain):
    """فحص حالة SSH للحساب - نسخة محسنة مع فحص شامل"""
    print(f"\n📋 Checking SSH status for {domain}...")
    
    try:
        # الحصول على معلومات الحساب
        result = whm_api_call(server, "accountsummary", {
            "user": cpanel_user
        })
        
        print(f"📊 Raw API Response: {result}")
        
        if "error" not in result:
            account_data = result.get("acct", {})
            if isinstance(account_data, list) and len(account_data) > 0:
                account_data = account_data[0]
            
            # فحص شامل لحالة SSH
            shell_status = account_data.get("shell", "0")
            has_shell = account_data.get("hasshell", 0)
            HASSHELL = account_data.get("HASSHELL", 0)
            
            print(f"📊 SSH Status Report for {domain}:")
            print(f"   User: {cpanel_user}")
            print(f"   Shell field: {shell_status}")
            print(f"   Hasshell field: {has_shell}")
            print(f"   HASSHELL field: {HASSHELL}")
            
            # تحديد حالة SSH - إصلاح المنطق
            ssh_enabled = False
            # فحص shell field - قد يكون مسار مثل "/bin/bash" أو رقم
            if isinstance(shell_status, str):
                if shell_status and shell_status != "0" and shell_status != "" and shell_status != "nologin" and "noshell" not in shell_status:
                    ssh_enabled = True
            elif str(shell_status) == "1":
                ssh_enabled = True
            
            # فحص hasshell و HASSHELL fields
            if str(has_shell) == "1" or HASSHELL == 1:
                ssh_enabled = True
            
            print(f"   SSH Access: {'🔓 Enabled' if ssh_enabled else '🔒 Disabled'}")
            print(f"   Account Status: {'🟢 Active' if account_data.get('suspended', 0) == 0 else '🔴 Suspended'}")
            print(f"   Package: {account_data.get('plan', 'N/A')}")
            
            if ssh_enabled:
                print(f"   🔑 SSH Connection:")
                print(f"      Host: {server['ip']}")
                print(f"      Port: 22 (default)")
                print(f"      Username: {cpanel_user}")
                print(f"      Note: Use cPanel to set SSH password")
                
                # فحص إضافي للتأكد من أن SSH يعمل فعلياً
                print(f"\n   🔍 Additional SSH verification:")
                print(f"      Checking if SSH service is running...")
                
                # محاولة فحص SSH service
                ssh_check = whm_api_call(server, "restartservice", {
                    "service": "sshd"
                })
                
                if "error" not in ssh_check:
                    print(f"      ✅ SSH service is accessible")
                else:
                    print(f"      ⚠️  SSH service check failed: {ssh_check.get('error', 'Unknown')}")
            else:
                print(f"   ⚠️  SSH is disabled for this account")
                print(f"   🔍 All SSH fields are disabled:")
                print(f"      - shell: {shell_status}")
                print(f"      - hasshell: {has_shell}")
                print(f"      - HASSHELL: {HASSHELL}")
                
        else:
            print(f"❌ Failed to get account info: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error checking SSH status: {str(e)}")
        logging.error(f"Error checking SSH status for {domain}: {str(e)}")

def manage_ssh_keys(server, cpanel_user, domain):
    """إدارة مفاتيح SSH"""
    print(f"\n🔑 SSH Keys Management for {domain}")
    print("=" * 50)
    
    try:
        # محاولة الحصول على مفاتيح SSH (قد لا يكون مدعوماً في WHM API)
        print(f"ℹ️  SSH Keys Management:")
        print(f"   Note: SSH keys are managed via cPanel interface")
        print(f"   User: {cpanel_user}")
        print(f"   Domain: {domain}")
        print(f"   Server: {server['ip']}")
        print(f"\n📋 To manage SSH keys:")
        print(f"   1. Login to cPanel: https://{server['ip']}:2083")
        print(f"   2. Username: {cpanel_user}")
        print(f"   3. Go to: Security → SSH Access")
        print(f"   4. Add/Remove SSH keys as needed")
        
    except Exception as e:
        print(f"❌ Error managing SSH keys: {str(e)}")
        logging.error(f"Error managing SSH keys for {domain}: {str(e)}")

def show_ssh_connection_info(server, cpanel_user, domain):
    """عرض معلومات الاتصال SSH"""
    print(f"\n📊 SSH Connection Information for {domain}")
    print("=" * 60)
    
    try:
        # الحصول على معلومات الحساب
        result = whm_api_call(server, "accountsummary", {
            "user": cpanel_user
        })
        
        if "error" not in result:
            account_data = result.get("acct", {})
            has_shell = account_data.get("hasshell", 0)
            
            print(f"🌐 Domain: {domain}")
            print(f"👤 Username: {cpanel_user}")
            print(f"🖥️  Server: {server['ip']}")
            print(f"🔑 SSH Status: {'🔓 Enabled' if has_shell else '🔒 Disabled'}")
            
            if has_shell:
                print(f"\n🔗 SSH Connection Details:")
                print(f"   Command: ssh {cpanel_user}@{server['ip']}")
                print(f"   Port: 22 (default)")
                print(f"   Protocol: SSH v2")
                print(f"   Authentication: Password or SSH Key")
                
                print(f"\n📋 Connection Steps:")
                print(f"   1. Open terminal/SSH client")
                print(f"   2. Run: ssh {cpanel_user}@{server['ip']}")
                print(f"   3. Enter password when prompted")
                print(f"   4. Or use SSH key if configured")
                
                print(f"\n⚠️  Important Notes:")
                print(f"   • SSH password is separate from cPanel password")
                print(f"   • Set SSH password via cPanel → Security → SSH Access")
                print(f"   • SSH keys provide more secure access")
                print(f"   • Default SSH port is 22")
            else:
                print(f"\n❌ SSH is not enabled for this account")
                print(f"   To enable SSH, use option 1 in SSH management menu")
                
        else:
            print(f"❌ Failed to get account info: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error getting SSH connection info: {str(e)}")
        logging.error(f"Error getting SSH connection info for {domain}: {str(e)}")

# === دوال إدارة PHP ===
def manage_php_menu(domain, servers):
    """قائمة إدارة PHP للحساب"""
    print(f"\n🐘 PHP Management for Domain: {domain}")
    print("=" * 60)
    
    # البحث عن الحساب
    account_info = find_account_by_domain(domain, servers)
    if not account_info:
        print(f"❌ Account not found for domain: {domain}")
        return
    
    server = account_info['server']
    cpanel_user = account_info['user']
    
    print(f"✅ Account found:")
    print(f"   Domain: {domain}")
    print(f"   User: {cpanel_user}")
    print(f"   Server: {account_info['server_name']}")
    
    while True:
        print(f"\n🐘 PHP Management Options:")
        print("1. 🔄 Change PHP version")
        print("2. 📋 Check current PHP version")
        print("3. 📊 List available PHP versions")
        print("4. ⚙️  PHP configuration info")
        print("5. 🔧 PHP handler settings")
        print("0. 🔙 Back to main menu")
        
        php_choice = input("\nChoose option: ").strip()
        
        if php_choice == "1":
            change_php_version(server, cpanel_user, domain)
        elif php_choice == "2":
            check_current_php_version(server, cpanel_user, domain)
        elif php_choice == "3":
            list_available_php_versions(server, cpanel_user, domain)
        elif php_choice == "4":
            show_php_config_info(server, cpanel_user, domain)
        elif php_choice == "5":
            show_php_handler_settings(server, cpanel_user, domain)
        elif php_choice == "0":
            break
        else:
            print("❌ Invalid option")

def change_php_version(server, cpanel_user, domain):
    """تغيير نسخة PHP للحساب"""
    print(f"\n🔄 Changing PHP version for {domain}...")
    
    try:
        # الحصول على النسخ المتاحة أولاً
        print("📋 Available PHP versions:")
        php_versions = get_available_php_versions(server)
        
        if not php_versions:
            print("❌ No PHP versions available")
            return
        
        # عرض النسخ المتاحة
        for i, version in enumerate(php_versions, 1):
            print(f"   {i}. PHP {version}")
        
        # اختيار النسخة
        version_choice = input(f"\nChoose PHP version (1-{len(php_versions)}): ").strip()
        try:
            version_index = int(version_choice) - 1
            if 0 <= version_index < len(php_versions):
                selected_version = php_versions[version_index]
                
                # تأكيد التغيير
                confirm = input(f"\n⚠️  Change PHP version to {selected_version}? (y/N): ").strip().lower()
                if confirm == 'y':
                    # تغيير نسخة PHP
                    result = change_php_version_for_account(server, cpanel_user, selected_version)
                    if result:
                        print(f"✅ PHP version changed to {selected_version} for {domain}")
                        print(f"   Note: Changes may take a few minutes to take effect")
                        logging.info(f"PHP version changed to {selected_version} for {domain} ({cpanel_user}) on {server['ip']}")
                    else:
                        print(f"❌ Failed to change PHP version")
                else:
                    print("❌ PHP version change cancelled")
            else:
                print("❌ Invalid version selection")
        except ValueError:
            print("❌ Invalid input")
            
    except Exception as e:
        print(f"❌ Error changing PHP version: {str(e)}")
        logging.error(f"Error changing PHP version for {domain}: {str(e)}")

def check_current_php_version(server, cpanel_user, domain):
    """فحص نسخة PHP الحالية للحساب"""
    print(f"\n📋 Checking current PHP version for {domain}...")
    
    try:
        # محاولة الحصول على معلومات PHP
        result = cpanel_api_call(server, cpanel_user, "PHP", "get_php_info")
        
        if result and "cpanelresult" in result:
            php_info = result["cpanelresult"].get("data", {})
            current_version = php_info.get("version", "Unknown")
            
            print(f"📊 PHP Version Report for {domain}:")
            print(f"   Current Version: PHP {current_version}")
            print(f"   User: {cpanel_user}")
            print(f"   Domain: {domain}")
            
            # معلومات إضافية
            if "handler" in php_info:
                print(f"   Handler: {php_info['handler']}")
            if "sapi" in php_info:
                print(f"   SAPI: {php_info['sapi']}")
                
        else:
            print(f"ℹ️  PHP version info not available via API")
            print(f"   Check via cPanel → Software → MultiPHP Manager")
            
    except Exception as e:
        print(f"❌ Error checking PHP version: {str(e)}")
        logging.error(f"Error checking PHP version for {domain}: {str(e)}")

def list_available_php_versions(server, cpanel_user, domain):
    """عرض النسخ المتاحة من PHP"""
    print(f"\n📋 Available PHP versions for {domain}...")
    
    try:
        php_versions = get_available_php_versions(server)
        
        if php_versions:
            print(f"📊 Available PHP versions on {server['ip']}:")
            for i, version in enumerate(php_versions, 1):
                print(f"   {i}. PHP {version}")
            
            print(f"\n📋 To change PHP version:")
            print(f"   1. Use option 1 in PHP management menu")
            print(f"   2. Or via cPanel → Software → MultiPHP Manager")
            print(f"   3. Or via cPanel → Software → MultiPHP INI Editor")
        else:
            print("❌ No PHP versions available")
            
    except Exception as e:
        print(f"❌ Error listing PHP versions: {str(e)}")
        logging.error(f"Error listing PHP versions for {domain}: {str(e)}")

def show_php_config_info(server, cpanel_user, domain):
    """عرض معلومات إعدادات PHP"""
    print(f"\n⚙️  PHP Configuration Info for {domain}")
    print("=" * 60)
    
    try:
        print(f"📋 PHP Configuration Information:")
        print(f"   Domain: {domain}")
        print(f"   User: {cpanel_user}")
        print(f"   Server: {server['ip']}")
        
        print(f"\n📋 PHP Management via cPanel:")
        print(f"   1. MultiPHP Manager: Software → MultiPHP Manager")
        print(f"   2. PHP Selector: Software → PHP Selector")
        print(f"   3. MultiPHP INI Editor: Software → MultiPHP INI Editor")
        print(f"   4. PHP Configuration: Software → PHP Configuration")
        
        print(f"\n🔧 Common PHP Settings:")
        print(f"   • memory_limit: Maximum memory usage")
        print(f"   • max_execution_time: Script timeout")
        print(f"   • upload_max_filesize: Max file upload size")
        print(f"   • post_max_size: Max POST data size")
        print(f"   • display_errors: Show PHP errors")
        
        print(f"\n⚠️  Note:")
        print(f"   • PHP settings are managed via cPanel")
        print(f"   • Some settings may require server admin access")
        print(f"   • Changes may take a few minutes to take effect")
        
    except Exception as e:
        print(f"❌ Error showing PHP config info: {str(e)}")
        logging.error(f"Error showing PHP config info for {domain}: {str(e)}")

def show_php_handler_settings(server, cpanel_user, domain):
    """عرض إعدادات PHP Handler"""
    print(f"\n🔧 PHP Handler Settings for {domain}")
    print("=" * 60)
    
    try:
        print(f"📋 PHP Handler Information:")
        print(f"   Domain: {domain}")
        print(f"   User: {cpanel_user}")
        print(f"   Server: {server['ip']}")
        
        print(f"\n🔧 PHP Handlers:")
        print(f"   • cgi: Common Gateway Interface")
        print(f"   • fcgid: FastCGI with process management")
        print(f"   • suphp: Single user PHP")
        print(f"   • lsapi: LiteSpeed API")
        print(f"   • proxy_fcgi: Apache FastCGI proxy")
        
        print(f"\n📋 Handler Management:")
        print(f"   1. Via cPanel: Software → MultiPHP Manager")
        print(f"   2. Select domain and choose handler")
        print(f"   3. Handler affects security and performance")
        
        print(f"\n⚠️  Security Notes:")
        print(f"   • suphp: Most secure, runs as user")
        print(f"   • fcgid: Good balance of security/performance")
        print(f"   • cgi: Less secure, runs as web server user")
        
    except Exception as e:
        print(f"❌ Error showing PHP handler settings: {str(e)}")
        logging.error(f"Error showing PHP handler settings for {domain}: {str(e)}")

# === دوال مساعدة ===
def get_available_php_versions(server):
    """الحصول على النسخ المتاحة من PHP"""
    try:
        # محاولة الحصول على النسخ المتاحة
        result = whm_api_call(server, "php_get_system_versions")
        
        if "error" not in result and "versions" in result:
            return result["versions"]
        else:
            # قائمة افتراضية للنسخ الشائعة
            return ["7.4", "8.0", "8.1", "8.2", "8.3"]
            
    except:
        # قائمة افتراضية في حالة الفشل
        return ["7.4", "8.0", "8.1", "8.2", "8.3"]

def change_php_version_for_account(server, cpanel_user, php_version):
    """تغيير نسخة PHP للحساب"""
    try:
        # محاولة تغيير نسخة PHP
        result = cpanel_api_call(server, cpanel_user, "PHP", "set_php_version", {
            "version": php_version
        })
        
        if result and "cpanelresult" in result:
            return True
        else:
            return False
            
    except:
        return False

def find_account_by_domain(domain, servers):
    """البحث عن حساب بواسطة الدومين مع اختيار السيرفر"""
    found_servers = []
    
    # البحث في جميع السيرفرات المتصلة
    for server_name, server in servers.items():
        if test_server_connection(server):
            try:
                accounts = list_accounts(server)
                for acct in accounts:
                    if acct["domain"].lower() == domain.lower():
                        found_servers.append({
                            'server': server,
                            'server_name': server_name,
                            'user': acct['user'],
                            'domain': acct['domain'],
                            'status': 'online'
                        })
            except Exception as e:
                # إذا فشل في جلب الحسابات، السيرفر مش شغال
                found_servers.append({
                    'server': server,
                    'server_name': server_name,
                    'user': acct['user'] if 'acct' in locals() else 'Unknown',
                    'domain': domain,
                    'status': 'error',
                    'error': str(e)
                })
    
    if not found_servers:
        return None
    
    # إذا وجد سيرفر واحد فقط
    if len(found_servers) == 1:
        server_info = found_servers[0]
        if server_info["status"] == "online":
            return {
                'server': server_info['server'],
                'server_name': server_info['server_name'],
                'user': server_info['user'],
                'domain': server_info['domain']
            }
        else:
            print(f"⚠️  Domain found on Server {server_info['server_name']} but server has issues: {server_info.get('error', 'Unknown error')}")
            return None
    
    # إذا وجد أكثر من سيرفر، اعرض خيارات للمستخدم
    online_servers = [s for s in found_servers if s["status"] == "online"]
    if online_servers:
        if len(online_servers) > 1:
            print(f"🔍 Domain found on multiple servers:")
            for i, s in enumerate(online_servers, 1):
                print(f"   {i}. Server {s['server_name']} ({s['server']['ip']}) - {s['status']}")
            
            # عرض السيرفر المختار تلقائياً
            best_server = max(online_servers, key=lambda x: int(x["server_name"]) if x["server_name"].isdigit() else 0)
            best_index = next(i for i, s in enumerate(online_servers, 1) if s["server_name"] == best_server["server_name"])
            print(f"✅ Auto-selected: Server {best_server['server_name']} (option {best_index})")
            
            # إعطاء خيار للمستخدم
            while True:
                choice = input(f"\n🌐 Choose server (1-{len(online_servers)}) or press Enter for auto-selected: ").strip()
                
                if not choice:  # إذا ضغط Enter، استخدم السيرفر المختار تلقائياً
                    print(f"✅ Using auto-selected Server {best_server['server_name']}")
                    return {
                        'server': best_server['server'],
                        'server_name': best_server['server_name'],
                        'user': best_server['user'],
                        'domain': best_server['domain']
                    }
                
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(online_servers):
                        selected_server = online_servers[choice_num - 1]
                        print(f"✅ Selected Server {selected_server['server_name']} manually")
                        return {
                            'server': selected_server['server'],
                            'server_name': selected_server['server_name'],
                            'user': selected_server['user'],
                            'domain': selected_server['domain']
                        }
                    else:
                        print(f"❌ Invalid choice. Please enter 1-{len(online_servers)}")
                except ValueError:
                    print("❌ Invalid input. Please enter a number or press Enter for auto-selection")
        
        # إذا كان هناك سيرفر واحد فقط، استخدمه
        return {
            'server': online_servers[0]['server'],
            'server_name': online_servers[0]['server_name'],
            'user': online_servers[0]['user'],
            'domain': online_servers[0]['domain']
        }
    else:
        # جميع السيرفرات لديها مشاكل
        print(f"⚠️  Domain found on {len(found_servers)} servers but all have issues:")
        for s in found_servers:
            print(f"   Server {s['server_name']} ({s['server']['ip']}): {s.get('error', 'Unknown error')}")
        return None

# === دوال إدارة الأكونتات المتعددة ===
def bulk_ssh_management_menu(servers):
    """قائمة إدارة SSH للأكونتات المتعددة"""
    print(f"\n🚀 Bulk SSH Management")
    print("=" * 60)
    
    while True:
        print(f"\n🔑 Bulk SSH Management Options:")
        print("1. 🔓 Enable SSH for multiple accounts")
        print("2. 🔒 Disable SSH for multiple accounts")
        print("3. 📋 Check SSH status for multiple accounts")
        print("4. 📊 SSH status report for all accounts")
        print("5. 🔄 Force SSH service restart")
        print("6. 🔍 Debug: Check single account SSH status")
        print("7. 🖥️ Single server SSH management")
        print("0. 🔙 Back to main menu")
        
        bulk_choice = input("\nChoose option: ").strip()
        
        if bulk_choice == "1":
            bulk_enable_ssh(servers)
        elif bulk_choice == "2":
            bulk_disable_ssh(servers)
        elif bulk_choice == "3":
            bulk_check_ssh_status(servers)
        elif bulk_choice == "4":
            ssh_status_report_all_servers(servers)
        elif bulk_choice == "5":
            force_ssh_service_restart(servers)
        elif bulk_choice == "6":
            debug_check_single_account_ssh(servers)
        elif bulk_choice == "7":
            single_server_ssh_management(servers)
        elif bulk_choice == "0":
            break
        else:
            print("❌ Invalid option")

def single_server_ssh_management(servers):
    """إدارة SSH لسيرفر محدد واحد"""
    print(f"\n🖥️ Single Server SSH Management")
    print("=" * 60)
    
    # اختيار السيرفر
    print("🖥️ Available servers:")
    server_list = list(servers.keys())
    for i, server_name in enumerate(server_list, 1):
        server = servers[server_name]
        status = "🟢 Online" if test_server_connection(server) else "🔴 Offline"
        print(f"   {i}. Server {server_name} ({server['ip']}) - {status}")
    
    try:
        server_choice = input(f"\nChoose server (1-{len(server_list)}): ").strip()
        server_index = int(server_choice) - 1
        
        if 0 <= server_index < len(server_list):
            server_name = server_list[server_index]
            server = servers[server_name]
            
            if not test_server_connection(server):
                print(f"❌ Server {server_name} is offline")
                return
            
            print(f"\n✅ Selected Server: {server_name} ({server['ip']})")
            
            # قائمة العمليات للسيرفر المحدد
            while True:
                print(f"\n🖥️ SSH Management for Server {server_name}:")
                print("1. 🔓 Enable SSH for all accounts")
                print("2. 🔒 Disable SSH for all accounts")
                print("3. 📋 Check SSH status for all accounts")
                print("4. 📊 SSH status report for this server")
                print("5. 🔄 Restart SSH service on this server")
                print("6. 🎯 Enable SSH for specific accounts")
                print("7. 🎯 Disable SSH for specific accounts")
                print("0. 🔙 Back to server selection")
                
                operation_choice = input("\nChoose operation: ").strip()
                
                if operation_choice == "1":
                    enable_ssh_all_accounts_server(server, server_name)
                elif operation_choice == "2":
                    disable_ssh_all_accounts_server(server, server_name)
                elif operation_choice == "3":
                    check_ssh_all_accounts_server(server, server_name)
                elif operation_choice == "4":
                    ssh_status_report_single_server(server, server_name)
                elif operation_choice == "5":
                    restart_ssh_service_single_server(server, server_name)
                elif operation_choice == "6":
                    enable_ssh_specific_accounts_server(server, server_name)
                elif operation_choice == "7":
                    disable_ssh_specific_accounts_server(server, server_name)
                elif operation_choice == "0":
                    break
                else:
                    print("❌ Invalid option")
                    
        else:
            print("❌ Invalid server selection")
            
    except ValueError:
        print("❌ Invalid input")

def debug_check_single_account_ssh(servers):
    """فحص مفصل لحالة SSH لحساب واحد للتصحيح"""
    print(f"\n🔍 Debug: Check Single Account SSH Status")
    print("=" * 60)
    
    domain = input("🌐 Enter domain to debug: ").strip()
    if not domain:
        print("❌ Domain cannot be empty")
        return
    
    # البحث عن الحساب
    account_info = find_account_by_domain(domain, servers)
    if not account_info:
        print(f"❌ Account not found for domain: {domain}")
        return
    
    server = account_info['server']
    cpanel_user = account_info['user']
    
    print(f"\n✅ Account found:")
    print(f"   Domain: {domain}")
    print(f"   User: {cpanel_user}")
    print(f"   Server: {account_info['server_name']} ({server['ip']})")
    
    # فحص مفصل لحالة SSH
    print(f"\n🔍 Detailed SSH Status Check:")
    print("-" * 50)
    
    try:
        # 1. فحص accountsummary
        print(f"1. 📊 Checking accountsummary API...")
        result = whm_api_call(server, "accountsummary", {
            "user": cpanel_user
        })
        
        print(f"   📊 Raw API Response: {result}")
        
        if "error" not in result and "data" in result and "acct" in result["data"]:
            account_data = result["data"]["acct"]
            
            # معالجة acct field
            if isinstance(account_data, list) and len(account_data) > 0:
                account_data = account_data[0]
                print(f"   📋 acct field is a list, using first element")
            else:
                print(f"   📋 acct field is a dict")
            
            print(f"   📊 Processed account_data: {account_data}")
            
            # فحص جميع الحقول المتعلقة بـ SSH
            shell_status = account_data.get("shell", "0")
            has_shell = account_data.get("hasshell", 0)
            HASSHELL = account_data.get("HASSHELL", 0)
            
            print(f"\n2. 🔍 SSH-related fields:")
            print(f"   shell field: {shell_status} (type: {type(shell_status)})")
            print(f"   hasshell field: {has_shell} (type: {type(has_shell)})")
            print(f"   HASSHELL field: {HASSHELL} (type: {type(HASSHELL)})")
            
            # فحص شامل لحالة SSH - إصلاح المنطق
            ssh_enabled = False
            enabled_via = []
            
            # فحص shell field - قد يكون مسار مثل "/bin/bash" أو رقم
            if isinstance(shell_status, str):
                if shell_status and shell_status != "0" and shell_status != "" and shell_status != "nologin" and "noshell" not in shell_status:
                    ssh_enabled = True
                    enabled_via.append(f"shell={shell_status}")
            elif str(shell_status) == "1":
                ssh_enabled = True
                enabled_via.append("shell=1")
            
            # فحص hasshell field
            if str(has_shell) == "1":
                ssh_enabled = True
                enabled_via.append("hasshell=1")
            
            # فحص HASSHELL field
            if HASSHELL == 1:
                ssh_enabled = True
                enabled_via.append("HASSHELL=1")
            
            print(f"\n3. 📊 SSH Status Analysis:")
            print(f"   SSH Enabled: {'✅ Yes' if ssh_enabled else '❌ No'}")
            if ssh_enabled:
                print(f"   Enabled via: {', '.join(enabled_via)}")
            else:
                print(f"   All SSH fields are disabled")
                if isinstance(shell_status, str) and "noshell" in shell_status:
                    print(f"   💡 Shell field shows 'noshell' - SSH is disabled")
                elif isinstance(shell_status, str) and shell_status == "nologin":
                    print(f"   💡 Shell field shows 'nologin' - SSH is disabled")
                elif str(shell_status) == "0":
                    print(f"   💡 Shell field is '0' - SSH is disabled")
            
            # 2. فحص إضافي - محاولة modifyacct
            print(f"\n4. 🔍 Testing modifyacct API...")
            test_result = whm_api_call(server, "modifyacct", {
                "user": cpanel_user,
                "HASSHELL": 1
            })
            
            print(f"   📊 modifyacct test response: {test_result}")
            
            # 3. فحص SSH service
            print(f"\n5. 🔍 Checking SSH service...")
            ssh_check = whm_api_call(server, "restartservice", {
                "service": "sshd"
            })
            
            print(f"   📊 SSH service check: {ssh_check}")
            
        else:
            if "error" in result:
                print(f"❌ Failed to get account info: {result.get('error', 'Unknown error')}")
            elif "data" not in result:
                print(f"❌ Failed to get account info: No 'data' field in response")
                print(f"   📊 Available keys: {list(result.keys())}")
            elif "acct" not in result["data"]:
                print(f"❌ Failed to get account info: No 'acct' field in 'data'")
                print(f"   📊 Data keys: {list(result['data'].keys())}")
            else:
                print(f"❌ Failed to get account info: Unknown error")
            
    except Exception as e:
        print(f"❌ Error during debug check: {str(e)}")
        logging.error(f"Error during debug SSH check for {domain}: {str(e)}")

def enable_ssh_all_accounts_server(server, server_name):
    """تفعيل SSH لجميع الحسابات على سيرفر محدد"""
    print(f"\n🔓 Enable SSH for All Accounts on Server {server_name}")
    print("=" * 70)
    
    # الحصول على جميع الحسابات
    accounts = list_accounts(server)
    if not accounts:
        print(f"❌ No accounts found on Server {server_name}")
        return
    
    print(f"📋 Found {len(accounts)} accounts on Server {server_name}")
    
    # تأكيد العملية
    confirm = input(f"\n⚠️  Enable SSH for ALL {len(accounts)} accounts on Server {server_name}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    # تنفيذ العملية
    success_count = 0
    failed_count = 0
    results = []
    
    print(f"\n🔄 Processing {len(accounts)} accounts...")
    print("-" * 70)
    
    for i, account in enumerate(accounts, 1):
        print(f"[{i}/{len(accounts)}] Processing {account['domain']} ({account['user']})...")
        
        try:
            result = whm_api_call(server, "modifyacct", {
                "user": account['user'],
                "HASSHELL": 1
            })
            
            # فحص النجاح
            success = False
            error_msg = "Unknown error"
            
            if isinstance(result, dict):
                metadata = result.get("metadata")
                if metadata and metadata.get("result") == 1:
                    success = True
                    error_msg = metadata.get("reason", "SSH enabled successfully")
                elif metadata:
                    error_msg = metadata.get("reason", "Operation failed")
                elif "cpanelresult" in result:
                    cpanel_result = result["cpanelresult"]
                    if cpanel_result.get("event", {}).get("result") == 1:
                        success = True
                        error_msg = "SSH enabled successfully"
                    else:
                        error_msg = cpanel_result.get("event", {}).get("reason", "Operation failed")
                elif "error" in result:
                    error_msg = result["error"]
            
            if success:
                print(f"   ✅ SSH enabled for {account['domain']}")
                success_count += 1
                results.append({"domain": account['domain'], "user": account['user'], "status": "Success"})
            else:
                print(f"   ❌ Failed to enable SSH: {error_msg}")
                failed_count += 1
                results.append({"domain": account['domain'], "user": account['user'], "status": "Failed", "error": error_msg})
                
        except Exception as e:
            print(f"   ❌ Error enabling SSH: {str(e)}")
            failed_count += 1
            results.append({"domain": account['domain'], "user": account['user'], "status": "Error", "error": str(e)})
    
    # عرض النتائج
    print(f"\n📊 SSH Enable Results for Server {server_name}:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📋 Total: {len(accounts)}")
    
    # تصدير النتائج
    if results and confirm_action("\nExport results to file?"):
        export_bulk_results(results, f"ssh_enable_all_{server_name}")

def disable_ssh_all_accounts_server(server, server_name):
    """إلغاء SSH لجميع الحسابات على سيرفر محدد"""
    print(f"\n🔒 Disable SSH for All Accounts on Server {server_name}")
    print("=" * 70)
    
    # الحصول على جميع الحسابات
    accounts = list_accounts(server)
    if not accounts:
        print(f"❌ No accounts found on Server {server_name}")
        return
    
    print(f"📋 Found {len(accounts)} accounts on Server {server_name}")
    
    # تأكيد العملية
    confirm = input(f"\n⚠️  Disable SSH for ALL {len(accounts)} accounts on Server {server_name}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    # تنفيذ العملية
    success_count = 0
    failed_count = 0
    results = []
    
    print(f"\n🔄 Processing {len(accounts)} accounts...")
    print("-" * 70)
    
    for i, account in enumerate(accounts, 1):
        print(f"[{i}/{len(accounts)}] Processing {account['domain']} ({account['user']})...")
        
        try:
            result = whm_api_call(server, "modifyacct", {
                "user": account['user'],
                "HASSHELL": 0
            })
            
            # فحص النجاح
            success = False
            error_msg = "Unknown error"
            
            if isinstance(result, dict):
                metadata = result.get("metadata")
                if metadata and metadata.get("result") == 1:
                    success = True
                    error_msg = metadata.get("reason", "SSH disabled successfully")
                elif metadata:
                    error_msg = metadata.get("reason", "Operation failed")
                elif "cpanelresult" in result:
                    cpanel_result = result["cpanelresult"]
                    if cpanel_result.get("event", {}).get("result") == 1:
                        success = True
                        error_msg = "SSH disabled successfully"
                    else:
                        error_msg = cpanel_result.get("event", {}).get("reason", "Operation failed")
                elif "error" in result:
                    error_msg = result["error"]
            
            if success:
                print(f"   ✅ SSH disabled for {account['domain']}")
                success_count += 1
                results.append({"domain": account['domain'], "user": account['user'], "status": "Success"})
            else:
                print(f"   ❌ Failed to disable SSH: {error_msg}")
                failed_count += 1
                results.append({"domain": account['domain'], "user": account['user'], "status": "Failed", "error": error_msg})
                
        except Exception as e:
            print(f"   ❌ Error disabling SSH: {str(e)}")
            failed_count += 1
            results.append({"domain": account['domain'], "user": account['user'], "status": "Error", "error": str(e)})
    
    # عرض النتائج
    print(f"\n📊 SSH Disable Results for Server {server_name}:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📋 Total: {len(accounts)}")
    
    # تصدير النتائج
    if results and confirm_action("\nExport results to file?"):
        export_bulk_results(results, f"ssh_disable_all_{server_name}")

def diagnose_ssh_api_issues(server, server_name, accounts):
    """تشخيص مشاكل SSH API قبل الفحص الشامل"""
    print(f"\n🔍 Diagnosing SSH API Issues on Server {server_name}")
    print("-" * 60)
    
    # اختبار اتصال السيرفر
    print(f"1. 🔍 Testing server connection...")
    if not test_server_connection(server):
        print(f"   ❌ Server {server_name} connection failed!")
        return False
    else:
        print(f"   ✅ Server {server_name} connection OK")
    
    # اختبار WHM API العام
    print(f"2. 🔍 Testing WHM API...")
    try:
        test_result = whm_api_call(server, "version", {})
        if "error" in test_result:
            print(f"   ❌ WHM API test failed: {test_result.get('error', 'Unknown error')}")
            return False
        else:
            print(f"   ✅ WHM API test OK")
    except Exception as e:
        print(f"   ❌ WHM API test exception: {str(e)}")
        return False
    
    # اختبار accountsummary API مع حساب واحد
    print(f"3. 🔍 Testing accountsummary API...")
    if accounts:
        test_account = accounts[0]
        try:
            test_result = whm_api_call(server, "accountsummary", {
                "user": test_account['user']
            })
            
            if "error" in test_result:
                print(f"   ❌ accountsummary API failed: {test_result.get('error', 'Unknown error')}")
                print(f"   🔧 This explains why all accounts show errors!")
                print(f"   💡 Possible solutions:")
                print(f"      - Check WHM API permissions for 'accountsummary'")
                print(f"      - Verify account exists: {test_account['user']}")
                print(f"      - Check server load/timeout issues")
                print(f"      - Try different API endpoint")
                return False
            elif "data" not in test_result:
                print(f"   ❌ accountsummary API returned no 'data' field")
                print(f"   📊 Raw response keys: {list(test_result.keys())}")
                return False
            elif "acct" not in test_result["data"]:
                print(f"   ❌ accountsummary API returned no 'acct' field in 'data'")
                print(f"   📊 'data' field keys: {list(test_result['data'].keys())}")
                return False
            else:
                print(f"   ✅ accountsummary API test OK for {test_account['user']}")
                account_data = test_result["data"]["acct"]
                if isinstance(account_data, list):
                    print(f"   📋 'acct' field is a list with {len(account_data)} items")
                    if len(account_data) > 0:
                        print(f"   📊 First account data keys: {list(account_data[0].keys())}")
                else:
                    print(f"   📋 'acct' field is a dict with keys: {list(account_data.keys())}")
                return True
        except Exception as e:
            print(f"   ❌ accountsummary API exception: {str(e)}")
            return False
    
    return True

def check_ssh_all_accounts_server(server, server_name):
    """فحص حالة SSH لجميع الحسابات على سيرفر محدد"""
    print(f"\n📋 Check SSH Status for All Accounts on Server {server_name}")
    print("=" * 70)
    
    # الحصول على جميع الحسابات
    accounts = list_accounts(server)
    if not accounts:
        print(f"❌ No accounts found on Server {server_name}")
        return
    
    print(f"📋 Found {len(accounts)} accounts on Server {server_name}")
    
    # تشخيص مشاكل API قبل البدء
    if not diagnose_ssh_api_issues(server, server_name, accounts):
        print(f"\n❌ API diagnosis failed - aborting SSH status check")
        return
    
    # فحص الحالة
    enabled_count = 0
    disabled_count = 0
    error_count = 0
    results = []
    
    print(f"\n🔄 Checking SSH status for {len(accounts)} accounts...")
    print("-" * 100)
    print(f"{'Domain':<30} {'User':<20} {'SSH Status':<15} {'Account Status':<15} {'Shell Details'}")
    print("-" * 100)
    
    for account in accounts:
        try:
            result = whm_api_call(server, "accountsummary", {
                "user": account['user']
            })
            
            # تشخيص مفصل للاستجابة
            if "error" in result:
                error_msg = result.get('error', 'Unknown API error')
                print(f"{account['domain']:<30} {account['user']:<20} {'❌ API Error':<15} {'N/A':<15} {error_msg}")
                error_count += 1
                results.append({"domain": account['domain'], "user": account['user'], "ssh_status": "API Error", "account_status": "N/A", "error": error_msg})
            elif "data" not in result:
                print(f"{account['domain']:<30} {account['user']:<20} {'❌ No Data':<15} {'N/A':<15} No 'data' field in response")
                error_count += 1
                results.append({"domain": account['domain'], "user": account['user'], "ssh_status": "No Data", "account_status": "N/A", "error": "No 'data' field"})
            elif "acct" not in result["data"]:
                print(f"{account['domain']:<30} {account['user']:<20} {'❌ No Acct':<15} {'N/A':<15} No 'acct' field in 'data'")
                error_count += 1
                results.append({"domain": account['domain'], "user": account['user'], "ssh_status": "No Acct", "account_status": "N/A", "error": "No 'acct' field in 'data'"})
            elif "acct" in result["data"]:
                account_data = result["data"]["acct"]
                
                # معالجة acct field
                if isinstance(account_data, list) and len(account_data) > 0:
                    account_data = account_data[0]
                elif isinstance(account_data, list) and len(account_data) == 0:
                    print(f"{account['domain']:<30} {account['user']:<20} {'❌ Empty Data':<15} {'N/A':<15} Empty 'acct' array")
                    error_count += 1
                    results.append({"domain": account['domain'], "user": account['user'], "ssh_status": "Empty Data", "account_status": "N/A", "error": "Empty 'acct' array"})
                    continue
                
                # فحص شامل لحالة SSH
                shell_status = account_data.get("shell", "0")
                has_shell = account_data.get("hasshell", 0)
                HASSHELL = account_data.get("HASSHELL", 0)
                
                ssh_enabled = False
                # فحص shell field - قد يكون مسار مثل "/bin/bash" أو رقم
                if isinstance(shell_status, str):
                    if shell_status and shell_status != "0" and shell_status != "" and shell_status != "nologin":
                        ssh_enabled = True
                elif str(shell_status) == "1":
                    ssh_enabled = True
                
                # فحص hasshell و HASSHELL fields
                if str(has_shell) == "1" or HASSHELL == 1:
                    ssh_enabled = True
                
                is_suspended = account_data.get("suspended", 0)
                account_status = "🔴 Suspended" if is_suspended else "🟢 Active"
                ssh_status = "🔓 Enabled" if ssh_enabled else "🔒 Disabled"
                
                shell_details = f"shell={shell_status}, hasshell={has_shell}, HASSHELL={HASSHELL}"
                
                print(f"{account['domain']:<30} {account['user']:<20} {ssh_status:<15} {account_status:<15} {shell_details}")
                
                if ssh_enabled:
                    enabled_count += 1
                else:
                    disabled_count += 1
                
                results.append({
                    "domain": account['domain'],
                    "user": account['user'],
                    "ssh_status": "Enabled" if ssh_enabled else "Disabled",
                    "account_status": "Suspended" if is_suspended else "Active",
                    "shell_details": shell_details
                })
            else:
                print(f"{account['domain']:<30} {account['user']:<20} {'❌ Unknown Error':<15} {'N/A':<15} Unexpected response format")
                error_count += 1
                results.append({"domain": account['domain'], "user": account['user'], "ssh_status": "Unknown Error", "account_status": "N/A", "error": "Unexpected response format"})
                
        except Exception as e:
            error_msg = str(e)
            print(f"{account['domain']:<30} {account['user']:<20} {'❌ Exception':<15} {'N/A':<15} {error_msg}")
            error_count += 1
            results.append({"domain": account['domain'], "user": account['user'], "ssh_status": "Exception", "account_status": "N/A", "error": error_msg})
    
    # عرض النتائج
    print("-" * 100)
    print(f"\n📊 SSH Status Summary for Server {server_name}:")
    print(f"   🔓 SSH Enabled: {enabled_count}")
    print(f"   🔒 SSH Disabled: {disabled_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📋 Total: {len(accounts)}")
    
    # تصدير النتائج
    if results and confirm_action("\nExport results to file?"):
        export_bulk_results(results, f"ssh_status_{server_name}")

def ssh_status_report_single_server(server, server_name):
    """تقرير حالة SSH لسيرفر محدد واحد"""
    print(f"\n📊 SSH Status Report - Server {server_name}")
    print("=" * 70)
    
    # الحصول على جميع الحسابات
    accounts = list_accounts(server)
    if not accounts:
        print(f"❌ No accounts found on Server {server_name}")
        return
    
    print(f"📋 Found {len(accounts)} accounts on Server {server_name}")
    
    # تشخيص مشاكل API قبل البدء
    if not diagnose_ssh_api_issues(server, server_name, accounts):
        print(f"\n❌ API diagnosis failed - aborting SSH status report")
        return
    
    # فحص الحالة
    enabled_count = 0
    disabled_count = 0
    error_count = 0
    results = []
    
    print(f"\n🔄 Checking SSH status for {len(accounts)} accounts...")
    
    for account in accounts:
        try:
            result = whm_api_call(server, "accountsummary", {
                "user": account['user']
            })
            
            if "error" not in result and "data" in result and "acct" in result["data"]:
                account_data = result["data"]["acct"]
                
                # معالجة acct field
                if isinstance(account_data, list) and len(account_data) > 0:
                    account_data = account_data[0]
                
                # فحص شامل لحالة SSH
                shell_status = account_data.get("shell", "0")
                has_shell = account_data.get("hasshell", 0)
                HASSHELL = account_data.get("HASSHELL", 0)
                
                ssh_enabled = False
                # فحص shell field - قد يكون مسار مثل "/bin/bash" أو رقم - SSH REPORT FUNCTION
                if isinstance(shell_status, str):
                    if shell_status and shell_status != "0" and shell_status != "" and shell_status != "nologin" and "noshell" not in shell_status:
                        ssh_enabled = True
                elif str(shell_status) == "1":
                    ssh_enabled = True
                
                # فحص hasshell و HASSHELL fields
                if str(has_shell) == "1" or HASSHELL == 1:
                    ssh_enabled = True
                
                is_suspended = account_data.get("suspended", 0)
                
                if ssh_enabled:
                    enabled_count += 1
                else:
                    disabled_count += 1
                
                results.append({
                    "domain": account['domain'],
                    "user": account['user'],
                    "ssh_status": "Enabled" if ssh_enabled else "Disabled",
                    "account_status": "Suspended" if is_suspended else "Active",
                    "shell_details": f"shell={shell_status}, hasshell={has_shell}, HASSHELL={HASSHELL}"
                })
            else:
                error_count += 1
                
        except Exception as e:
            error_count += 1
    
    # عرض النتائج
    print(f"\n📊 SSH Status Summary for Server {server_name}:")
    print(f"   🔓 SSH Enabled: {enabled_count}")
    print(f"   🔒 SSH Disabled: {disabled_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📋 Total: {len(accounts)}")
    
    # عرض أمثلة للحسابات المفعلة
    if enabled_count > 0:
        print(f"\n📊 Sample enabled accounts:")
        enabled_accounts = [r for r in results if r['ssh_status'] == "Enabled"]
        for i, account in enumerate(enabled_accounts[:5], 1):
            print(f"   {i}. {account['user']} ({account['domain']}) - {account['shell_details']}")
        if len(enabled_accounts) > 5:
            print(f"   ... and {len(enabled_accounts) - 5} more")
    
    # تصدير النتائج
    if results and confirm_action("\nExport complete report to file?"):
        export_bulk_results(results, f"ssh_status_report_{server_name}")

def restart_ssh_service_single_server(server, server_name):
    """إعادة تشغيل SSH service على سيرفر محدد"""
    print(f"\n🔄 Restart SSH Service on Server {server_name}")
    print("=" * 70)
    
    print(f"⚠️  This will restart SSH service on Server {server_name}!")
    print(f"⚠️  All active SSH connections will be disconnected!")
    
    confirm = input(f"\n⚠️  Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    try:
        print(f"🔄 Restarting SSH service on Server {server_name}...")
        
        restart_result = whm_api_call(server, "restartservice", {
            "service": "sshd"
        })
        
        print(f"📊 Restart result: {restart_result}")
        
        if "error" not in restart_result:
            if "metadata" in restart_result:
                if restart_result["metadata"].get("result") == 1:
                    print(f"✅ SSH service restarted successfully on Server {server_name}")
                    print(f"⚠️  All SSH connections have been reset")
                    print(f"📋 Users may need to reconnect to SSH")
                    logging.info(f"SSH service restarted on {server_name} ({server['ip']})")
                else:
                    print(f"❌ SSH service restart failed: {restart_result['metadata'].get('reason', 'Unknown error')}")
            else:
                print(f"✅ SSH service restart command sent to Server {server_name}")
        else:
            print(f"❌ SSH service restart failed: {restart_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error restarting SSH service: {str(e)}")
        logging.error(f"Error restarting SSH service on {server_name}: {str(e)}")

def enable_ssh_specific_accounts_server(server, server_name):
    """تفعيل SSH لحسابات محددة على سيرفر محدد"""
    print(f"\n🎯 Enable SSH for Specific Accounts on Server {server_name}")
    print("=" * 70)
    
    # الحصول على جميع الحسابات
    accounts = list_accounts(server)
    if not accounts:
        print(f"❌ No accounts found on Server {server_name}")
        return
    
    print(f"📋 Available accounts on Server {server_name}:")
    for i, account in enumerate(accounts[:10], 1):
        print(f"   {i}. {account['domain']} ({account['user']})")
    if len(accounts) > 10:
        print(f"   ... and {len(accounts) - 10} more")
    
    # اختيار الحسابات
    print(f"\nSelect accounts to enable SSH:")
    print("1. 📋 Enter domains manually")
    print("2. 📂 Load from file")
    print("3. 📦 All accounts with specific package")
    
    method = input("\nChoose method (1-3): ").strip()
    
    if method == "1":
        domains = get_domains_manually()
    elif method == "2":
        domains = get_domains_from_file()
    elif method == "3":
        domains = get_domains_by_package({server_name: server})
    else:
        print("❌ Invalid method")
        return
    
    if not domains:
        print("❌ No domains selected")
        return
    
    # فلترة الحسابات للسيرفر المحدد
    server_domains = [account['domain'] for account in accounts]
    valid_domains = [domain for domain in domains if domain in server_domains]
    
    if not valid_domains:
        print("❌ No valid domains found on this server")
        return
    
    print(f"\n📋 Selected {len(valid_domains)} valid domains on Server {server_name}:")
    for i, domain in enumerate(valid_domains[:5], 1):
        print(f"   {i}. {domain}")
    if len(valid_domains) > 5:
        print(f"   ... and {len(valid_domains) - 5} more")
    
    # تأكيد العملية
    confirm = input(f"\n⚠️  Enable SSH for {len(valid_domains)} accounts on Server {server_name}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    # تنفيذ العملية
    success_count = 0
    failed_count = 0
    results = []
    
    print(f"\n🔄 Processing {len(valid_domains)} accounts...")
    print("-" * 70)
    
    for i, domain in enumerate(valid_domains, 1):
        # البحث عن الحساب في السيرفر
        account = None
        for acc in accounts:
            if acc['domain'] == domain:
                account = acc
                break
        
        if not account:
            print(f"[{i}/{len(valid_domains)}] ❌ Account not found: {domain}")
            failed_count += 1
            continue
        
        print(f"[{i}/{len(valid_domains)}] Processing {domain} ({account['user']})...")
        
        try:
            result = whm_api_call(server, "modifyacct", {
                "user": account['user'],
                "HASSHELL": 1
            })
            
            # فحص النجاح
            success = False
            error_msg = "Unknown error"
            
            if isinstance(result, dict):
                metadata = result.get("metadata")
                if metadata and metadata.get("result") == 1:
                    success = True
                    error_msg = metadata.get("reason", "SSH enabled successfully")
                elif metadata:
                    error_msg = metadata.get("reason", "Operation failed")
                elif "cpanelresult" in result:
                    cpanel_result = result["cpanelresult"]
                    if cpanel_result.get("event", {}).get("result") == 1:
                        success = True
                        error_msg = "SSH enabled successfully"
                    else:
                        error_msg = cpanel_result.get("event", {}).get("reason", "Operation failed")
                elif "error" in result:
                    error_msg = result["error"]
            
            if success:
                print(f"   ✅ SSH enabled for {domain}")
                success_count += 1
                results.append({"domain": domain, "user": account['user'], "status": "Success"})
            else:
                print(f"   ❌ Failed to enable SSH: {error_msg}")
                failed_count += 1
                results.append({"domain": domain, "user": account['user'], "status": "Failed", "error": error_msg})
                
        except Exception as e:
            print(f"   ❌ Error enabling SSH: {str(e)}")
            failed_count += 1
            results.append({"domain": domain, "user": account['user'], "status": "Error", "error": str(e)})
    
    # عرض النتائج
    print(f"\n📊 SSH Enable Results for Server {server_name}:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📋 Total: {len(valid_domains)}")
    
    # تصدير النتائج
    if results and confirm_action("\nExport results to file?"):
        export_bulk_results(results, f"ssh_enable_specific_{server_name}")

def disable_ssh_specific_accounts_server(server, server_name):
    """إلغاء SSH لحسابات محددة على سيرفر محدد"""
    print(f"\n🎯 Disable SSH for Specific Accounts on Server {server_name}")
    print("=" * 70)
    
    # الحصول على جميع الحسابات
    accounts = list_accounts(server)
    if not accounts:
        print(f"❌ No accounts found on Server {server_name}")
        return
    
    print(f"📋 Available accounts on Server {server_name}:")
    for i, account in enumerate(accounts[:10], 1):
        print(f"   {i}. {account['domain']} ({account['user']})")
    if len(accounts) > 10:
        print(f"   ... and {len(accounts) - 10} more")
    
    # اختيار الحسابات
    print(f"\nSelect accounts to disable SSH:")
    print("1. 📋 Enter domains manually")
    print("2. 📂 Load from file")
    print("3. 📦 All accounts with specific package")
    
    method = input("\nChoose method (1-3): ").strip()
    
    if method == "1":
        domains = get_domains_manually()
    elif method == "2":
        domains = get_domains_from_file()
    elif method == "3":
        domains = get_domains_by_package({server_name: server})
    else:
        print("❌ Invalid method")
        return
    
    if not domains:
        print("❌ No domains selected")
        return
    
    # فلترة الحسابات للسيرفر المحدد
    server_domains = [account['domain'] for account in accounts]
    valid_domains = [domain for domain in domains if domain in server_domains]
    
    if not valid_domains:
        print("❌ No valid domains found on this server")
        return
    
    print(f"\n📋 Selected {len(valid_domains)} valid domains on Server {server_name}:")
    for i, domain in enumerate(valid_domains[:5], 1):
        print(f"   {i}. {domain}")
    if len(valid_domains) > 5:
        print(f"   ... and {len(valid_domains) - 5} more")
    
    # تأكيد العملية
    confirm = input(f"\n⚠️  Disable SSH for {len(valid_domains)} accounts on Server {server_name}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    # تنفيذ العملية
    success_count = 0
    failed_count = 0
    results = []
    
    print(f"\n🔄 Processing {len(valid_domains)} accounts...")
    print("-" * 70)
    
    for i, domain in enumerate(valid_domains, 1):
        # البحث عن الحساب في السيرفر
        account = None
        for acc in accounts:
            if acc['domain'] == domain:
                account = acc
                break
        
        if not account:
            print(f"[{i}/{len(valid_domains)}] ❌ Account not found: {domain}")
            failed_count += 1
            continue
        
        print(f"[{i}/{len(valid_domains)}] Processing {domain} ({account['user']})...")
        
        try:
            result = whm_api_call(server, "modifyacct", {
                "user": account['user'],
                "HASSHELL": 0
            })
            
            # فحص النجاح
            success = False
            error_msg = "Unknown error"
            
            if isinstance(result, dict):
                metadata = result.get("metadata")
                if metadata and metadata.get("result") == 1:
                    success = True
                    error_msg = metadata.get("reason", "SSH disabled successfully")
                elif metadata:
                    error_msg = metadata.get("reason", "Operation failed")
                elif "cpanelresult" in result:
                    cpanel_result = result["cpanelresult"]
                    if cpanel_result.get("event", {}).get("result") == 1:
                        success = True
                        error_msg = "SSH disabled successfully"
                    else:
                        error_msg = cpanel_result.get("event", {}).get("reason", "Operation failed")
                elif "error" in result:
                    error_msg = result["error"]
            
            if success:
                print(f"   ✅ SSH disabled for {domain}")
                success_count += 1
                results.append({"domain": domain, "user": account['user'], "status": "Success"})
            else:
                print(f"   ❌ Failed to disable SSH: {error_msg}")
                failed_count += 1
                results.append({"domain": domain, "user": account['user'], "status": "Failed", "error": error_msg})
                
        except Exception as e:
            print(f"   ❌ Error disabling SSH: {str(e)}")
            failed_count += 1
            results.append({"domain": domain, "user": account['user'], "status": "Error", "error": str(e)})
    
    # عرض النتائج
    print(f"\n📊 SSH Disable Results for Server {server_name}:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📋 Total: {len(valid_domains)}")
    
    # تصدير النتائج
    if results and confirm_action("\nExport results to file?"):
        export_bulk_results(results, f"ssh_disable_specific_{server_name}")

def force_ssh_service_restart(servers):
    """إجبار إعادة تشغيل SSH service على جميع السيرفرات"""
    print(f"\n🔄 Force SSH Service Restart")
    print("=" * 50)
    
    print("⚠️  This will restart SSH service on all servers!")
    print("⚠️  All active SSH connections will be disconnected!")
    
    confirm = input("\n⚠️  Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    success_count = 0
    failed_count = 0
    
    for server_name, server in servers.items():
        print(f"\n🖥️  Server {server_name} ({server['ip']}):")
        
        if not test_server_connection(server):
            print(f"   🔴 Server offline")
            failed_count += 1
            continue
        
        try:
            # محاولة إعادة تشغيل SSH service
            print(f"   🔄 Restarting SSH service...")
            
            restart_result = whm_api_call(server, "restartservice", {
                "service": "sshd"
            })
            
            if "error" not in restart_result:
                print(f"   ✅ SSH service restarted successfully")
                success_count += 1
                logging.info(f"SSH service restarted on {server_name} ({server['ip']})")
            else:
                print(f"   ❌ SSH service restart failed: {restart_result.get('error', 'Unknown error')}")
                failed_count += 1
                
        except Exception as e:
            print(f"   ❌ Error restarting SSH service: {str(e)}")
            failed_count += 1
    
    print(f"\n📊 SSH Service Restart Results:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📋 Total: {len(servers)}")
    
    if success_count > 0:
        print(f"\n✅ SSH service restarted on {success_count} servers")
        print(f"⚠️  All SSH connections have been reset")
        print(f"📋 Users may need to reconnect to SSH")

def bulk_enable_ssh(servers):
    """تفعيل SSH لأكونتات متعددة"""
    print(f"\n🔓 Bulk Enable SSH Access")
    print("=" * 50)
    
    # اختيار طريقة تحديد الحسابات
    print("Select accounts method:")
    print("1. 📋 Enter domains manually")
    print("2. 📂 Load from file")
    print("3. 🖥️  All accounts on a server")
    print("4. 📦 All accounts with specific package")
    
    method = input("\nChoose method (1-4): ").strip()
    
    if method == "1":
        domains = get_domains_manually()
    elif method == "2":
        domains = get_domains_from_file()
    elif method == "3":
        domains = get_all_domains_from_server(servers)
    elif method == "4":
        domains = get_domains_by_package(servers)
    else:
        print("❌ Invalid method")
        return
    
    if not domains:
        print("❌ No domains selected")
        return
    
    print(f"\n📋 Selected {len(domains)} domains:")
    for i, domain in enumerate(domains[:5], 1):
        print(f"   {i}. {domain}")
    if len(domains) > 5:
        print(f"   ... and {len(domains) - 5} more")
    
    # تأكيد العملية
    confirm = input(f"\n⚠️  Enable SSH for {len(domains)} accounts? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    # تنفيذ العملية
    success_count = 0
    failed_count = 0
    results = []
    
    print(f"\n🔄 Processing {len(domains)} accounts...")
    print("-" * 60)
    
    for i, domain in enumerate(domains, 1):
        print(f"[{i}/{len(domains)}] Processing {domain}...")
        
        # البحث عن الحساب
        account_info = find_account_by_domain(domain, servers)
        if not account_info:
            print(f"   ❌ Account not found for {domain}")
            failed_count += 1
            results.append({"domain": domain, "status": "Not Found", "error": "Account not found"})
            continue
        
        # تفعيل SSH
        try:
            result = whm_api_call(account_info['server'], "modifyacct", {
                "user": account_info['user'],
                "HASSHELL": 1  # استخدام HASSHELL المحسن
            })
            
            # فحص النجاح بطريقة محسنة مثل السكريبت القديم
            success = False
            error_msg = "Unknown error"
            
            if isinstance(result, dict):
                # فحص metadata أولاً
                metadata = result.get("metadata")
                if metadata and metadata.get("result") == 1:
                    success = True
                    error_msg = metadata.get("reason", "SSH enabled successfully")
                elif metadata:
                    error_msg = metadata.get("reason", "Operation failed")
                # فحص cpanelresult كبديل
                elif "cpanelresult" in result:
                    cpanel_result = result["cpanelresult"]
                    if cpanel_result.get("event", {}).get("result") == 1:
                        success = True
                        error_msg = "SSH enabled successfully"
                    else:
                        error_msg = cpanel_result.get("event", {}).get("reason", "Operation failed")
                # فحص الأخطاء المباشرة
                elif "error" in result:
                    error_msg = result["error"]
                else:
                    error_msg = "Unexpected response format"
            
            if success:
                print(f"   ✅ SSH enabled for {domain}")
                
                # محاولة تطبيق التغيير فعلياً
                print(f"      🔄 Applying changes to system...")
                apply_result = apply_ssh_changes_to_system(account_info['server'], account_info['user'])
                
                if apply_result:
                    print(f"      ✅ System changes applied successfully")
                    results.append({"domain": domain, "status": "Success", "user": account_info['user'], "system_applied": True})
                else:
                    print(f"      ⚠️  SSH enabled but system changes may need manual restart")
                    results.append({"domain": domain, "status": "Success", "user": account_info['user'], "system_applied": False})
                
                success_count += 1
                logging.info(f"Bulk SSH enabled for {domain} ({account_info['user']}) on {account_info['server']['ip']}")
            else:
                print(f"   ❌ Failed to enable SSH: {error_msg}")
                failed_count += 1
                results.append({"domain": domain, "status": "Failed", "error": error_msg})
                
        except Exception as e:
            print(f"   ❌ Error enabling SSH: {str(e)}")
            failed_count += 1
            results.append({"domain": domain, "status": "Error", "error": str(e)})
    
    # عرض النتائج
    print(f"\n📊 Bulk SSH Enable Results:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📋 Total: {len(domains)}")
    
    # تصدير النتائج
    if results and confirm_action("\nExport results to file?"):
        export_bulk_results(results, "bulk_ssh_enable")

def bulk_disable_ssh(servers):
    """إلغاء SSH لأكونتات متعددة"""
    print(f"\n🔒 Bulk Disable SSH Access")
    print("=" * 50)
    
    # اختيار طريقة تحديد الحسابات
    print("Select accounts method:")
    print("1. 📋 Enter domains manually")
    print("2. 📂 Load from file")
    print("3. 🖥️  All accounts on a server")
    print("4. 📦 All accounts with specific package")
    
    method = input("\nChoose method (1-4): ").strip()
    
    if method == "1":
        domains = get_domains_manually()
    elif method == "2":
        domains = get_domains_from_file()
    elif method == "3":
        domains = get_all_domains_from_server(servers)
    elif method == "4":
        domains = get_domains_by_package(servers)
    else:
        print("❌ Invalid method")
        return
    
    if not domains:
        print("❌ No domains selected")
        return
    
    print(f"\n📋 Selected {len(domains)} domains:")
    for i, domain in enumerate(domains[:5], 1):
        print(f"   {i}. {domain}")
    if len(domains) > 5:
        print(f"   ... and {len(domains) - 5} more")
    
    # تأكيد العملية
    confirm = input(f"\n⚠️  Disable SSH for {len(domains)} accounts? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    # تنفيذ العملية
    success_count = 0
    failed_count = 0
    results = []
    
    print(f"\n🔄 Processing {len(domains)} accounts...")
    print("-" * 60)
    
    for i, domain in enumerate(domains, 1):
        print(f"[{i}/{len(domains)}] Processing {domain}...")
        
        # البحث عن الحساب
        account_info = find_account_by_domain(domain, servers)
        if not account_info:
            print(f"   ❌ Account not found for {domain}")
            failed_count += 1
            results.append({"domain": domain, "status": "Not Found", "error": "Account not found"})
            continue
        
        # إلغاء SSH
        try:
            result = whm_api_call(account_info['server'], "modifyacct", {
                "user": account_info['user'],
                "HASSHELL": 0  # استخدام HASSHELL المحسن
            })
            
            # فحص النجاح بطريقة محسنة مثل السكريبت القديم
            success = False
            error_msg = "Unknown error"
            
            if isinstance(result, dict):
                # فحص metadata أولاً
                metadata = result.get("metadata")
                if metadata and metadata.get("result") == 1:
                    success = True
                    error_msg = metadata.get("reason", "SSH disabled successfully")
                elif metadata:
                    error_msg = metadata.get("reason", "Operation failed")
                # فحص cpanelresult كبديل
                elif "cpanelresult" in result:
                    cpanel_result = result["cpanelresult"]
                    if cpanel_result.get("event", {}).get("result") == 1:
                        success = True
                        error_msg = "SSH disabled successfully"
                    else:
                        error_msg = cpanel_result.get("event", {}).get("reason", "Operation failed")
                # فحص الأخطاء المباشرة
                elif "error" in result:
                    error_msg = result["error"]
                else:
                    error_msg = "Unexpected response format"
            
            if success:
                print(f"   ✅ SSH disabled for {domain}")
                
                # محاولة تطبيق التغيير فعلياً
                print(f"      🔄 Applying changes to system...")
                apply_result = apply_ssh_changes_to_system(account_info['server'], account_info['user'])
                
                if apply_result:
                    print(f"      ✅ System changes applied successfully")
                    results.append({"domain": domain, "status": "Success", "user": account_info['user'], "system_applied": True})
                else:
                    print(f"      ⚠️  SSH disabled but system changes may need manual restart")
                    results.append({"domain": domain, "status": "Success", "user": account_info['user'], "system_applied": False})
                
                success_count += 1
                logging.info(f"Bulk SSH disabled for {domain} ({account_info['user']}) on {account_info['server']['ip']}")
            else:
                print(f"   ❌ Failed to disable SSH: {error_msg}")
                failed_count += 1
                results.append({"domain": domain, "status": "Failed", "error": error_msg})
                
        except Exception as e:
            print(f"   ❌ Error disabling SSH: {str(e)}")
            failed_count += 1
            results.append({"domain": domain, "status": "Error", "error": str(e)})
    
    # عرض النتائج
    print(f"\n📊 Bulk SSH Disable Results:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📋 Total: {len(domains)}")
    
    # تصدير النتائج
    if results and confirm_action("\nExport results to file?"):
        export_bulk_results(results, "bulk_ssh_disable")

def bulk_check_ssh_status(servers):
    """فحص حالة SSH لأكونتات متعددة"""
    print(f"\n📋 Bulk Check SSH Status")
    print("=" * 50)
    
    # اختيار طريقة تحديد الحسابات
    print("Select accounts method:")
    print("1. 📋 Enter domains manually")
    print("2. 📂 Load from file")
    print("3. 🖥️  All accounts on a server")
    print("4. 📦 All accounts with specific package")
    
    method = input("\nChoose method (1-4): ").strip()
    
    if method == "1":
        domains = get_domains_manually()
    elif method == "2":
        domains = get_domains_from_file()
    elif method == "3":
        domains = get_all_domains_from_server(servers)
    elif method == "4":
        domains = get_domains_by_package(servers)
    else:
        print("❌ Invalid method")
        return
    
    if not domains:
        print("❌ No domains selected")
        return
    
    # فحص الحالة
    enabled_count = 0
    disabled_count = 0
    error_count = 0
    results = []
    
    print(f"\n🔄 Checking SSH status for {len(domains)} accounts...")
    print("-" * 80)
    print(f"{'Domain':<30} {'User':<15} {'SSH Status':<15} {'Account Status'}")
    print("-" * 80)
    
    for domain in domains:
        # البحث عن الحساب
        account_info = find_account_by_domain(domain, servers)
        if not account_info:
            print(f"{domain:<30} {'N/A':<15} {'❌ Not Found':<15} {'N/A'}")
            error_count += 1
            results.append({"domain": domain, "user": "N/A", "ssh_status": "Not Found", "account_status": "N/A"})
            continue
        
        try:
            # الحصول على معلومات الحساب
            result = whm_api_call(account_info['server'], "accountsummary", {
                "user": account_info['user']
            })
            
            if "error" not in result:
                account_data = result.get("acct", {})
                has_shell = account_data.get("hasshell", 0)
                is_suspended = account_data.get("suspended", 0)
                
                ssh_status = "🔓 Enabled" if has_shell else "🔒 Disabled"
                account_status = "🔴 Suspended" if is_suspended else "🟢 Active"
                
                print(f"{domain:<30} {account_info['user']:<15} {ssh_status:<15} {account_status}")
                
                if has_shell:
                    enabled_count += 1
                else:
                    disabled_count += 1
                
                results.append({
                    "domain": domain,
                    "user": account_info['user'],
                    "ssh_status": "Enabled" if has_shell else "Disabled",
                    "account_status": "Suspended" if is_suspended else "Active",
                    "server": account_info['server_name']
                })
            else:
                print(f"{domain:<30} {account_info['user']:<15} {'❌ Error':<15} {'N/A'}")
                error_count += 1
                results.append({"domain": domain, "user": account_info['user'], "ssh_status": "Error", "account_status": "N/A"})
                
        except Exception as e:
            print(f"{domain:<30} {account_info['user']:<15} {'❌ Error':<15} {'N/A'}")
            error_count += 1
            results.append({"domain": domain, "user": account_info['user'], "ssh_status": "Error", "account_status": "N/A"})
    
    # عرض النتائج
    print("-" * 80)
    print(f"\n📊 SSH Status Summary:")
    print(f"   🔓 SSH Enabled: {enabled_count}")
    print(f"   🔒 SSH Disabled: {disabled_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📋 Total: {len(domains)}")
    
    # تصدير النتائج
    if results and confirm_action("\nExport results to file?"):
        export_bulk_results(results, "bulk_ssh_status_check")

def ssh_status_report_all_servers(servers):
    """تقرير حالة SSH لجميع الحسابات على جميع السيرفرات"""
    print(f"\n📊 SSH Status Report - All Servers")
    print("=" * 80)
    
    all_results = []
    total_enabled = 0
    total_disabled = 0
    total_error = 0
    
    for server_name, server in servers.items():
        print(f"\n🖥️  Server {server_name} ({server['ip']}):")
        
        if not test_server_connection(server):
            print(f"   🔴 Server offline")
            continue
        
        accounts = list_accounts(server)
        if not accounts:
            print(f"   📋 No accounts found")
            continue
        
        print(f"   📋 Checking {len(accounts)} accounts...")
        server_enabled = 0
        server_disabled = 0
        server_error = 0
        
        for account in accounts:
            try:
                result = whm_api_call(server, "accountsummary", {
                    "user": account['user']
                })
                
                if "error" not in result:
                    account_data = result.get("acct", {})
                    
                    # معالجة acct field - قد يكون list أو dict
                    if isinstance(account_data, list) and len(account_data) > 0:
                        account_data = account_data[0]
                    
                    # فحص شامل لحالة SSH
                    shell_status = account_data.get("shell", "0")
                    has_shell = account_data.get("hasshell", 0)
                    HASSHELL = account_data.get("HASSHELL", 0)
                    
                    # تحديد حالة SSH
                    ssh_enabled = False
                    if str(shell_status) == "1" or str(has_shell) == "1" or HASSHELL == 1:
                        ssh_enabled = True
                    
                    is_suspended = account_data.get("suspended", 0)
                    
                    if ssh_enabled:
                        server_enabled += 1
                        total_enabled += 1
                    else:
                        server_disabled += 1
                        total_disabled += 1
                    
                    all_results.append({
                        "domain": account['domain'],
                        "user": account['user'],
                        "server": server_name,
                        "ssh_status": "Enabled" if ssh_enabled else "Disabled",
                        "account_status": "Suspended" if is_suspended else "Active",
                        "shell_details": f"shell={shell_status}, hasshell={has_shell}, HASSHELL={HASSHELL}"
                    })
                else:
                    server_error += 1
                    total_error += 1
                    
            except Exception as e:
                server_error += 1
                total_error += 1
        
        print(f"   🔓 SSH Enabled: {server_enabled}")
        print(f"   🔒 SSH Disabled: {server_disabled}")
        print(f"   ❌ Errors: {server_error}")
        
        # عرض تفاصيل إضافية للتصحيح
        if server_enabled > 0:
            print(f"   📊 Sample enabled accounts:")
            enabled_count = 0
            for result in all_results:
                if result['server'] == server_name and result['ssh_status'] == "Enabled":
                    print(f"      - {result['user']} ({result['domain']}) - {result['shell_details']}")
                    enabled_count += 1
                    if enabled_count >= 3:  # عرض أول 3 حسابات مفعلة
                        break
    
    # عرض النتائج الإجمالية
    print(f"\n📊 Overall SSH Status Summary:")
    print(f"   🔓 Total SSH Enabled: {total_enabled}")
    print(f"   🔒 Total SSH Disabled: {total_disabled}")
    print(f"   ❌ Total Errors: {total_error}")
    print(f"   📋 Total Accounts: {len(all_results)}")
    
    # تصدير النتائج
    if all_results and confirm_action("\nExport complete report to file?"):
        export_bulk_results(all_results, "ssh_status_all_servers")

def bulk_php_management_menu(servers):
    """قائمة إدارة PHP للأكونتات المتعددة"""
    print(f"\n🚀 Bulk PHP Management")
    print("=" * 60)
    
    while True:
        print(f"\n🐘 Bulk PHP Management Options:")
        print("1. 🔄 Change PHP version for multiple accounts")
        print("2. 📋 Check PHP version for multiple accounts")
        print("3. 📊 PHP version report for all accounts")
        print("0. 🔙 Back to main menu")
        
        bulk_choice = input("\nChoose option: ").strip()
        
        if bulk_choice == "1":
            bulk_change_php_version(servers)
        elif bulk_choice == "2":
            bulk_check_php_version(servers)
        elif bulk_choice == "3":
            php_version_report_all_servers(servers)
        elif bulk_choice == "0":
            break
        else:
            print("❌ Invalid option")

def bulk_change_php_version(servers):
    """تغيير نسخة PHP لأكونتات متعددة"""
    print(f"\n🔄 Bulk Change PHP Version")
    print("=" * 50)
    
    # اختيار نسخة PHP أولاً
    print("📋 Available PHP versions:")
    php_versions = get_available_php_versions(list(servers.values())[0])
    
    for i, version in enumerate(php_versions, 1):
        print(f"   {i}. PHP {version}")
    
    version_choice = input(f"\nChoose PHP version (1-{len(php_versions)}): ").strip()
    try:
        version_index = int(version_choice) - 1
        if 0 <= version_index < len(php_versions):
            selected_version = php_versions[version_index]
        else:
            print("❌ Invalid version selection")
            return
    except ValueError:
        print("❌ Invalid input")
        return
    
    # اختيار طريقة تحديد الحسابات
    print(f"\nSelected PHP version: {selected_version}")
    print("Select accounts method:")
    print("1. 📋 Enter domains manually")
    print("2. 📂 Load from file")
    print("3. 🖥️  All accounts on a server")
    print("4. 📦 All accounts with specific package")
    
    method = input("\nChoose method (1-4): ").strip()
    
    if method == "1":
        domains = get_domains_manually()
    elif method == "2":
        domains = get_domains_from_file()
    elif method == "3":
        domains = get_all_domains_from_server(servers)
    elif method == "4":
        domains = get_domains_by_package(servers)
    else:
        print("❌ Invalid method")
        return
    
    if not domains:
        print("❌ No domains selected")
        return
    
    print(f"\n📋 Selected {len(domains)} domains:")
    for i, domain in enumerate(domains[:5], 1):
        print(f"   {i}. {domain}")
    if len(domains) > 5:
        print(f"   ... and {len(domains) - 5} more")
    
    # تأكيد العملية
    confirm = input(f"\n⚠️  Change PHP version to {selected_version} for {len(domains)} accounts? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled")
        return
    
    # تنفيذ العملية
    success_count = 0
    failed_count = 0
    results = []
    
    print(f"\n🔄 Processing {len(domains)} accounts...")
    print("-" * 60)
    
    for i, domain in enumerate(domains, 1):
        print(f"[{i}/{len(domains)}] Processing {domain}...")
        
        # البحث عن الحساب
        account_info = find_account_by_domain(domain, servers)
        if not account_info:
            print(f"   ❌ Account not found for {domain}")
            failed_count += 1
            results.append({"domain": domain, "status": "Not Found", "error": "Account not found"})
            continue
        
        # تغيير نسخة PHP
        try:
            result = change_php_version_for_account(account_info['server'], account_info['user'], selected_version)
            
            if result:
                print(f"   ✅ PHP version changed to {selected_version} for {domain}")
                success_count += 1
                results.append({"domain": domain, "status": "Success", "user": account_info['user'], "php_version": selected_version})
                logging.info(f"Bulk PHP version changed to {selected_version} for {domain} ({account_info['user']}) on {account_info['server']['ip']}")
            else:
                print(f"   ❌ Failed to change PHP version for {domain}")
                failed_count += 1
                results.append({"domain": domain, "status": "Failed", "error": "API call failed"})
                
        except Exception as e:
            print(f"   ❌ Error changing PHP version for {domain}: {str(e)}")
            failed_count += 1
            results.append({"domain": domain, "status": "Error", "error": str(e)})
    
    # عرض النتائج
    print(f"\n📊 Bulk PHP Version Change Results:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📋 Total: {len(domains)}")
    print(f"   🐘 Target Version: PHP {selected_version}")
    
    # تصدير النتائج
    if results and confirm_action("\nExport results to file?"):
        export_bulk_results(results, f"bulk_php_change_to_{selected_version}")

def bulk_check_php_version(servers):
    """فحص نسخة PHP لأكونتات متعددة"""
    print(f"\n📋 Bulk Check PHP Version")
    print("=" * 50)
    
    # اختيار طريقة تحديد الحسابات
    print("Select accounts method:")
    print("1. 📋 Enter domains manually")
    print("2. 📂 Load from file")
    print("3. 🖥️  All accounts on a server")
    print("4. 📦 All accounts with specific package")
    
    method = input("\nChoose method (1-4): ").strip()
    
    if method == "1":
        domains = get_domains_manually()
    elif method == "2":
        domains = get_domains_from_file()
    elif method == "3":
        domains = get_all_domains_from_server(servers)
    elif method == "4":
        domains = get_domains_by_package(servers)
    else:
        print("❌ Invalid method")
        return
    
    if not domains:
        print("❌ No domains selected")
        return
    
    # فحص نسخة PHP
    version_count = {}
    error_count = 0
    results = []
    
    print(f"\n🔄 Checking PHP version for {len(domains)} accounts...")
    print("-" * 80)
    print(f"{'Domain':<30} {'User':<15} {'PHP Version':<15} {'Account Status'}")
    print("-" * 80)
    
    for domain in domains:
        # البحث عن الحساب
        account_info = find_account_by_domain(domain, servers)
        if not account_info:
            print(f"{domain:<30} {'N/A':<15} {'❌ Not Found':<15} {'N/A'}")
            error_count += 1
            results.append({"domain": domain, "user": "N/A", "php_version": "Not Found", "account_status": "N/A"})
            continue
        
        try:
            # محاولة الحصول على معلومات PHP
            result = cpanel_api_call(account_info['server'], account_info['user'], "PHP", "get_php_info")
            
            if result and "cpanelresult" in result:
                php_info = result["cpanelresult"].get("data", {})
                current_version = php_info.get("version", "Unknown")
                
                # فحص حالة الحساب
                account_result = whm_api_call(account_info['server'], "accountsummary", {
                    "user": account_info['user']
                })
                
                if "error" not in account_result:
                    account_data = account_result.get("acct", {})
                    is_suspended = account_data.get("suspended", 0)
                    account_status = "🔴 Suspended" if is_suspended else "🟢 Active"
                else:
                    account_status = "N/A"
                
                print(f"{domain:<30} {account_info['user']:<15} {'PHP ' + current_version:<15} {account_status}")
                
                # عد النسخ
                if current_version in version_count:
                    version_count[current_version] += 1
                else:
                    version_count[current_version] = 1
                
                results.append({
                    "domain": domain,
                    "user": account_info['user'],
                    "php_version": current_version,
                    "account_status": "Suspended" if is_suspended else "Active",
                    "server": account_info['server_name']
                })
            else:
                print(f"{domain:<30} {account_info['user']:<15} {'❌ Unknown':<15} {'N/A'}")
                error_count += 1
                results.append({"domain": domain, "user": account_info['user'], "php_version": "Unknown", "account_status": "N/A"})
                
        except Exception as e:
            print(f"{domain:<30} {account_info['user']:<15} {'❌ Error':<15} {'N/A'}")
            error_count += 1
            results.append({"domain": domain, "user": account_info['user'], "php_version": "Error", "account_status": "N/A"})
    
    # عرض النتائج
    print("-" * 80)
    print(f"\n📊 PHP Version Summary:")
    for version, count in sorted(version_count.items()):
        print(f"   🐘 PHP {version}: {count} accounts")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📋 Total: {len(domains)}")
    
    # تصدير النتائج
    if results and confirm_action("\nExport results to file?"):
        export_bulk_results(results, "bulk_php_version_check")

def php_version_report_all_servers(servers):
    """تقرير نسخة PHP لجميع الحسابات على جميع السيرفرات"""
    print(f"\n📊 PHP Version Report - All Servers")
    print("=" * 80)
    
    all_results = []
    all_version_count = {}
    total_error = 0
    
    for server_name, server in servers.items():
        print(f"\n🖥️  Server {server_name} ({server['ip']}):")
        
        if not test_server_connection(server):
            print(f"   🔴 Server offline")
            continue
        
        accounts = list_accounts(server)
        if not accounts:
            print(f"   📋 No accounts found")
            continue
        
        print(f"   📋 Checking PHP versions for {len(accounts)} accounts...")
        server_version_count = {}
        server_error = 0
        
        for account in accounts:
            try:
                result = cpanel_api_call(server, account['user'], "PHP", "get_php_info")
                
                if result and "cpanelresult" in result:
                    php_info = result["cpanelresult"].get("data", {})
                    current_version = php_info.get("version", "Unknown")
                    
                    # عد النسخ للسيرفر
                    if current_version in server_version_count:
                        server_version_count[current_version] += 1
                    else:
                        server_version_count[current_version] = 1
                    
                    # عد النسخ الإجمالي
                    if current_version in all_version_count:
                        all_version_count[current_version] += 1
                    else:
                        all_version_count[current_version] = 1
                    
                    # فحص حالة الحساب
                    account_result = whm_api_call(server, "accountsummary", {
                        "user": account['user']
                    })
                    
                    if "error" not in account_result:
                        account_data = account_result.get("acct", {})
                        is_suspended = account_data.get("suspended", 0)
                    else:
                        is_suspended = 0
                    
                    all_results.append({
                        "domain": account['domain'],
                        "user": account['user'],
                        "server": server_name,
                        "php_version": current_version,
                        "account_status": "Suspended" if is_suspended else "Active"
                    })
                else:
                    server_error += 1
                    total_error += 1
                    
            except Exception as e:
                server_error += 1
                total_error += 1
        
        # عرض نتائج السيرفر
        for version, count in sorted(server_version_count.items()):
            print(f"   🐘 PHP {version}: {count} accounts")
        if server_error > 0:
            print(f"   ❌ Errors: {server_error}")
    
    # عرض النتائج الإجمالية
    print(f"\n📊 Overall PHP Version Summary:")
    for version, count in sorted(all_version_count.items()):
        print(f"   🐘 PHP {version}: {count} accounts")
    print(f"   ❌ Total Errors: {total_error}")
    print(f"   📋 Total Accounts: {len(all_results)}")
    
    # تصدير النتائج
    if all_results and confirm_action("\nExport complete report to file?"):
        export_bulk_results(all_results, "php_version_all_servers")

# === دوال مساعدة للعمليات المتعددة ===
def get_domains_manually():
    """الحصول على قائمة الدومينات يدوياً"""
    domains = []
    print("\nEnter domains (one per line, empty line to finish):")
    while True:
        domain = input("Domain: ").strip()
        if not domain:
            break
        domains.append(domain)
        print(f"   ✓ Added: {domain}")
    return domains

def get_domains_from_file():
    """الحصول على قائمة الدومينات من ملف"""
    file_path = input("\n📂 Enter file path: ").strip()
    if not file_path:
        return []
    
    try:
        domains = []
        with open(file_path, 'r') as f:
            for line in f:
                domain = line.strip()
                if domain and not domain.startswith('#'):
                    domains.append(domain)
        
        print(f"✅ Loaded {len(domains)} domains from file")
        return domains
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return []
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return []

def get_all_domains_from_server(servers):
    """الحصول على جميع الدومينات من سيرفر محدد"""
    print("\n🖥️  Available servers:")
    server_list = list(servers.keys())
    for i, server_name in enumerate(server_list, 1):
        print(f"   {i}. Server {server_name} ({servers[server_name]['ip']})")
    
    try:
        server_choice = input(f"\nChoose server (1-{len(server_list)}): ").strip()
        server_index = int(server_choice) - 1
        
        if 0 <= server_index < len(server_list):
            server_name = server_list[server_index]
            server = servers[server_name]
            
            if test_server_connection(server):
                accounts = list_accounts(server)
                domains = [account['domain'] for account in accounts]
                print(f"✅ Found {len(domains)} domains on Server {server_name}")
                return domains
            else:
                print(f"❌ Server {server_name} is offline")
                return []
        else:
            print("❌ Invalid server selection")
            return []
            
    except ValueError:
        print("❌ Invalid input")
        return []

def get_domains_by_package(servers):
    """الحصول على الدومينات حسب الباقة"""
    package_name = input("\n📦 Enter package name: ").strip()
    if not package_name:
        return []
    
    domains = []
    for server_name, server in servers.items():
        if test_server_connection(server):
            accounts = list_accounts(server)
            for account in accounts:
                if account.get('plan', '').lower() == package_name.lower():
                    domains.append(account['domain'])
    
    print(f"✅ Found {len(domains)} domains with package '{package_name}'")
    return domains

def apply_ssh_changes_to_system(server, cpanel_user):
    """تطبيق تغييرات SSH على النظام - نسخة محسنة من السكريبت القديم"""
    try:
        # التحقق من حالة SSH الحالية أولاً
        print(f"         🔍 Verifying SSH status...")
        
        # استخدام accountsummary للتحقق من الحالة
        check_result = whm_api_call(server, "accountsummary", {
            "user": cpanel_user
        })
        
        print(f"         📊 Raw API response: {check_result}")
        
        if "error" not in check_result and "acct" in check_result:
            acct_data = check_result["acct"][0] if isinstance(check_result["acct"], list) else check_result["acct"]
            shell_status = acct_data.get("shell", "0")
            has_shell = acct_data.get("hasshell", 0)
            
            print(f"         📊 Account shell status: shell={shell_status}, hasshell={has_shell}")
            
            # فحص شامل لحالة SSH
            ssh_enabled = False
            
            # فحص 1: shell field
            if str(shell_status) == "1":
                ssh_enabled = True
                print(f"         ✅ SSH enabled via shell field")
            
            # فحص 2: hasshell field
            if str(has_shell) == "1":
                ssh_enabled = True
                print(f"         ✅ SSH enabled via hasshell field")
            
            # فحص 3: HASSHELL field (معامل WHM API)
            if acct_data.get("HASSHELL", 0) == 1:
                ssh_enabled = True
                print(f"         ✅ SSH enabled via HASSHELL field")
            
            if ssh_enabled:
                print(f"         ✅ SSH is properly enabled in account settings")
                
                # محاولة إعادة تشغيل SSH service لتطبيق التغييرات
                print(f"         🔄 Restarting SSH service to apply changes...")
                
                restart_result = whm_api_call(server, "restartservice", {
                    "service": "sshd"
                })
                
                print(f"         📊 Restart result: {restart_result}")
                
                if "error" not in restart_result:
                    if "metadata" in restart_result:
                        if restart_result["metadata"].get("result") == 1:
                            print(f"         ✅ SSH service restarted successfully")
                            return True
                        else:
                            print(f"         ⚠️  SSH service restart returned: {restart_result['metadata'].get('reason', 'Unknown')}")
                    else:
                        print(f"         ✅ SSH service restart command sent")
                        return True
                else:
                    print(f"         ⚠️  SSH service restart failed: {restart_result.get('error', 'Unknown error')}")
                    
                    # محاولة بديلة
                    print(f"         🔄 Trying alternative restart method...")
                    alt_result = whm_api_call(server, "restartservice", {
                        "service": "ssh"
                    })
                    
                    if "error" not in alt_result:
                        print(f"         ✅ SSH service restarted via alternative method")
                        return True
                
                # حتى لو فشلت إعادة التشغيل، SSH مفعل في الحساب
                print(f"         ⚠️  SSH is enabled in account but service restart may be needed")
                return True
            else:
                print(f"         ❌ SSH is not properly enabled in account settings")
                print(f"         🔍 All SSH fields are disabled: shell={shell_status}, hasshell={has_shell}")
                return False
        else:
            print(f"         ❌ Could not verify account status")
            if "error" in check_result:
                print(f"         📊 Error details: {check_result['error']}")
            return False
                
    except Exception as e:
        print(f"         ❌ Error applying SSH changes: {str(e)}")
        return False

def export_bulk_results(results, operation_name):
    """تصدير نتائج العمليات المتعددة"""
    try:
        # إنشاء مجلد التقارير إذا لم يكن موجوداً
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # تحديد العناوين والبيانات
        if results:
            # استخراج العناوين من أول عنصر
            headers = list(results[0].keys())
            # تحويل البيانات إلى قائمة من القوائم
            data_rows = []
            for result in results:
                row = [result.get(header, "") for header in headers]
                data_rows.append(row)
        else:
            headers = []
            data_rows = []
        
        # تصدير Excel
        excel_filename = f"{operation_name}_{timestamp}"
        export_to_excel(data_rows, headers, excel_filename, f"Bulk Operation: {operation_name}")
        
        # تصدير CSV
        csv_filename = f"{operation_name}_{timestamp}"
        export_to_csv(data_rows, headers, csv_filename)
        
        logging.info(f"Bulk operation results exported: {operation_name}")
        
    except Exception as e:
        print(f"❌ Error exporting results: {str(e)}")
        logging.error(f"Error exporting bulk results: {str(e)}")

# === القائمة الرئيسية ===
def main():
    """الدالة الرئيسية"""
    try:
        servers = initialize_script("WHM Accounts & Domains Management")
        
        while True:
            print(f"\n{'='*20} ACCOUNTS & DOMAINS MANAGEMENT {'='*20}")
            print("🔍 Domain Search & Management:")
            print("1.  🌐 Search domain across all servers")
            print("2.  📋 List all domains on all servers")
            print("3.  🎯 Advanced domain search")
            print("4.  📊 Domain statistics report")
            print("5.  🔍 List all available domains (Main + Subdomains)")
            print("6.  🔎 Search domains by keyword")
            print("7.  🧪 Test subdomain loading for specific domain")
            
            print("\n👥 Account Management:")
            print("8.  📋 List accounts on a server")
            print("9.  ➕ Create new account")
            print("10. ⏸️  Suspend account by domain")
            print("11. ▶️  Unsuspend account by domain")
            print("12. 🗑️  Terminate account by domain")
            print("13. 🔑 Change cPanel password by domain")
            
            print("\n🔧 System Tools:")
            print("14. 🌐 Check server status")
            print("15. 📜 View operation logs")
            print("16. 🎲 Generate random password")
            
            print("\n🔐 SSH & PHP Management:")
            print("17. 🔑 Manage SSH access for account")
            print("18. 🐘 Manage PHP version for account")
            
            print("\n🚀 Bulk Operations:")
            print("19. 🔑 Bulk SSH management")
            print("20. 🐘 Bulk PHP management")
            
            print("\n0.  🚪 Exit")
            print("=" * 75)
            
            choice = input("Choose option: ").strip()

            if choice == "1":
                domain = input("\n🌐 Enter domain to search: ").strip()
                if domain:
                    search_domain_across_servers(domain, servers)
                else:
                    print("❌ Domain cannot be empty")

            elif choice == "2":
                list_all_domains(servers)

            elif choice == "3":
                print("\n🔍 Advanced Domain Search")
                print("=" * 50)
                print("Search Options:")
                print("1. 🔤 Search by domain name pattern")
                print("2. 📅 Search by creation date")
                print("3. 💾 Search by disk usage")
                print("4. 📦 Search by package")
                print("5. 📊 Search by status")
                
                search_choice = input("\nChoose search option: ").strip()
                found_domains = []
                
                if search_choice == "1":
                    pattern = input("Enter domain pattern (e.g., *blog*, *.com): ").strip()
                    if pattern:
                        found_domains = advanced_domain_search(servers, pattern=pattern)
                elif search_choice == "2":
                    date_range = input("Enter date range (YYYY-MM-DD,YYYY-MM-DD): ").strip()
                    if date_range:
                        found_domains = advanced_domain_search(servers, date_range=date_range)
                elif search_choice == "3":
                    size = input("Enter minimum disk usage in MB: ").strip()
                    if size:
                        found_domains = advanced_domain_search(servers, min_disk_usage=size)
                elif search_choice == "4":
                    package = input("Enter package name: ").strip()
                    if package:
                        found_domains = advanced_domain_search(servers, package=package)
                elif search_choice == "5":
                    status = input("Enter status (active/suspended): ").strip()
                    if status:
                        found_domains = advanced_domain_search(servers, status=status)
                else:
                    print("❌ Invalid option")
                    continue
                    
                if found_domains:
                    print(f"\n📊 Found {len(found_domains)} matching domains:")
                    print("-" * 80)
                    for i, domain in enumerate(found_domains, 1):
                        print(f"{i}. 🌐 {domain['domain']} - Server: {domain['server']} - Status: {domain['status']}")
                        print(f"   👤 User: {domain['user']} | 📧 Email: {domain['email']} | 📦 Package: {domain['package']}")
                        print(f"   📅 Created: {domain['creation_date']} | 💾 Disk: {domain['disk_used']}MB")
                        print("-" * 80)
                else:
                    print("❌ No domains found matching the search criteria")

            elif choice == "4":
                domain_statistics_report(servers)

            elif choice == "5":
                from common_functions import list_all_available_domains
                list_all_available_domains(servers)

            elif choice == "6":
                keyword = input("\n🔍 Enter keyword to search for domains: ").strip()
                if keyword:
                    from common_functions import search_domains_by_keyword
                    search_domains_by_keyword(servers, keyword)
                else:
                    print("❌ Keyword cannot be empty")

            elif choice == "7":
                domain = input("\n🧪 Enter domain to test subdomain loading: ").strip()
                if domain:
                    from common_functions import test_subdomain_loading
                    # البحث عن السيرفر أولاً
                    server, acct, server_name = find_server_by_domain(domain, servers, include_subdomains=False)
                    if server:
                        test_subdomain_loading(server, domain)
                    else:
                        print(f"❌ Domain {domain} not found on any server")
                else:
                    print("❌ Domain cannot be empty")

            elif choice == "8":
                list_server_accounts(servers)

            elif choice == "9":
                create_new_account(servers)

            elif choice == "10":
                domain = input("\n🌐 Enter domain to suspend: ").strip()
                if domain:
                    suspend_account_by_domain(domain, servers)
                else:
                    print("❌ Domain cannot be empty")

            elif choice == "11":
                domain = input("\n🌐 Enter domain to unsuspend: ").strip()
                if domain:
                    unsuspend_account_by_domain(domain, servers)
                else:
                    print("❌ Domain cannot be empty")

            elif choice == "12":
                domain = input("\n🌐 Enter domain to terminate: ").strip()
                if domain:
                    terminate_account_by_domain(domain, servers)
                else:
                    print("❌ Domain cannot be empty")

            elif choice == "13":
                domain = input("\n🌐 Enter domain to change password: ").strip()
                if domain:
                    change_cpanel_password_menu(domain, servers)
                else:
                    print("❌ Domain cannot be empty")

            elif choice == "14":
                display_server_status(servers)

            elif choice == "15":
                show_logs()

            elif choice == "16":
                length = input("🔢 Password length (default 12): ").strip() or "12"
                try:
                    length = int(length)
                    if length < 4:
                        print("❌ Password length must be at least 4")
                    else:
                        password = generate_password(length)
                        print(f"🎲 Generated password: {password}")
                except ValueError:
                    print("❌ Invalid length")

            elif choice == "17":
                domain = input("\n🌐 Enter domain to manage SSH: ").strip()
                if domain:
                    manage_ssh_menu(domain, servers)
                else:
                    print("❌ Domain cannot be empty")

            elif choice == "18":
                domain = input("\n🌐 Enter domain to manage PHP: ").strip()
                if domain:
                    manage_php_menu(domain, servers)
                else:
                    print("❌ Domain cannot be empty")

            elif choice == "19":
                bulk_ssh_management_menu(servers)

            elif choice == "20":
                bulk_php_management_menu(servers)

            elif choice == "0":
                print("👋 Goodbye!")
                logging.info("Accounts & Domains Manager closed")
                break
                
            else:
                print("❌ Invalid option")

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        logging.info("Program interrupted by user")
        sys.exit(0)
    except Exception as e:
        handle_script_error(e, "Accounts & Domains Manager")
        sys.exit(1)

if __name__ == "__main__":
    main()
