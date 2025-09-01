#!/usr/bin/env python3
# === الدوال المشتركة لجميع سكريبتات WHM ===

import requests
import json
import urllib3
from openpyxl import Workbook
import logging
import os
from datetime import datetime, timedelta
import csv
import getpass
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from fnmatch import fnmatch
import string
import secrets

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد نظام السجلات
def setup_logging(log_file='whm_control.log'):
    """إعداد نظام السجلات"""
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# === إعدادات السيرفرات ===
def load_servers_config():
    """تحميل إعدادات السيرفرات"""
    try:
        from servers_config import servers
        return servers
    except ImportError:
        print("❌ Error: servers_config.py file not found!")
        print("Please create servers_config.py with your server configuration.")
        sys.exit(1)

# === دوال WHM الأساسية ===
def whm_api_call(server, function, params=None, timeout=30):
    """استدعاء WHM API مع معالجة الأخطاء"""
    if params is None:
        params = {}
    
    try:
        BASE_URL = f"https://{server['ip']}:2087/json-api"
        HEADERS = {"Authorization": f"WHM root:{server['token']}"}
        url = f"{BASE_URL}/{function}?api.version=1"
        
        logging.info(f"Calling WHM API: {function} on {server['ip']}")
        response = requests.get(url, headers=HEADERS, params=params, verify=False, timeout=timeout)
        response.raise_for_status()
        
        result = response.json()
        
        # التحقق من وجود رسالة خطأ في الاستجابة
        if 'error' in result:
            error_msg = result['error']
            logging.error(f"API Error: {error_msg}")
            return {"error": error_msg}
        
        # التحقق من البيانات - السماح باستجابات cPanel
        if function == "cpanel":
            # استجابات cPanel قد تكون مختلفة
            return result
        elif 'data' not in result and 'metadata' not in result:
            return {"error": "Invalid response format"}
        
        # فحص حالة الاستجابة
        if 'metadata' in result:
            if result['metadata'].get('result') == 0:
                error_message = result['metadata'].get('reason', 'Unknown error')
                logging.error(f"WHM API Error: {error_message}")
                return {"error": error_message}
        
        return result
        
    except requests.exceptions.Timeout:
        logging.error(f"Timeout error connecting to {server['ip']}")
        return {"error": "Connection timeout"}
    except requests.exceptions.ConnectionError:
        logging.error(f"Connection error to {server['ip']}")
        return {"error": "Connection failed"}
    except Exception as e:
        logging.error(f"Error calling WHM API: {str(e)}")
        return {"error": str(e)}



def test_server_connection(server):
    """اختبار الاتصال بالسيرفر"""
    result = whm_api_call(server, "version")
    if "error" not in result:
        version = result.get("data", {}).get("version", "Unknown")
        logging.info(f"Server {server['ip']} is online - WHM Version: {version}")
        return True
    else:
        logging.error(f"Server {server['ip']} is offline or unreachable")
        return False

def list_accounts(server):
    """جلب قائمة الحسابات الأساسية"""
    data = whm_api_call(server, "listaccts")
    if "error" in data:
        return []
    return data.get("data", {}).get("acct", [])



def cpanel_api_call(server, user, module, function, params=None, timeout=30):
    """استدعاء cPanel API مباشرة (كما كان في السكريبت القديم)"""
    if params is None:
        params = {}
    
    try:
        BASE_URL = f"https://{server['ip']}:2087/json-api/cpanel"
        HEADERS = {"Authorization": f"WHM root:{server['token']}"}
        
        api_params = {
            "cpanel_jsonapi_user": user,
            "cpanel_jsonapi_apiversion": "3",
            "cpanel_jsonapi_module": module,
            "cpanel_jsonapi_func": function
        }
        
        # دمج المعاملات الإضافية
        api_params.update(params)
        
        logging.info(f"Calling cPanel API: {module}::{function} for user {user}")
        response = requests.get(BASE_URL, headers=HEADERS, params=api_params, verify=False, timeout=timeout)
        response.raise_for_status()
        
        result = response.json()
        return result
        
    except Exception as e:
        logging.error(f"Error calling cPanel API: {str(e)}")
        return {"error": str(e)}

def list_all_domains(server):
    """جلب جميع الدومينات (الرئيسية + الصب دومين) من السيرفر"""
    try:
        # جلب الدومينات الرئيسية
        main_domains = []
        accounts = list_accounts(server)
        for acct in accounts:
            main_domains.append({
                "domain": acct["domain"],
                "user": acct["user"],
                "type": "main",
                "server": server
            })
        
        # جلب الصب دومين باستخدام cPanel API
        subdomains = []
        try:
            # محاولة جلب الصب دومين من جميع الحسابات
            if accounts:
                print(f"      🔍 Checking subdomains for {len(accounts)} accounts...")
                for i, acct in enumerate(accounts, 1):
                    try:
                        print(f"         📋 Checking account {i}/{len(accounts)}: {acct['user']}")
                        result = cpanel_api_call(server, acct["user"], "SubDomain", "listsubdomains")
                        
                        if result and "data" in result:
                            print(f"         ✅ Found {len(result['data'])} subdomains for {acct['user']}")
                            for subdomain in result["data"]:
                                subdomains.append({
                                    "domain": subdomain["domain"],
                                    "user": acct["user"],
                                    "type": "subdomain",
                                    "server": server
                                })
                        elif result and "error" in result:
                            print(f"         ⚠️  API error for {acct['user']}: {result['error']}")
                        else:
                            print(f"         ℹ️  No subdomains found for {acct['user']}")
                    except Exception as e:
                        print(f"         ❌ Error checking {acct['user']}: {e}")
                        continue
        except Exception as e:
            print(f"      ❌ Error in subdomain loading: {e}")
        
        # محاولة استخدام WHM API كبديل لجلب الصب دومين
        if not subdomains:
            print(f"      🔍 Trying WHM API as alternative...")
            try:
                whm_result = whm_api_call(server, "get_domain_info")
                if whm_result and "data" in whm_result:
                    print(f"         📊 WHM API returned {len(whm_result['data'])} items")
                    # يمكن إضافة معالجة إضافية هنا
            except Exception as e:
                print(f"         ❌ WHM API also failed: {e}")
        
        # محاولة البحث في الدومينات الرئيسية للبحث عن الصب دومين
        if not subdomains:
            print(f"      🔍 Searching main domains for subdomain patterns...")
            for acct in accounts:
                domain = acct["domain"]
                # البحث عن أنماط الصب دومين
                if "." in domain and domain.count(".") > 1:
                    print(f"         🔍 Found potential subdomain: {domain}")
                    subdomains.append({
                        "domain": domain,
                        "user": acct["user"],
                        "type": "subdomain",
                        "server": server
                    })
        
        # محاولة جلب الصب دومين باستخدام طرق أخرى
        if not subdomains:
            print(f"      🔍 Trying alternative methods for subdomains...")
            for acct in accounts:
                try:
                    # محاولة 1: SubDomain::listsubdomains
                    result1 = cpanel_api_call(server, acct["user"], "SubDomain", "listsubdomains")
                    if result1 and "data" in result1 and result1["data"]:
                        print(f"         ✅ Method 1 (SubDomain::listsubdomains) found {len(result1['data'])} subdomains for {acct['user']}")
                        for subdomain in result1["data"]:
                            subdomains.append({
                                "domain": subdomain["domain"],
                                "user": acct["user"],
                                "type": "subdomain",
                                "server": server
                            })
                        continue
                    
                    # محاولة 2: SubDomain::list
                    result2 = cpanel_api_call(server, acct["user"], "SubDomain", "list")
                    if result2 and "data" in result2 and result2["data"]:
                        print(f"         ✅ Method 2 (SubDomain::list) found {len(result2['data'])} subdomains for {acct['user']}")
                        for subdomain in result2["data"]:
                            subdomains.append({
                                "domain": subdomain["domain"],
                                "user": acct["user"],
                                "type": "subdomain",
                                "server": server
                            })
                        continue
                    
                    # محاولة 3: Addon::listaddondomains
                    result3 = cpanel_api_call(server, acct["user"], "Addon", "listaddondomains")
                    if result3 and "data" in result3 and result3["data"]:
                        print(f"         ✅ Method 3 (Addon::listaddondomains) found {len(result3['data'])} addon domains for {acct['user']}")
                        for addon in result3["data"]:
                            subdomains.append({
                                "domain": addon["domain"],
                                "user": acct["user"],
                                "type": "addon",
                                "server": server
                            })
                        continue
                    
                    # محاولة 4: Park::listparkeddomains
                    result4 = cpanel_api_call(server, acct["user"], "Park", "listparkeddomains")
                    if result4 and "data" in result4 and result4["data"]:
                        print(f"         ✅ Method 4 (Park::listparkeddomains) found {len(result4['data'])} parked domains for {acct['user']}")
                        for parked in result4["data"]:
                            subdomains.append({
                                "domain": parked["domain"],
                                "user": acct["user"],
                                "type": "parked",
                                "server": server
                            })
                        continue
                    
                    print(f"         ℹ️  No subdomains found for {acct['user']} using any method")
                    
                except Exception as e:
                    print(f"         ❌ Error checking {acct['user']}: {e}")
                    continue
        
        # محاولة خاصة للبحث في egypetoo.com
        egypetoo_accounts = [acct for acct in accounts if "egypetoo.com" in acct["domain"]]
        if egypetoo_accounts:
            print(f"      🔍 Found egypetoo.com account, checking for subdomains...")
            for acct in egypetoo_accounts:
                print(f"         📋 Checking account: {acct['user']} ({acct['domain']})")
                try:
                    # محاولة جلب الصب دومين من egypetoo.com
                    print(f"         🔍 Trying SubDomain::listsubdomains...")
                    result = cpanel_api_call(server, acct["user"], "SubDomain", "listsubdomains")
                    print(f"         📤 API Response: {result}")
                    
                    if result and "data" in result and result["data"]:
                        print(f"         ✅ Found {len(result['data'])} subdomains in egypetoo.com:")
                        for subdomain in result["data"]:
                            print(f"            - {subdomain['domain']}")
                            subdomains.append({
                                "domain": subdomain["domain"],
                                "user": acct["user"],
                                "type": "subdomain",
                                "server": server
                            })
                    elif result and "error" in result:
                        print(f"         ⚠️  SubDomain API error: {result['error']}")
                    else:
                        print(f"         ℹ️  No subdomains found in SubDomain API")
                    
                    # محاولة جلب Addon domains
                    print(f"         🔍 Trying Addon::listaddondomains...")
                    addon_result = cpanel_api_call(server, acct["user"], "Addon", "listaddondomains")
                    print(f"         📤 Addon API Response: {addon_result}")
                    
                    if addon_result and "data" in addon_result and addon_result["data"]:
                        print(f"         ✅ Found {len(addon_result['data'])} addon domains in egypetoo.com:")
                        for addon in addon_result["data"]:
                            print(f"            - {addon['domain']}")
                            subdomains.append({
                                "domain": addon["domain"],
                                "user": acct["user"],
                                "type": "addon",
                                "server": server
                            })
                    elif addon_result and "error" in addon_result:
                        print(f"         ⚠️  Addon API error: {addon_result['error']}")
                    else:
                        print(f"         ℹ️  No addon domains found")
                    
                    # محاولة استخدام WHM API لجلب معلومات الحساب
                    print(f"         🔍 Trying WHM API for account details...")
                    whm_result = whm_api_call(server, "getacct", {"user": acct["user"]})
                    if whm_result and "data" in whm_result:
                        account_data = whm_result["data"]
                        print(f"         📊 Account details: {account_data}")
                        
                        # البحث عن الصب دومين في معلومات الحساب
                        if "subdomains" in account_data:
                            print(f"         ✅ Found subdomains in account data: {account_data['subdomains']}")
                            for subdomain in account_data["subdomains"]:
                                subdomains.append({
                                    "domain": subdomain,
                                    "user": acct["user"],
                                    "type": "subdomain",
                                    "server": server
                                })
                        
                        # البحث عن addon domains في معلومات الحساب
                        if "addondomains" in account_data:
                            print(f"         ✅ Found addon domains in account data: {account_data['addondomains']}")
                            for addon in account_data["addondomains"]:
                                subdomains.append({
                                    "domain": addon,
                                    "user": acct["user"],
                                    "type": "addon",
                                    "server": server
                                })
                    
                    # محاولة استخدام WHM API لجلب جميع الدومينات
                    print(f"         🔍 Trying WHM API for all domains...")
                    all_domains_result = whm_api_call(server, "listaccts")
                    if all_domains_result and "data" in all_domains_result:
                        all_accounts = all_domains_result["data"]["acct"]
                        for acc in all_accounts:
                            if acc["user"] == acct["user"]:
                                print(f"         📊 Account info from WHM: {acc}")
                                
                                # البحث في child_nodes
                                if "child_nodes" in acc and acc["child_nodes"]:
                                    print(f"         ✅ Found child nodes: {acc['child_nodes']}")
                                    for child in acc["child_nodes"]:
                                        if isinstance(child, dict) and "domain" in child:
                                            subdomains.append({
                                                "domain": child["domain"],
                                                "user": acct["user"],
                                                "type": "subdomain",
                                                "server": server
                                            })
                                        elif isinstance(child, str):
                                            subdomains.append({
                                                "domain": child,
                                                "user": acct["user"],
                                                "type": "subdomain",
                                                "server": server
                                            })
                                
                                # محاولة استخدام get_domain_info
                                print(f"         🔍 Trying get_domain_info for {acct['user']}...")
                                try:
                                    domain_info_result = whm_api_call(server, "get_domain_info", {"domain": acct["domain"]})
                                    if domain_info_result and "data" in domain_info_result:
                                        domain_data = domain_info_result["data"]
                                        print(f"         📊 Domain info: {domain_data}")
                                        
                                        # البحث في domains array
                                        if "domains" in domain_data and isinstance(domain_data["domains"], list):
                                            print(f"         🔍 Found {len(domain_data['domains'])} domains in domain_info")
                                            for domain_info in domain_data["domains"]:
                                                if isinstance(domain_info, dict) and "domain" in domain_info:
                                                    domain_name = domain_info["domain"]
                                                    domain_type = domain_info.get("domain_type", "unknown")
                                                    domain_user = domain_info.get("user", acct["user"])
                                                    
                                                    # تجاهل الدومين الأساسي
                                                    if domain_name != acct["domain"]:
                                                        print(f"         ✅ Found {domain_type} domain: {domain_name}")
                                                        subdomains.append({
                                                            "domain": domain_name,
                                                            "user": domain_user,
                                                            "type": domain_type,
                                                            "server": server
                                                        })
                                        
                                        # البحث عن الصب دومين في domain_info (fallback)
                                        if "subdomains" in domain_data:
                                            print(f"         ✅ Found subdomains in domain_info: {domain_data['subdomains']}")
                                            for subdomain in domain_data["subdomains"]:
                                                subdomains.append({
                                                    "domain": subdomain,
                                                    "user": acct["user"],
                                                    "type": "subdomain",
                                                    "server": server
                                                })
                                        
                                        # البحث عن addon domains في domain_info (fallback)
                                        if "addondomains" in domain_data:
                                            print(f"         ✅ Found addon domains in domain_info: {domain_data['addondomains']}")
                                            for addon in domain_data["addondomains"]:
                                                subdomains.append({
                                                    "domain": addon,
                                                    "user": acct["user"],
                                                    "type": "addon",
                                                    "server": server
                                                })
                                except Exception as e:
                                    print(f"         ❌ get_domain_info failed: {e}")
                                
                                break
                            
                except Exception as e:
                    print(f"         ❌ Error checking egypetoo.com: {e}")
        else:
            print(f"      ℹ️  No egypetoo.com account found")
        
        all_domains = main_domains + subdomains
        print(f"      📊 Found {len(main_domains)} main domains + {len(subdomains)} subdomains")
        return all_domains
        
    except Exception as e:
        logging.error(f"Error listing domains: {str(e)}")
        return []

def find_server_by_domain(domain, servers, include_subdomains=True, search_mode="smart"):
    """البحث عن السيرفر الذي يحتوي على الدومين مع خيارات بحث متقدمة"""
    print(f"🔍 Searching for domain: {domain}...")
    
    if search_mode == "fast":
        print("🚀 Using fast search...")
        return find_server_by_domain_fast(domain, servers)
    elif search_mode == "smart":
        print("🧠 Using smart search...")
        return find_server_by_domain_smart(domain, servers)
    elif search_mode == "full":
        print("🔍 Using full search...")
        return find_server_by_domain_full(domain, servers)
    else:
        print("🧠 Using smart search (default)...")
        return find_server_by_domain_smart(domain, servers)

def find_server_by_domain_fast(domain, servers):
    """البحث السريع في الدومينات الرئيسية فقط"""
    print("🔍 Searching across {} servers...".format(len(servers)))
    print("   📋 Searching main domains only (faster)...")
    
    found_servers = []
    
    for i, (name, server) in enumerate(servers.items(), 1):
        print(f"   📡 Checking Server {name} ({i}/{len(servers)})...")
        
        if test_server_connection(server):
            try:
                print(f"      🔍 Loading main domains from Server {name}...")
                accounts = list_accounts(server)
                
                for acct in accounts:
                    if acct["domain"].lower() == domain.lower():
                        print(f"      ✅ Found {domain} as main domain on Server {name}!")
                        found_servers.append((server, acct, name))
                        break
                        
            except Exception as e:
                print(f"      ⚠️  Error loading domains from Server {name}: {e}")
                continue
    
    if found_servers:
        print(f"      📊 Found {len(found_servers)} server(s) with domain: {domain}")
        
        if len(found_servers) == 1:
            server, acct, name = found_servers[0]
            print(f"      📊 Processing single server result: {name} - Status: online")
            print(f"✅ Found {domain} as main domain on Server {name}")
            print(f"   👤 cPanel user: {acct['user']}")
            print(f"      📤 Returning result: ({server}, {acct}, {name})")
            return server, acct, name
        else:
            # عرض خيارات السيرفرات
            print(f"🔍 Domain found on multiple servers:")
            for i, (server, acct, name) in enumerate(found_servers, 1):
                status = "online" if test_server_connection(server) else "offline"
                print(f"   {i}. Server {name} ({server['ip']}) - {status}")
            
            # اختيار تلقائي للسيرفر الأول
            auto_selected = found_servers[0]
            print(f"✅ Auto-selected: Server {auto_selected[2]} (option 1)")
            
            # السماح للمستخدم باختيار السيرفر
            try:
                choice = input(f"\n🌐 Choose server (1-{len(found_servers)}) or press Enter for auto-selected: ").strip()
                if choice:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(found_servers):
                        selected = found_servers[choice_idx]
                        print(f"✅ Selected: Server {selected[2]}")
                        return selected
            except (ValueError, IndexError):
                pass
            
            # استخدام الاختيار التلقائي
            print(f"✅ Using auto-selected: Server {auto_selected[2]}")
            return auto_selected
    
    print("🔍 Fast search result: None")
    return None, None, None

def find_server_by_domain_smart(domain, servers):
    """البحث الذكي: الدومينات الرئيسية أولاً، ثم الصب دومين إذا لزم الأمر"""
    # محاولة البحث السريع أولاً
    result = find_server_by_domain_fast(domain, servers)
    if result[0] is not None:
        return result
    
    # إذا لم يتم العثور عليه، البحث في الصب دومين
    print("   🔍 Main domain not found, searching subdomains...")
    return find_server_by_domain_full(domain, servers)

def find_server_by_domain_full(domain, servers):
    """البحث الكامل في جميع الدومينات والصب دومين"""
    print("🔍 Searching across {} servers...".format(len(servers)))
    print("   📋 Searching all domains + subdomains...")
    
    found_servers = []
    
    for i, (name, server) in enumerate(servers.items(), 1):
        print(f"   📡 Checking Server {name} ({i}/{len(servers)})...")
        
        if test_server_connection(server):
            try:
                print(f"      🔍 Loading all domains from Server {name}...")
                all_domains = list_all_domains(server)
                
                for domain_info in all_domains:
                    if domain_info["domain"].lower() == domain.lower():
                        print(f"      ✅ Found {domain} as {domain_info['type']} domain on Server {name}!")
                        found_servers.append((server, domain_info, name))
                        break
                        
            except Exception as e:
                print(f"      ⚠️  Error loading domains from Server {name}: {e}")
                continue
    
    if found_servers:
        print(f"      📊 Found {len(found_servers)} server(s) with domain: {domain}")
        
        if len(found_servers) == 1:
            server, domain_info, name = found_servers[0]
            print(f"      📊 Processing single server result: {name} - Status: online")
            print(f"✅ Found {domain} as {domain_info['type']} domain on Server {name}")
            print(f"   👤 cPanel user: {domain_info['user']}")
            return server, domain_info, name
        else:
            # عرض خيارات السيرفرات
            print(f"🔍 Domain found on multiple servers:")
            for i, (server, domain_info, name) in enumerate(found_servers, 1):
                status = "online" if test_server_connection(server) else "offline"
                print(f"   {i}. Server {name} ({s['ip']}) - {status}")
            
            # اختيار تلقائي للسيرفر الأول
            auto_selected = found_servers[0]
            print(f"✅ Auto-selected: Server {auto_selected[2]} (option 1)")
            
            # السماح للمستخدم باختيار السيرفر
            try:
                choice = input(f"\n🌐 Choose server (1-{len(found_servers)}) or press Enter for auto-selected: ").strip()
                if choice:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(found_servers):
                        selected = found_servers[choice_idx]
                        print(f"✅ Selected: Server {selected[2]}")
                        return selected
            except (ValueError, IndexError):
                pass
            
            # استخدام الاختيار التلقائي
            print(f"✅ Using auto-selected: Server {auto_selected[2]}")
            return auto_selected
    
    print("❌ Domain not found on any server!")
    return None, None, None

def find_server_by_email(email_address, servers):
    """البحث عن الإيميل في جميع السيرفرات"""
    print("🔍 Searching for email across {} servers...".format(len(servers)))
    print("   📧 Searching for email: {}".format(email_address))
    
    found_servers = []
    
    for i, (name, server) in enumerate(servers.items(), 1):
        print(f"   📡 Checking Server {name} ({i}/{len(servers)})...")
        
        if test_server_connection(server):
            try:
                print(f"      🔍 Loading accounts from Server {name}...")
                accounts = list_accounts(server)
                
                for acct in accounts:
                    if acct["domain"].lower() == email_address.split("@")[1].lower():
                        print(f"      ✅ Found domain {acct['domain']} on Server {name}!")
                        
                        # البحث عن الإيميل في هذا الحساب
                        print(f"      🔍 Checking email accounts in {acct['user']}...")
                        try:
                            emails = list_email_accounts(server, acct['user'], acct['domain'])
                            for email in emails:
                                if email.get("email", "").lower() == email_address.lower():
                                    print(f"      🎯 Found email {email_address} on Server {name}!")
                                    found_servers.append((server, acct, name))
                                    break
                        except Exception as e:
                            print(f"      ⚠️  Error checking emails: {e}")
                            continue
                        
                        if found_servers:
                            break
                        
            except Exception as e:
                print(f"      ⚠️  Error loading accounts from Server {name}: {e}")
                continue
    
    if found_servers:
        print(f"      📊 Found {len(found_servers)} server(s) with email: {email_address}")
        
        if len(found_servers) == 1:
            server, acct, name = found_servers[0]
            print(f"      📊 Processing single server result: {name} - Status: online")
            print(f"✅ Found email {email_address} on Server {name}")
            print(f"   👤 cPanel user: {acct['user']}")
            return server, acct, name
        else:
            # عرض خيارات السيرفرات
            print(f"🔍 Email found on multiple servers:")
            for i, (server, acct, name) in enumerate(found_servers, 1):
                status = "online" if test_server_connection(server) else "offline"
                print(f"   {i}. Server {name} ({server['ip']}) - {status}")
            
            # اختيار تلقائي للسيرفر الأول
            auto_selected = found_servers[0]
            print(f"✅ Auto-selected: Server {auto_selected[2]} (option 1)")
            
            # السماح للمستخدم باختيار السيرفر
            try:
                choice = input(f"\n🌐 Choose server (1-{len(found_servers)}) or press Enter for auto-selected: ").strip()
                if choice:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(found_servers):
                        selected = found_servers[choice_idx]
                        print(f"✅ Selected: Server {selected[2]}")
                        return selected
            except (ValueError, IndexError):
                pass
            
            # استخدام الاختيار التلقائي
            print(f"✅ Using auto-selected: Server {auto_selected[2]}")
            return auto_selected
    
    print("❌ Email not found on any server!")
    return None, None, None

def get_online_servers(servers):
    """الحصول على السيرفرات المتصلة"""
    online_servers = {}
    for name, server in servers.items():
        if test_server_connection(server):
            online_servers[name] = server
    
    if not online_servers:
        print("❌ No online servers available!")
        return {}
    
    return online_servers

def display_server_status(servers):
    """عرض حالة جميع السيرفرات"""
    print("\n🔍 Server Status Check:")
    print("-" * 50)
    for name, server in servers.items():
        status = "🟢 Online" if test_server_connection(server) else "🔴 Offline"
        print(f"Server {name} ({server['ip']}): {status}")

def list_all_available_domains(servers):
    """عرض جميع الدومينات المتاحة (أساسية + subdomains)"""
    print("\n🌐 All Available Domains:")
    print("=" * 80)
    
    total_domains = 0
    total_subdomains = 0
    
    for name, server in servers.items():
        if test_server_connection(server):
            print(f"\n🖥️  Server {name} ({server['ip']}):")
            print("-" * 60)
            
            try:
                all_domains = list_all_domains(server)
                
                if not all_domains:
                    print("   ⚠️  No domains found or error loading domains")
                    continue
                
                # فصل الدومينات الأساسية عن الـ subdomains
                main_domains = [d for d in all_domains if d["type"] == "main_domain"]
                subdomains = [d for d in all_domains if d["type"] == "subdomain"]
                
                # عرض الدومينات الأساسية
                if main_domains:
                    print(f"   📌 Main Domains ({len(main_domains)}):")
                    for i, domain_info in enumerate(main_domains, 1):
                        print(f"      {i}. {domain_info['domain']} (User: {domain_info['user']})")
                        total_domains += 1
                
                # عرض الـ subdomains
                if subdomains:
                    print(f"   🔗 Subdomains ({len(subdomains)}):")
                    for i, domain_info in enumerate(subdomains, 1):
                        parent = domain_info['parent_domain']
                        sub = domain_info['subdomain_name']
                        print(f"      {i}. {sub}.{parent} (User: {domain_info['user']})")
                        total_subdomains += 1
                
                if not main_domains and not subdomains:
                    print("   ⚠️  No domains found on this server")
                    
            except Exception as e:
                print(f"   ❌ Error loading domains: {e}")
        else:
            print(f"\n🖥️  Server {name} ({server['ip']}): 🔴 Offline")
    
    print(f"\n📊 Summary:")
    print(f"   🌐 Total Main Domains: {total_domains}")
    print(f"   🔗 Total Subdomains: {total_subdomains}")
    print(f"   📈 Total Domains: {total_domains + total_subdomains}")

def search_domains_by_keyword(servers, keyword):
    """البحث عن دومينات تحتوي على كلمة معينة"""
    print(f"\n🔍 Searching for domains containing: '{keyword}'")
    print("=" * 80)
    
    found_domains = []
    
    for name, server in servers.items():
        if test_server_connection(server):
            try:
                all_domains = list_all_domains(server)
                
                for domain_info in all_domains:
                    if keyword.lower() in domain_info["domain"].lower():
                        found_domains.append({
                            "server": name,
                            "server_ip": server["ip"],
                            "domain": domain_info["domain"],
                            "user": domain_info["user"],
                            "type": domain_info["type"],
                            "parent_domain": domain_info.get("parent_domain", ""),
                            "subdomain_name": domain_info.get("subdomain_name", "")
                        })
                        
            except Exception as e:
                print(f"⚠️  Error searching Server {name}: {e}")
    
    if not found_domains:
        print(f"❌ No domains found containing '{keyword}'")
        return
    
    print(f"✅ Found {len(found_domains)} matching domains:")
    print("-" * 80)
    
    for i, domain_info in enumerate(found_domains, 1):
        domain_type = domain_info["type"]
        if domain_type == "subdomain":
            print(f"{i}. {domain_info['domain']} (Subdomain)")
            print(f"   📍 Parent: {domain_info['parent_domain']}")
        else:
            print(f"{i}. {domain_info['domain']} (Main Domain)")
        
        print(f"   🖥️  Server: {domain_info['server']} ({domain_info['server_ip']})")
        print(f"   👤 User: {domain_info['user']}")
        print()

# === دوال مساعدة ===
def confirm_action(message):
    """تأكيد العملية"""
    response = input(f"{message} (y/N): ").lower()
    return response == 'y' or response == 'yes'

def generate_password(length=12):
    """توليد كلمة مرور عشوائية وقوية"""
    import random
    import string
    
    # تحديد مجموعات الأحرف
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*"
    
    # التأكد من وجود حرف واحد على الأقل من كل نوع
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special)
    ]
    
    # إكمال باقي كلمة المرور
    remaining_length = length - len(password)
    all_characters = lowercase + uppercase + digits + special
    password.extend(random.choice(all_characters) for _ in range(remaining_length))
    
    # خلط الأحرف
    random.shuffle(password)
    return ''.join(password)

def generate_strong_password(length=16):
    """توليد باسورد قوي عشوائي"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # شرط أساسي: لازم يحتوي على حرف كبير، صغير، رقم، ورمز
        if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in string.punctuation for c in password)):
            return password

def get_secure_password():
    """الحصول على كلمة مرور بشكل آمن"""
    return getpass.getpass("Enter password: ")

def show_logs(log_file='whm_control.log'):
    """عرض سجلات العمليات"""
    if os.path.exists(log_file):
        print("\n📜 Recent Operation Logs:")
        print("-" * 50)
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-20:]:  # عرض آخر 20 سطر
                    print(line.strip())
        except Exception as e:
            print(f"❌ Error reading log file: {str(e)}")
    else:
        print("❌ No log file found")

# === دوال التصدير ===
def export_to_excel(data, headers, filename_prefix, sheet_name="Data"):
    """تصدير البيانات إلى Excel"""
    try:
        # إنشاء مجلد reports إذا لم يكن موجوداً
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        # تنظيف اسم الـ sheet (إزالة الرموز غير المسموحة)
        clean_sheet_name = "".join(c for c in sheet_name if c not in ':*?/\\[]')
        # تقصير الاسم إذا كان طويلاً (Excel يقبل 31 حرف فقط)
        if len(clean_sheet_name) > 31:
            clean_sheet_name = clean_sheet_name[:31]
        
        wb = Workbook()
        ws = wb.active
        ws.title = clean_sheet_name
        
        # إضافة العناوين
        ws.append(headers)
        
        # تنسيق العناوين
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
        
        # إضافة البيانات
        for row in data:
            ws.append(row)
        
        # إنشاء اسم الملف في مجلد reports
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.xlsx"
        filepath = os.path.join(reports_dir, filename)
        
        wb.save(filepath)
        print(f"✅ Excel file saved as: reports/{filename}")
        logging.info(f"Data exported to Excel: reports/{filename}")
        return filepath
        
    except Exception as e:
        logging.error(f"Error exporting to Excel: {str(e)}")
        print(f"❌ Error exporting to Excel: {str(e)}")
        return None

def export_to_csv(data, headers, filename_prefix):
    """تصدير البيانات إلى CSV"""
    try:
        # إنشاء مجلد reports إذا لم يكن موجوداً
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for row in data:
                writer.writerow(row)
        
        print(f"✅ CSV file saved as: reports/{filename}")
        logging.info(f"Data exported to CSV: reports/{filename}")
        return filepath
        
    except Exception as e:
        logging.error(f"Error exporting to CSV: {str(e)}")
        print(f"❌ Error exporting to CSV: {str(e)}")
        return None

# === دالة تهيئة السكريبت ===
def initialize_script(script_name):
    """تهيئة السكريبت مع إعداد السجلات وتحميل السيرفرات"""
    print(f"🚀 {script_name}")
    print("=" * 60)
    
    # إعداد السجلات
    setup_logging()
    
    # تحميل إعدادات السيرفرات
    servers = load_servers_config()
    
    # فحص الاتصال عند البدء
    display_server_status(servers)
    
    return servers

# === دوال فحص الصحة ===
def check_basic_health(server, server_name):
    """فحص الصحة الأساسي للسيرفر"""
    print(f"\n🔧 Basic Health Check - {server_name}")
    print("=" * 50)
    
    health_score = 0
    max_score = 3
    
    # فحص الاتصال
    if test_server_connection(server):
        print("✅ Server connection: OK")
        health_score += 1
    else:
        print("❌ Server connection: Failed")
        return {"score": 0, "status": "OFFLINE"}
    
    # فحص الحسابات
    try:
        accounts = list_accounts(server)
        if accounts:
            print(f"✅ Accounts accessible: {len(accounts)} accounts found")
            health_score += 1
        else:
            print("⚠️  No accounts found")
    except:
        print("❌ Error accessing accounts")
    
    # فحص خدمة WHM
    try:
        version_result = whm_api_call(server, "version")
        if "error" not in version_result:
            version = version_result.get("data", {}).get("version", "Unknown")
            print(f"✅ WHM service: Running (Version: {version})")
            health_score += 1
        else:
            print("❌ WHM service: Error")
    except:
        print("❌ WHM service: Exception")
    
    # تحديد الحالة العامة
    percentage = (health_score / max_score) * 100
    
    if percentage >= 100:
        status = "EXCELLENT"
        indicator = "🟢"
    elif percentage >= 66:
        status = "GOOD"
        indicator = "🟡"
    elif percentage >= 33:
        status = "FAIR"
        indicator = "🟠"
    else:
        status = "POOR"
        indicator = "🔴"
    
    print(f"\n{indicator} Overall Health: {status} ({health_score}/{max_score})")
    
    return {
        "score": health_score,
        "max_score": max_score,
        "percentage": percentage,
        "status": status,
        "indicator": indicator
    }

# === معالج الأخطاء العام ===
def handle_script_error(e, script_name):
    """معالجة أخطاء السكريبت"""
    error_msg = f"Error in {script_name}: {str(e)}"
    print(f"\n❌ {error_msg}")
    logging.error(error_msg)
    
    print(f"\n💡 Troubleshooting:")
    print("1. Check server connectivity")
    print("2. Verify WHM credentials")
    print("3. Check servers_config.py file")
    print("4. Review log files for details")

# === دوال إدارة الإيميل ===
def list_email_accounts(server, cpanel_user, domain=None):
    """جلب قائمة الإيميلات مع معالجة أفضل للبيانات والأخطاء"""
    try:
        params = {"include_disk_usage": 1}  # طلب معلومات الديسك
        if domain:
            params["domain"] = domain
            
        result = cpanel_api_call(server, cpanel_user, "Email", "list_pops", params)
        
        if "error" in result:
            logging.error(f"Error fetching email accounts for {cpanel_user}: {result['error']}")
            return []
            
        # استخراج البيانات من الاستجابة
        if "result" in result and "data" in result["result"]:
            emails = result["result"]["data"]
            
            # التحقق من نوع البيانات وتنظيفها
            if isinstance(emails, list):
                # تنظيف وتنسيق البيانات
                cleaned_emails = []
                for email in emails:
                    if isinstance(email, dict):
                        # إضافة معلومات إضافية وتنظيف البيانات
                        # معالجة أفضل للبيانات الرقمية
                        try:
                            diskused = email.get("diskused", 0)
                            diskquota = email.get("diskquota", 0)
                            
                            # تحويل إلى أرقام مع معالجة الأخطاء
                            diskused = float(diskused) if diskused and str(diskused).replace('.', '').replace('-', '').isdigit() else 0
                            diskquota = float(diskquota) if diskquota and str(diskquota).replace('.', '').replace('-', '').isdigit() else 0
                            
                            # إذا كانت الحصة 0، استخدم القيمة الافتراضية
                            if diskquota == 0:
                                diskquota = 1024 * 1024 * 1024  # 1GB بالبايت (Unlimited)
                                
                        except (ValueError, TypeError):
                            diskused = 0
                            diskquota = 1024 * 1024 * 1024  # 1GB بالبايت (Unlimited)
                        
                        cleaned_email = {
                            "email": email.get("email", "").strip(),
                            "domain": email.get("domain", domain),
                            "user": email.get("user", ""),
                            "diskused": diskused,
                            "diskquota": diskquota,
                            "suspended": bool(email.get("suspended", 0)),
                            "login": f"{email.get('user', '')}@{email.get('domain', domain)}"
                        }
                        
                        # إضافة فقط إذا كان الإيميل صالحاً
                        if cleaned_email["email"] and "@" in cleaned_email["email"]:
                            cleaned_emails.append(cleaned_email)
                            
                return cleaned_emails
            else:
                logging.warning(f"Unexpected data format for {cpanel_user}'s emails")
                return []
        
        logging.warning(f"No email data found for {cpanel_user}")
        return []
        
    except Exception as e:
        logging.error(f"Error listing email accounts for {cpanel_user}: {str(e)}")
        return []


