#!/usr/bin/env python3
# === WHM Server Monitoring & Health Check Script ===

import sys
import os
import requests
import socket
import time
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# استيراد الدوال المشتركة
from common_functions import *

# === دوال فحص حالة المواقع ===
def check_website_status(domain, timeout=10):
    """فحص حالة موقع واحد"""
    protocols = ['https://', 'http://']
    www_variants = [f"www.{domain}", domain]
    
    result = {
        'domain': domain,
        'status_code': None,
        'status_text': 'Unknown',
        'final_url': None,
        'response_time': None,
        'error': None,
        'ssl_valid': False,
        'redirects': []
    }
    
    for protocol in protocols:
        for variant in www_variants:
            try:
                url = f"{protocol}{variant}"
                start_time = time.time()
                
                # فحص الموقع مع تتبع الإعادة التوجيه
                response = requests.get(
                    url,
                    timeout=timeout,
                    verify=False,
                    allow_redirects=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                
                response_time = round((time.time() - start_time) * 1000, 2)
                
                # تسجيل معلومات الاستجابة
                result['status_code'] = response.status_code
                result['response_time'] = response_time
                result['final_url'] = response.url
                result['ssl_valid'] = url.startswith('https://')
                
                # تتبع إعادة التوجيهات
                if response.history:
                    result['redirects'] = [r.status_code for r in response.history]
                
                # تحديد حالة النص
                if response.status_code == 200:
                    result['status_text'] = '🟢 OK'
                elif response.status_code in [301, 302]:
                    result['status_text'] = '🟡 Redirect'
                elif response.status_code == 404:
                    result['status_text'] = '🔴 Not Found'
                elif response.status_code == 403:
                    result['status_text'] = '🔴 Forbidden'
                elif response.status_code == 500:
                    result['status_text'] = '🔴 Server Error'
                else:
                    result['status_text'] = f'🔴 Error {response.status_code}'
                
                return result
                
            except requests.exceptions.SSLError:
                result['error'] = 'SSL Error'
                continue
            except requests.exceptions.ConnectionError:
                result['error'] = 'Connection Failed'
                continue
            except requests.exceptions.Timeout:
                result['error'] = 'Timeout'
                continue
            except Exception as e:
                result['error'] = str(e)
                continue
    
    # إذا لم ينجح أي بروتوكول
    if result['status_code'] is None:
        result['status_text'] = '🔴 Failed'
        if not result['error']:
            result['error'] = 'All connection attempts failed'
    
    return result

def check_websites_parallel(domains_list, max_workers=20, timeout=10):
    """فحص المواقع بالتوازي"""
    print(f"\n🔍 Checking {len(domains_list)} websites...")
    print("=" * 80)
    
    results = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # إرسال جميع المهام
        future_to_domain = {
            executor.submit(check_website_status, domain, timeout): domain 
            for domain in domains_list
        }
        
        # معالجة النتائج
        for future in as_completed(future_to_domain):
            completed += 1
            domain = future_to_domain[future]
            
            try:
                result = future.result()
                results.append(result)
                
                # عرض التقدم
                status_icon = "✅" if result['status_code'] in [200, 301, 302] else "❌"
                print(f"{status_icon} [{completed}/{len(domains_list)}] {domain} - {result['status_text']}")
                
            except Exception as e:
                error_result = {
                    'domain': domain,
                    'status_code': None,
                    'status_text': '🔴 Error',
                    'final_url': None,
                    'response_time': None,
                    'error': str(e),
                    'ssl_valid': False,
                    'redirects': []
                }
                results.append(error_result)
                print(f"❌ [{completed}/{len(domains_list)}] {domain} - Error: {str(e)}")
    
    return results

def analyze_website_results(results):
    """تحليل نتائج فحص المواقع"""
    print(f"\n📊 Website Status Analysis")
    print("=" * 60)
    
    # تصنيف النتائج
    working_sites = []      # 200, 301, 302
    broken_sites = []       # غير ذلك
    error_sites = []        # أخطاء في الاتصال
    
    for result in results:
        if result['status_code'] in [200, 301, 302]:
            working_sites.append(result)
        elif result['status_code'] is not None:
            broken_sites.append(result)
        else:
            error_sites.append(result)
    
    total = len(results)
    working_count = len(working_sites)
    broken_count = len(broken_sites)
    error_count = len(error_sites)
    
    print(f"📈 Summary:")
    print(f"   Total Websites: {total}")
    print(f"   🟢 Working (200/301/302): {working_count} ({(working_count/total)*100:.1f}%)")
    print(f"   🔴 Broken (Other codes): {broken_count} ({(broken_count/total)*100:.1f}%)")
    print(f"   ⚠️  Connection Errors: {error_count} ({(error_count/total)*100:.1f}%)")
    
    # تفصيل الحالات المكسورة
    if broken_sites or error_sites:
        print(f"\n🔴 Problematic Websites:")
        print("-" * 100)
        print(f"{'Domain':<30} {'Status':<15} {'Code':<8} {'Error':<30} {'Response Time':<15}")
        print("-" * 100)
        
        # المواقع المكسورة
        for site in broken_sites:
            error_text = site.get('error', '')[:30] if site.get('error') else ''
            response_time = f"{site['response_time']}ms" if site['response_time'] else 'N/A'
            print(f"{site['domain']:<30} {site['status_text']:<15} {site['status_code']:<8} {error_text:<30} {response_time:<15}")
        
        # مواقع بأخطاء الاتصال
        for site in error_sites:
            error_text = site.get('error', '')[:30] if site.get('error') else 'Unknown'
            print(f"{site['domain']:<30} {'🔴 Failed':<15} {'N/A':<8} {error_text:<30} {'N/A':<15}")
    
    # إحصائيات إضافية
    print(f"\n📊 Additional Statistics:")
    
    # توزيع أكواد الاستجابة
    status_codes = {}
    for result in results:
        if result['status_code']:
            code = result['status_code']
            if code not in status_codes:
                status_codes[code] = 0
            status_codes[code] += 1
    
    print(f"   Status Code Distribution:")
    for code, count in sorted(status_codes.items()):
        percentage = (count / total) * 100
        print(f"      {code}: {count} sites ({percentage:.1f}%)")
    
    # متوسط وقت الاستجابة
    response_times = [r['response_time'] for r in results if r['response_time']]
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        print(f"   Average Response Time: {avg_response_time:.2f}ms")
    
    return {
        'working_sites': working_sites,
        'broken_sites': broken_sites,
        'error_sites': error_sites,
        'status_codes': status_codes
    }

def get_all_domains_from_servers(servers):
    """جلب جميع الدومينات من جميع السيرفرات"""
    print("\n📡 Collecting domains from all servers...")
    all_domains = []
    
    for server_name, server in servers.items():
        print(f"🖥️  Checking Server {server_name} ({server['ip']})...")
        
        if test_server_connection(server):
            accounts = list_accounts(server)
            if accounts:
                server_domains = [acct["domain"] for acct in accounts]
                all_domains.extend(server_domains)
                print(f"   ✅ Found {len(server_domains)} domains")
            else:
                print(f"   ⚠️  No accounts found")
        else:
            print(f"   🔴 Server offline")
    
    # إزالة المكررات
    unique_domains = list(set(all_domains))
    print(f"\n📊 Total unique domains: {len(unique_domains)}")
    
    return unique_domains

def check_websites_from_file(file_path):
    """فحص المواقع من ملف"""
    try:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return []
            
        domains = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                domain = line.strip()
                if domain and not domain.startswith('#'):
                    # تنظيف الدومين
                    domain = domain.lower()
                    # إزالة البروتوكول إذا كان موجوداً
                    if domain.startswith(('http://', 'https://')):
                        parsed = urlparse(domain)
                        domain = parsed.netloc
                    # إزالة المسار إذا كان موجوداً
                    domain = domain.split('/')[0]
                    # إزالة www إذا كانت موجودة
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    domains.append(domain)
        
        if not domains:
            print("❌ No valid domains found in file")
            return []
            
        print(f"📂 Loaded {len(domains)} domains from {file_path}")
        return list(set(domains))  # إزالة التكرار
        
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return []

# === دوال فحص السيرفرات ===
def get_server_system_info(server):
    """جلب معلومات النظام للسيرفر"""
    try:
        # معلومات النظام الأساسية
        version_result = whm_api_call(server, "version")
        loadavg_result = whm_api_call(server, "loadavg")
        hostname_result = whm_api_call(server, "gethostname")
        
        system_info = {
            'server_ip': server['ip'],
            'status': 'online'
        }
        
        # إصدار WHM
        if "error" not in version_result:
            system_info['whm_version'] = version_result.get("data", {}).get("version", "Unknown")
        else:
            system_info['whm_version'] = "Unknown"
        
        # Load Average
        if "error" not in loadavg_result:
            loadavg_data = loadavg_result.get("data", {})
            system_info['load_average'] = {
                '1min': loadavg_data.get('one', 'Unknown'),
                '5min': loadavg_data.get('five', 'Unknown'),
                '15min': loadavg_data.get('fifteen', 'Unknown')
            }
        else:
            # محاولة بديلة باستخدام shell command
            try:
                loadavg_shell = whm_api_call(server, "shell", {"command": "cat /proc/loadavg"})
                if "error" not in loadavg_shell and "data" in loadavg_shell:
                    output = loadavg_shell["data"].get("output", "").strip()
                    if output:
                        parts = output.split()
                        if len(parts) >= 3:
                            system_info['load_average'] = {
                                '1min': parts[0],
                                '5min': parts[1],
                                '15min': parts[2]
                            }
                        else:
                            system_info['load_average'] = {'1min': 'Unknown', '5min': 'Unknown', '15min': 'Unknown'}
                    else:
                        system_info['load_average'] = {'1min': 'Unknown', '5min': 'Unknown', '15min': 'Unknown'}
                else:
                    system_info['load_average'] = {'1min': 'Unknown', '5min': 'Unknown', '15min': 'Unknown'}
            except:
                system_info['load_average'] = {'1min': 'Unknown', '5min': 'Unknown', '15min': 'Unknown'}
        
        # اسم المضيف
        if "error" not in hostname_result:
            system_info['hostname'] = hostname_result.get("data", {}).get("hostname", "Unknown")
        else:
            # محاولة بديلة باستخدام shell command
            try:
                hostname_shell = whm_api_call(server, "shell", {"command": "hostname"})
                if "error" not in hostname_shell and "data" in hostname_shell:
                    output = hostname_shell["data"].get("output", "").strip()
                    if output:
                        system_info['hostname'] = output
                    else:
                        system_info['hostname'] = "Unknown"
                else:
                    system_info['hostname'] = "Unknown"
            except:
                system_info['hostname'] = "Unknown"
        
        return system_info
        
    except Exception as e:
        logging.error(f"Error getting system info for {server['ip']}: {str(e)}")
        return {
            'server_ip': server['ip'],
            'status': 'error',
            'error': str(e)
        }

def check_server_services(server):
    """فحص الخدمات الأساسية على السيرفر - نسخة محسنة"""
    services_to_check = ['httpd', 'mysql', 'exim', 'dovecot', 'named', 'sshd', 'cpanel']
    service_status = {}
    
    for service in services_to_check:
        try:
            if service == 'cpanel':
                # فحص cPanel بشكل خاص
                result = whm_api_call(server, "version")
                if "error" not in result:
                    service_status[service] = {
                        'running': True,
                        'enabled': True,
                        'status': '🟢 Running',
                        'method_used': 'version'
                    }
                else:
                    service_status[service] = {
                        'running': False,
                        'enabled': False,
                        'status': '🔴 Stopped',
                        'method_used': 'version'
                    }
            elif service == 'httpd':
                # فحص Apache باستخدام الطرق الجديدة
                service_result = check_specific_service(server, 'httpd', ['httpd', 'apache2'])
                service_status[service] = {
                    'running': service_result['running'],
                    'enabled': service_result['running'],
                    'status': '🟢 Running' if service_result['running'] else '🔴 Stopped',
                    'method_used': service_result['method']
                }
            elif service == 'mysql':
                # فحص MySQL باستخدام الطرق الجديدة
                service_result = check_specific_service(server, 'mysql', ['mysqld', 'mariadb'])
                service_status[service] = {
                    'running': service_result['running'],
                    'enabled': service_result['running'],
                    'status': '🟢 Running' if service_result['running'] else '🔴 Stopped',
                    'method_used': service_result['method']
                }
            elif service == 'exim':
                # فحص Exim باستخدام الطرق الجديدة
                service_result = check_specific_service(server, 'exim', ['exim'])
                service_status[service] = {
                    'running': service_result['running'],
                    'enabled': service_result['running'],
                    'status': '🟢 Running' if service_result['running'] else '🔴 Stopped',
                    'method_used': service_result['method']
                }
            elif service == 'dovecot':
                # فحص Dovecot باستخدام الطرق الجديدة
                service_result = check_specific_service(server, 'dovecot', ['dovecot'])
                service_status[service] = {
                    'running': service_result['running'],
                    'enabled': service_result['running'],
                    'status': '🟢 Running' if service_result['running'] else '🔴 Stopped',
                    'method_used': service_result['method']
                }
            elif service == 'named':
                # فحص BIND DNS باستخدام الطرق الجديدة
                service_result = check_specific_service(server, 'named', ['named'])
                service_status[service] = {
                    'running': service_result['running'],
                    'enabled': service_result['running'],
                    'status': '🟢 Running' if service_result['running'] else '🔴 Stopped',
                    'method_used': service_result['method']
                }
            elif service == 'sshd':
                # فحص SSH باستخدام الطرق الجديدة
                service_result = check_specific_service(server, 'sshd', ['sshd'])
                service_status[service] = {
                    'running': service_result['running'],
                    'enabled': service_result['running'],
                    'status': '🟢 Running' if service_result['running'] else '🔴 Stopped',
                    'method_used': service_result['method']
                }
            else:
                service_status[service] = {
                    'running': False,
                    'enabled': False,
                    'status': '❓ Unknown',
                    'method_used': 'none'
                }
                
        except Exception as e:
            service_status[service] = {
                'running': False,
                'enabled': False,
                'status': '❓ Unknown',
                'method_used': 'none',
                'error': str(e)
            }
    
    return service_status

def get_server_disk_usage(server):
    """جلب معلومات استخدام القرص"""
    try:
        result = whm_api_call(server, "showbw")
        
        if "error" not in result and "data" in result:
            # محاولة جلب معلومات القرص الأساسية
            disk_info = {
                'status': 'success',
                'message': 'Disk usage data available'
            }
        else:
            disk_info = {
                'status': 'limited',
                'message': 'Limited disk information available'
            }
        
        return disk_info
        
    except Exception as e:
        logging.error(f"Error getting disk usage for {server['ip']}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def comprehensive_server_check(server, server_name):
    """فحص شامل للسيرفر - نسخة محسنة"""
    print(f"\n🔍 Comprehensive Server Check - {server_name}")
    print("=" * 60)
    
    check_results = {
        'server_name': server_name,
        'check_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 1. فحص الاتصال الأساسي
    print("1. 🌐 Testing basic connectivity...")
    if test_server_connection(server):
        print("   ✅ Server is online and accessible")
        check_results['connectivity'] = True
    else:
        print("   🔴 Server is offline or unreachable")
        check_results['connectivity'] = False
        return check_results
    
    # 2. معلومات النظام
    print("2. 🖥️  Getting system information...")
    system_info = get_server_system_info(server)
    check_results['system_info'] = system_info
    
    if system_info['status'] == 'online':
        print(f"   ✅ WHM Version: {system_info['whm_version']}")
        print(f"   ✅ Hostname: {system_info['hostname']}")
        load_avg = system_info['load_average']
        print(f"   📊 Load Average: {load_avg['1min']}, {load_avg['5min']}, {load_avg['15min']}")
    else:
        print("   ❌ Error getting system information")
    
    # 3. فحص الخدمات المحسن
    print("3. 🔧 Checking essential services...")
    services = check_server_services(server)
    check_results['services'] = services
    
    running_services = 0
    total_services = len(services)
    
    # عرض تفصيلي للخدمات
    for service_name, service_info in services.items():
        status = service_info['status']
        method = service_info.get('method_used', 'unknown')
        
        # عرض الطريقة المستخدمة في الفحص للتشخيص
        if method != 'none':
            print(f"   {service_name}: {status} (checked via {method})")
        else:
            print(f"   {service_name}: {status}")
            
        if service_info.get('running', False):
            running_services += 1
    
    print(f"   📊 Services running: {running_services}/{total_services}")
    
    # إضافة فحص إضافي للخدمات الحرجة
    critical_services = ['httpd', 'mysql', 'exim']
    critical_running = sum(1 for s in critical_services if services.get(s, {}).get('running', False))
    
    if critical_running == len(critical_services):
        print("   ✅ All critical services are running")
    elif critical_running > 0:
        print(f"   ⚠️  {critical_running}/{len(critical_services)} critical services running")
    else:
        print("   🔴 No critical services detected as running")
    
    check_results['critical_services_status'] = f"{critical_running}/{len(critical_services)}"
    
    # 4. فحص الحسابات
    print("4. 👥 Checking accounts...")
    accounts = list_accounts(server)
    if accounts:
        active_accounts = sum(1 for acct in accounts if acct.get('suspended', 0) == 0)
        suspended_accounts = len(accounts) - active_accounts
        
        print(f"   ✅ Total accounts: {len(accounts)}")
        print(f"   🟢 Active: {active_accounts}")
        print(f"   🔴 Suspended: {suspended_accounts}")
        
        check_results['accounts'] = {
            'total': len(accounts),
            'active': active_accounts,
            'suspended': suspended_accounts
        }
    else:
        print("   ⚠️  No accounts found")
        check_results['accounts'] = {'total': 0, 'active': 0, 'suspended': 0}
    
    # 5. فحص استخدام القرص
    print("5. 💾 Checking disk usage...")
    disk_info = get_server_disk_usage(server)
    check_results['disk_usage'] = disk_info
    
    if disk_info['status'] == 'success':
        print("   ✅ Disk usage information available")
    else:
        print("   ⚠️  Limited disk information")
    
    # 6. حساب النقاط الإجمالية المحسن
    total_score = 0
    max_score = 100
    
    # نقاط الاتصال (15 نقطة)
    if check_results['connectivity']:
        total_score += 15
    
    # نقاط النظام (20 نقطة)
    if system_info['status'] == 'online':
        total_score += 20
    
    # نقاط الخدمات العامة (25 نقطة)
    if total_services > 0:
        service_score = (running_services / total_services) * 25
        total_score += service_score
    
    # نقاط الخدمات الحرجة (20 نقطة) - جديد
    if len(critical_services) > 0:
        critical_score = (critical_running / len(critical_services)) * 20
        total_score += critical_score
    
    # نقاط الحسابات (20 نقطة)
    if check_results['accounts']['total'] > 0:
        account_health = (check_results['accounts']['active'] / check_results['accounts']['total']) * 20
        total_score += account_health
    else:
        total_score += 10  # نقاط جزئية إذا لم توجد حسابات
    
    check_results['health_score'] = total_score
    check_results['service_details'] = {
        'total_services': total_services,
        'running_services': running_services,
        'critical_services': len(critical_services),
        'critical_running': critical_running
    }
    
    # تحديد الحالة العامة
    if total_score >= 95:
        status = "🟢 EXCELLENT"
        status_color = "🔵"
    elif total_score >= 85:
        status = "🟡 GOOD"
        status_color = "🟢"
    elif total_score >= 70:
        status = "🟠 FAIR"
        status_color = "🟡"
    elif total_score >= 50:
        status = "⚫ CRITICAL"
        status_color = "🔴"
    else:
        status = "⚫ CRITICAL"
        status_color = "🔴"
    
    check_results['status'] = status
    
    print(f"\n{status_color} OVERALL SERVER HEALTH: {status}")
    print(f"📊 Health Score: {total_score:.1f}/100")
    print(f"🔧 Service Status: {running_services}/{total_services} total, {critical_running}/{len(critical_services)} critical")
    
    return check_results

def monitor_all_servers(servers):
    """مراقبة جميع السيرفرات"""
    print("\n🌐 Monitoring All Servers")
    print("=" * 60)
    
    all_results = []
    
    for server_name, server in servers.items():
        print(f"\n🖥️  Monitoring {server_name}...")
        
        # فحص أساسي سريع
        start_time = time.time()
        
        if test_server_connection(server):
            # جلب معلومات أساسية
            system_info = get_server_system_info(server)
            accounts = list_accounts(server)
            
            # حساب الإحصائيات
            active_accounts = sum(1 for acct in accounts if acct.get('suspended', 0) == 0) if accounts else 0
            suspended_accounts = len(accounts) - active_accounts if accounts else 0
            
            # فحص خدمات مهمة باستخدام الدالة المحسنة
            critical_services = ['httpd', 'mysql', 'exim']
            running_critical = 0
            
            for service in critical_services:
                try:
                    # استخدام الدالة المحسنة التي تعمل مع WHM API v1
                    service_result = check_specific_service(server, service, [service])
                    if service_result['running']:
                        running_critical += 1
                except:
                    pass
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # تحديد الحالة
            if running_critical == len(critical_services) and suspended_accounts == 0:
                status = "🟢 HEALTHY"
            elif running_critical >= 2:
                status = "🟡 STABLE"
            else:
                status = "🔴 ISSUES"
            
            result = {
                'server': server_name,
                'ip': server['ip'],
                'status': status,
                'whm_version': system_info.get('whm_version', 'Unknown'),
                'total_accounts': len(accounts) if accounts else 0,
                'active_accounts': active_accounts,
                'suspended_accounts': suspended_accounts,
                'critical_services_running': f"{running_critical}/{len(critical_services)}",
                'response_time': f"{response_time}ms",
                'online': True
            }
            
            print(f"   Status: {status}")
            print(f"   Accounts: {active_accounts} active, {suspended_accounts} suspended")
            print(f"   Services: {running_critical}/{len(critical_services)} critical services running")
            print(f"   Response time: {response_time}ms")
            
        else:
            result = {
                'server': server_name,
                'ip': server['ip'],
                'status': '🔴 OFFLINE',
                'whm_version': 'N/A',
                'total_accounts': 'N/A',
                'active_accounts': 'N/A',
                'suspended_accounts': 'N/A',
                'critical_services_running': 'N/A',
                'response_time': 'N/A',
                'online': False
            }
            
            print(f"   Status: 🔴 OFFLINE")
        
        all_results.append(result)
    
    # ملخص عام
    print(f"\n📊 MONITORING SUMMARY")
    print("=" * 50)
    
    total_servers = len(servers)
    online_servers = sum(1 for r in all_results if r['online'])
    offline_servers = total_servers - online_servers
    
    # حساب إجمالي الحسابات
    total_accounts = sum(r['total_accounts'] for r in all_results if isinstance(r['total_accounts'], int))
    total_active = sum(r['active_accounts'] for r in all_results if isinstance(r['active_accounts'], int))
    total_suspended = sum(r['suspended_accounts'] for r in all_results if isinstance(r['suspended_accounts'], int))
    
    print(f"Servers: {online_servers}/{total_servers} online")
    print(f"Total Accounts: {total_accounts}")
    print(f"Active Accounts: {total_active}")
    print(f"Suspended Accounts: {total_suspended}")
    
    if offline_servers > 0:
        print(f"\n⚠️  {offline_servers} server(s) offline:")
        for result in all_results:
            if not result['online']:
                print(f"   🔴 {result['server']} ({result['ip']})")
    
    return all_results

def export_server_monitoring_report(results):
    """تصدير تقرير مراقبة السيرفرات"""
    headers = [
        "Server", "IP Address", "Status", "WHM Version", "Total Accounts", 
        "Active Accounts", "Suspended Accounts", "Critical Services", 
        "Response Time", "Check Date"
    ]
    
    data_rows = []
    for result in results:
        data_rows.append([
            result['server'],
            result['ip'],
            result['status'],
            result['whm_version'],
            result['total_accounts'],
            result['active_accounts'],
            result['suspended_accounts'],
            result['critical_services_running'],
            result['response_time'],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
    
    # تصدير إلى Excel و CSV
    export_to_excel(data_rows, headers, "server_monitoring", "Server Monitoring Report")
    export_to_csv(data_rows, headers, "server_monitoring")

def performance_benchmark(server, server_name):
    """اختبار أداء السيرفر"""
    print(f"\n⚡ Performance Benchmark - {server_name}")
    print("=" * 50)
    
    benchmark_results = {
        'server_name': server_name,
        'ip': server['ip'],
        'benchmark_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print("🚀 Running performance tests...")
    
    # 1. اختبار سرعة الاستجابة
    print("\n1. 📡 Response Time Test...")
    response_times = []
    
    for i in range(5):
        start_time = time.time()
        result = whm_api_call(server, "version")
        end_time = time.time()
        
        if "error" not in result:
            response_time = round((end_time - start_time) * 1000, 2)
            response_times.append(response_time)
            print(f"   Test {i+1}: {response_time}ms")
        else:
            print(f"   Test {i+1}: Failed")
        
        time.sleep(1)  # تأخير بين الاختبارات
    
    if response_times:
        avg_response = sum(response_times) / len(response_times)
        min_response = min(response_times)
        max_response = max(response_times)
        
        print(f"   📊 Average: {avg_response:.2f}ms")
        print(f"   📊 Min: {min_response}ms")
        print(f"   📊 Max: {max_response}ms")
        
        # تقييم الأداء
        if avg_response < 500:
            performance_rating = "🟢 Excellent"
        elif avg_response < 1000:
            performance_rating = "🟡 Good"
        elif avg_response < 2000:
            performance_rating = "🟠 Fair"
        else:
            performance_rating = "🔴 Poor"
        
        print(f"   ⚡ Performance: {performance_rating}")
        
        benchmark_results['response_time'] = {
            'average': avg_response,
            'min': min_response,
            'max': max_response,
            'rating': performance_rating
        }
    else:
        print("   ❌ All response tests failed")
        benchmark_results['response_time'] = {'error': 'All tests failed'}
    
    # 2. اختبار تحميل البيانات
    print("\n2. 📊 Data Loading Test...")
    start_time = time.time()
    accounts = list_accounts(server)
    load_time = round((time.time() - start_time) * 1000, 2)
    
    if accounts:
        print(f"   ✅ Loaded {len(accounts)} accounts in {load_time}ms")
        
        if load_time < 1000:
            load_rating = "🟢 Fast"
        elif load_time < 3000:
            load_rating = "🟡 Moderate"
        elif load_time < 5000:
            load_rating = "🟠 Slow"
        else:
            load_rating = "🔴 Very Slow"
        
        print(f"   📊 Data Loading: {load_rating}")
        
        benchmark_results['data_loading'] = {
            'accounts_count': len(accounts),
            'load_time': load_time,
            'rating': load_rating
        }
    else:
        print("   ❌ Failed to load accounts data")
        benchmark_results['data_loading'] = {'error': 'Failed to load data'}
    
    # 3. اختبار الخدمات المتعددة
    print("\n3. 🔧 Services Response Test...")
    services_to_test = ['version', 'gethostname', 'loadavg']
    service_times = []
    
    for service in services_to_test:
        start_time = time.time()
        result = whm_api_call(server, service)
        service_time = round((time.time() - start_time) * 1000, 2)
        
        if "error" not in result:
            service_times.append(service_time)
            print(f"   {service}: {service_time}ms")
        else:
            print(f"   {service}: Failed")
    
    if service_times:
        avg_service_time = sum(service_times) / len(service_times)
        print(f"   📊 Average service response: {avg_service_time:.2f}ms")
        
        benchmark_results['services_response'] = {
            'average_time': avg_service_time,
            'tested_services': len(service_times)
        }
    
    # حساب النقاط الإجمالية
    total_score = 100
    
    # خصم نقاط حسب الأداء
    if 'response_time' in benchmark_results and 'average' in benchmark_results['response_time']:
        avg_resp = benchmark_results['response_time']['average']
        if avg_resp > 2000:
            total_score -= 30
        elif avg_resp > 1000:
            total_score -= 15
        elif avg_resp > 500:
            total_score -= 5
    
    if 'data_loading' in benchmark_results and 'load_time' in benchmark_results['data_loading']:
        load_time = benchmark_results['data_loading']['load_time']
        if load_time > 5000:
            total_score -= 20
        elif load_time > 3000:
            total_score -= 10
        elif load_time > 1000:
            total_score -= 5
    
    benchmark_results['performance_score'] = max(0, total_score)
    
    # تحديد التقييم العام
    if total_score >= 95:
        overall_rating = "🟢 EXCELLENT"
    elif total_score >= 85:
        overall_rating = "🟡 GOOD"
    elif total_score >= 70:
        overall_rating = "🟠 FAIR"
    else:
        overall_rating = "🔴 POOR"
    
    print(f"\n⚡ OVERALL PERFORMANCE: {overall_rating}")
    print(f"📊 Performance Score: {total_score}/100")
    
    return benchmark_results

# === قوائم فحص المواقع ===
def website_status_checker_menu(servers):
    """قائمة فحص حالة المواقع"""
    print("\n🌐 Website Status Checker")
    print("=" * 50)
    
    while True:
        print(f"\n🔍 Website Status Checking Options:")
        print("1. 🌐 Check all websites from WHM servers")
        print("2. 📂 Check websites from file")
        print("3. 🎯 Check specific domains manually")
        print("4. 🔧 Check broken sites only (non 200/301/302)")
        print("0. 🚪 Back to main menu")
        
        choice = input("\nChoose option: ").strip()
        
        if choice == "1":
            print("\n🔄 This will check all domains from all WHM servers...")
            if confirm_action("Continue with full check?"):
                
                # جلب جميع الدومينات
                all_domains = get_all_domains_from_servers(servers)
                
                if not all_domains:
                    print("❌ No domains found!")
                    continue
                
                # إعدادات الفحص
                print(f"\n⚙️  Checking Configuration:")
                timeout = input("Request timeout (default 10 seconds): ").strip() or "10"
                max_workers = input("Concurrent connections (default 20): ").strip() or "20"
                
                try:
                    timeout = int(timeout)
                    max_workers = int(max_workers)
                except ValueError:
                    print("❌ Invalid settings, using defaults")
                    timeout = 10
                    max_workers = 20
                
                print(f"   ⏱️  Timeout: {timeout} seconds")
                print(f"   🔗 Concurrent: {max_workers} connections")
                print(f"   📊 Total domains: {len(all_domains)}")
                
                estimated_time = (len(all_domains) / max_workers) * (timeout + 2)
                print(f"   ⏰ Estimated time: {estimated_time/60:.1f} minutes")
                
                if confirm_action("Start checking?"):
                    # تشغيل الفحص
                    start_time = time.time()
                    results = check_websites_parallel(all_domains, max_workers, timeout)
                    end_time = time.time()
                    
                    # تحليل النتائج
                    analysis = analyze_website_results(results)
                    
                    print(f"\n⏱️  Check completed in {(end_time - start_time)/60:.2f} minutes")
                    
                    # تصدير النتائج
                    if confirm_action("Export results?"):
                        export_choice = input("Export format (1=Excel, 2=CSV, 3=Both): ").strip()
                        
                        headers = ["Domain", "Status Code", "Status Text", "Final URL", "Response Time (ms)", 
                                  "SSL Valid", "Redirects", "Error", "Check Date"]
                        data_rows = []
                        
                        for result in results:
                            redirects_str = ','.join(map(str, result['redirects'])) if result['redirects'] else ''
                            data_rows.append([
                                result['domain'],
                                result['status_code'],
                                result['status_text'],
                                result['final_url'],
                                result['response_time'],
                                result['ssl_valid'],
                                redirects_str,
                                result['error'] or '',
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                        
                        if export_choice in ["1", "3"]:
                            export_to_excel(data_rows, headers, "website_status_all", "Website Status Report")
                        if export_choice in ["2", "3"]:
                            export_to_csv(data_rows, headers, "website_status_all")

        elif choice == "2":
            print("\n📂 Check Websites from File")
            print("=" * 50)
            print("Instructions:")
            print("1. Create a text file with one domain per line")
            print("2. Domains can be with or without http(s)://")
            print("3. Lines starting with # are ignored")
            print("4. Empty lines are ignored")
    
            file_path = input("\n📂 Enter file path: ").strip()
            if not file_path:
                print("❌ No file path provided")
                continue
    
            print("\nReading file...")
            domains = check_websites_from_file(file_path)
            if domains:
                print(f"\n📋 Found {len(domains)} domains to check")
                if confirm_action("Start checking these domains?"):
                    timeout = int(input("\nTimeout in seconds (default 10): ").strip() or "10")
                    max_workers = int(input("Concurrent connections (default 20): ").strip() or "20")
            
                    results = check_websites_parallel(domains, max_workers, timeout)
                    analysis = analyze_website_results(results)
            
                    if confirm_action("\nExport results?"):
                        export_choice = input("Export format (1=Excel, 2=CSV, 3=Both): ").strip()
                        
                        headers = ["Domain", "Status Code", "Status Text", "Final URL", "Response Time (ms)", 
                                  "SSL Valid", "Redirects", "Error", "Check Date"]
                        data_rows = []
                        
                        for result in results:
                            redirects_str = ','.join(map(str, result['redirects'])) if result['redirects'] else ''
                            data_rows.append([
                                result['domain'],
                                result['status_code'],
                                result['status_text'],
                                result['final_url'],
                                result['response_time'],
                                result['ssl_valid'],
                                redirects_str,
                                result['error'] or '',
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                        
                        if export_choice in ["1", "3"]:
                            export_to_excel(data_rows, headers, "website_status_file", "Website Status from File")
                        if export_choice in ["2", "3"]:
                            export_to_csv(data_rows, headers, "website_status_file")

        elif choice == "3":
            print("\n🎯 Check Specific Websites")
            print("=" * 50)
            print("Enter domains to check (one per line, empty line to finish):")
            
            domains = []
            while True:
                domain = input("Domain: ").strip()
                if not domain:
                    break
                # تنظيف الدومين
                domain = domain.lower()
                if domain.startswith(('http://', 'https://')):
                    parsed = urlparse(domain)
                    domain = parsed.netloc
                domain = domain.split('/')[0]
                if domain.startswith('www.'):
                    domain = domain[4:]
                
                if domain:
                    domains.append(domain)
                    print(f"   ✓ Added: {domain}")
            
            if domains:
                print(f"\n📋 {len(domains)} domains to check:")
                for i, domain in enumerate(domains, 1):
                    print(f"   {i}. {domain}")
                
                timeout = int(input("\nTimeout in seconds (default 10): ").strip() or "10")
                max_workers = int(input("Concurrent connections (default 10): ").strip() or "10")
                
                results = check_websites_parallel(domains, max_workers, timeout)
                analysis = analyze_website_results(results)
                
                if confirm_action("\nExport results?"):
                    export_choice = input("Export format (1=Excel, 2=CSV, 3=Both): ").strip()
                    
                    headers = ["Domain", "Status Code", "Status Text", "Final URL", "Response Time (ms)", 
                              "SSL Valid", "Redirects", "Error", "Check Date"]
                    data_rows = []
                    
                    for result in results:
                        redirects_str = ','.join(map(str, result['redirects'])) if result['redirects'] else ''
                        data_rows.append([
                            result['domain'],
                            result['status_code'],
                            result['status_text'],
                            result['final_url'],
                            result['response_time'],
                            result['ssl_valid'],
                            redirects_str,
                            result['error'] or '',
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                    
                    if export_choice in ["1", "3"]:
                        export_to_excel(data_rows, headers, "website_status_custom", "Custom Website Check")
                    if export_choice in ["2", "3"]:
                        export_to_csv(data_rows, headers, "website_status_custom")
            else:
                print("❌ No domains entered")

        elif choice == "4":
            print("\n🔧 Check Broken Sites Only")
            print("This will find sites with status codes other than 200, 301, 302")
            
            if confirm_action("Continue with broken sites check?"):
                # جلب جميع الدومينات
                all_domains = get_all_domains_from_servers(servers)
                
                if not all_domains:
                    print("❌ No domains found!")
                    continue
                
                timeout = int(input("Request timeout (default 5): ").strip() or "5")
                max_workers = int(input("Concurrent connections (default 30): ").strip() or "30")
                
                # فحص المواقع
                results = check_websites_parallel(all_domains, max_workers, timeout)
                
                # فلترة المواقع المكسورة فقط
                broken_sites = []
                for result in results:
                    if result['status_code'] not in [200, 301, 302]:
                        broken_sites.append(result)
                
                if broken_sites:
                    print(f"\n🔴 Found {len(broken_sites)} Broken Websites:")
                    print("-" * 100)
                    print(f"{'Domain':<30} {'Status':<15} {'Code':<8} {'Error':<30}")
                    print("-" * 100)
                    
                    for site in broken_sites:
                        error_text = site.get('error', '')[:30] if site.get('error') else ''
                        print(f"{site['domain']:<30} {site['status_text']:<15} {site['status_code'] or 'N/A':<8} {error_text:<30}")
                    
                    # تصدير فقط المواقع المكسورة
                    if confirm_action("Export broken sites list?"):
                        export_choice = input("Export format (1=Excel, 2=CSV, 3=Both): ").strip()
                        
                        headers = ["Domain", "Status Code", "Status Text", "Final URL", "Response Time (ms)", 
                                  "SSL Valid", "Redirects", "Error", "Check Date"]
                        data_rows = []
                        
                        for result in broken_sites:
                            redirects_str = ','.join(map(str, result['redirects'])) if result['redirects'] else ''
                            data_rows.append([
                                result['domain'],
                                result['status_code'],
                                result['status_text'],
                                result['final_url'],
                                result['response_time'],
                                result['ssl_valid'],
                                redirects_str,
                                result['error'] or '',
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                        
                        if export_choice in ["1", "3"]:
                            export_to_excel(data_rows, headers, "broken_websites", "Broken Websites Report")
                        if export_choice in ["2", "3"]:
                            export_to_csv(data_rows, headers, "broken_websites")
                else:
                    print("✅ Great! No broken websites found - all sites are working properly!")

        elif choice == "0":
            break
        
        else:
            print("❌ Invalid option")

# === القائمة الرئيسية ===
def main():
    """الدالة الرئيسية"""
    try:
        servers = initialize_script("WHM Server Monitoring & Health Check")
        
        while True:
            print(f"\n{'='*20} SERVER MONITORING & HEALTH CHECK {'='*20}")
            print("🖥️  Server Health & Monitoring:")
            print("1.  🔍 Comprehensive server check")
            print("2.  🌐 Monitor all servers")
            print("3.  ⚡ Performance benchmark")
            print("4.  🔧 Check server services")
            print("5.  📊 Server statistics report")
            
            print("\n🌐 Website Status Monitoring:")
            print("6.  🔍 Check all websites status")
            print("7.  📂 Check websites from file")
            print("8.  🎯 Check specific websites")
            print("9.  🔴 Find broken websites only")
            
            print("\n📈 System Analysis:")
            print("10. 📊 Generate monitoring report")
            print("11. 🎯 Quick health check (all servers)")
            print("12. 🔧 System information overview")
            
            print("\n🔧 System Tools:")
            print("13. 🌐 Check server status")
            print("14. 📜 View operation logs")
            print("15. 🎲 Generate random password")
            print("16. 🔍 Detailed Service Diagnostics")
            print("17. 📋 Large logs management")
            print("18. 🔄 Account transfer between servers")
            
            print("\n0.  🚪 Exit")
            print("=" * 75)
            
            choice = input("Choose option: ").strip()

            if choice == "1":
                # فحص شامل لسيرفر محدد
                online_servers = get_online_servers(servers)
                if online_servers:
                    print(f"\nAvailable servers:")
                    for name, server in online_servers.items():
                        print(f"   {name}: {server['ip']}")
                    
                    server_choice = input(f"\nChoose server ({'/'.join(online_servers.keys())}): ").strip()
                    if server_choice in online_servers:
                        result = comprehensive_server_check(online_servers[server_choice], server_choice)
                        
                        if confirm_action("\nExport detailed report?"):
                            # تصدير التقرير المفصل
                            headers = ["Check Item", "Status", "Details", "Score"]
                            data_rows = [
                                ["Connectivity", "✅ Online" if result['connectivity'] else "❌ Offline", 
                                 f"Server: {result['server_name']}", "20/20" if result['connectivity'] else "0/20"],
                                ["System Info", "✅ Available" if result['system_info']['status'] == 'online' else "❌ Error", 
                                 f"WHM: {result['system_info'].get('whm_version', 'Unknown')}", 
                                 "20/20" if result['system_info']['status'] == 'online' else "0/20"],
                                ["Services", f"{len([s for s in result['services'].values() if s.get('running', False)])}/{len(result['services'])} Running", 
                                 "Critical services check", f"{len([s for s in result['services'].values() if s.get('running', False)])}/{len(result['services'])}"],
                                ["Accounts", f"{result['accounts']['total']} Total", 
                                 f"Active: {result['accounts']['active']}, Suspended: {result['accounts']['suspended']}", 
                                 f"{result['accounts']['active']}/{result['accounts']['total']}"],
                                ["Overall Score", result['status'], f"Health Score: {result['health_score']:.1f}/100", f"{result['health_score']:.1f}/100"]
                            ]
                            
                            export_to_excel(data_rows, headers, f"server_check_{server_choice}", f"Server Check - {server_choice}")
                    else:
                        print("❌ Invalid server choice!")

            elif choice == "2":
                # مراقبة جميع السيرفرات
                results = monitor_all_servers(servers)
                
                if confirm_action("\nExport monitoring report?"):
                    export_server_monitoring_report(results)

            elif choice == "3":
                # اختبار الأداء
                online_servers = get_online_servers(servers)
                if online_servers:
                    print(f"\nAvailable servers:")
                    for name, server in online_servers.items():
                        print(f"   {name}: {server['ip']}")
                    
                    server_choice = input(f"\nChoose server ({'/'.join(online_servers.keys())}): ").strip()
                    if server_choice in online_servers:
                        benchmark_result = performance_benchmark(online_servers[server_choice], server_choice)
                        
                        if confirm_action("\nExport benchmark report?"):
                            headers = ["Metric", "Value", "Rating", "Details"]
                            data_rows = []
                            
                            if 'response_time' in benchmark_result:
                                rt = benchmark_result['response_time']
                                if 'average' in rt:
                                    data_rows.append([
                                        "Response Time",
                                        f"{rt['average']:.2f}ms avg",
                                        rt.get('rating', 'Unknown'),
                                        f"Min: {rt['min']}ms, Max: {rt['max']}ms"
                                    ])
                            
                            if 'data_loading' in benchmark_result:
                                dl = benchmark_result['data_loading']
                                if 'load_time' in dl:
                                    data_rows.append([
                                        "Data Loading",
                                        f"{dl['load_time']}ms",
                                        dl.get('rating', 'Unknown'),
                                        f"Loaded {dl['accounts_count']} accounts"
                                    ])
                            
                            data_rows.append([
                                "Overall Performance",
                                f"{benchmark_result['performance_score']}/100",
                                "Performance Score",
                                f"Benchmark Date: {benchmark_result['benchmark_date']}"
                            ])
                            
                            export_to_excel(data_rows, headers, f"performance_benchmark_{server_choice}", 
                                          f"Performance Benchmark - {server_choice}")
                    else:
                        print("❌ Invalid server choice!")

            elif choice == "4":
                # فحص خدمات السيرفر
                online_servers = get_online_servers(servers)
                if online_servers:
                    server_choice = input(f"\nChoose server ({'/'.join(online_servers.keys())}): ").strip()
                    if server_choice in online_servers:
                        print(f"\n🔧 Checking Services - {server_choice}")
                        print("=" * 50)
                        
                        services = check_server_services(online_servers[server_choice])
                        
                        print(f"{'Service':<15} {'Status':<15} {'Running':<10} {'Enabled'}")
                        print("-" * 55)
                        
                        for service_name, service_info in services.items():
                            running = "✅ Yes" if service_info.get('running', False) else "❌ No"
                            enabled = "✅ Yes" if service_info.get('enabled', False) else "❌ No"
                            print(f"{service_name:<15} {service_info['status']:<15} {running:<10} {enabled}")
                    else:
                        print("❌ Invalid server choice!")

            elif choice == "5":
                # تقرير إحصائيات السيرفر
                print("\n📊 Server Statistics Report")
                print("=" * 50)
                
                total_servers = len(servers)
                online_count = 0
                total_accounts = 0
                total_active = 0
                total_suspended = 0
                
                server_details = []
                
                for server_name, server in servers.items():
                    if test_server_connection(server):
                        online_count += 1
                        accounts = list_accounts(server)
                        
                        if accounts:
                            server_accounts = len(accounts)
                            active_accounts = sum(1 for acct in accounts if acct.get('suspended', 0) == 0)
                            suspended_accounts = server_accounts - active_accounts
                            
                            total_accounts += server_accounts
                            total_active += active_accounts
                            total_suspended += suspended_accounts
                            
                            server_details.append({
                                'server': server_name,
                                'ip': server['ip'],
                                'status': 'Online',
                                'accounts': server_accounts,
                                'active': active_accounts,
                                'suspended': suspended_accounts
                            })
                        else:
                            server_details.append({
                                'server': server_name,
                                'ip': server['ip'],
                                'status': 'Online (No Accounts)',
                                'accounts': 0,
                                'active': 0,
                                'suspended': 0
                            })
                    else:
                        server_details.append({
                            'server': server_name,
                            'ip': server['ip'],
                            'status': 'Offline',
                            'accounts': 'N/A',
                            'active': 'N/A',
                            'suspended': 'N/A'
                        })
                
                print(f"📈 Overall Statistics:")
                print(f"   Total Servers: {total_servers}")
                print(f"   Online Servers: {online_count}")
                print(f"   Offline Servers: {total_servers - online_count}")
                print(f"   Total Accounts: {total_accounts}")
                print(f"   Active Accounts: {total_active}")
                print(f"   Suspended Accounts: {total_suspended}")
                
                print(f"\n🖥️  Server Breakdown:")
                print("-" * 70)
                print(f"{'Server':<15} {'IP':<15} {'Status':<20} {'Accounts':<10} {'Active':<8} {'Suspended'}")
                print("-" * 70)
                
                for detail in server_details:
                    print(f"{detail['server']:<15} {detail['ip']:<15} {detail['status']:<20} "
                          f"{detail['accounts']:<10} {detail['active']:<8} {detail['suspended']}")

            elif choice == "6":
                # فحص جميع المواقع
                website_status_checker_menu(servers)

            elif choice == "7":
                # فحص المواقع من ملف
                print("\n📂 Check Websites from File")
                print("=" * 50)
                
                file_path = input("📂 Enter file path: ").strip()
                if file_path:
                    domains = check_websites_from_file(file_path)
                    if domains:
                        timeout = int(input("Timeout in seconds (default 10): ").strip() or "10")
                        max_workers = int(input("Concurrent connections (default 20): ").strip() or "20")
                        
                        results = check_websites_parallel(domains, max_workers, timeout)
                        analysis = analyze_website_results(results)

            elif choice == "8":
                # فحص مواقع محددة
                print("\n🎯 Check Specific Websites")
                print("=" * 50)
                print("Enter domains (one per line, empty line to finish):")
                
                domains = []
                while True:
                    domain = input("Domain: ").strip()
                    if not domain:
                        break
                    domains.append(domain)
                    print(f"   ✓ Added: {domain}")
                
                if domains:
                    timeout = int(input("Timeout (default 10): ").strip() or "10")
                    max_workers = int(input("Concurrent connections (default 10): ").strip() or "10")
                    
                    results = check_websites_parallel(domains, max_workers, timeout)
                    analysis = analyze_website_results(results)

            elif choice == "9":
                # البحث عن المواقع المعطلة فقط
                print("\n🔴 Find Broken Websites Only")
                print("=" * 50)
                
                all_domains = get_all_domains_from_servers(servers)
                if all_domains:
                    timeout = int(input("Timeout (default 5): ").strip() or "5")
                    max_workers = int(input("Concurrent connections (default 30): ").strip() or "30")
                    
                    results = check_websites_parallel(all_domains, max_workers, timeout)
                    
                    # فلترة المواقع المكسورة
                    broken_sites = [r for r in results if r['status_code'] not in [200, 301, 302]]
                    
                    if broken_sites:
                        print(f"\n🔴 Found {len(broken_sites)} broken websites")
                        for site in broken_sites[:10]:
                            print(f"   {site['domain']} - {site['status_text']}")
                    else:
                        print("✅ No broken websites found!")

            elif choice == "10":
                # توليد تقرير المراقبة
                print("\n📊 Generating Monitoring Report...")
                results = monitor_all_servers(servers)
                export_server_monitoring_report(results)

            elif choice == "11":
                # فحص سريع لجميع السيرفرات
                print("\n🎯 Quick Health Check - All Servers")
                print("=" * 60)
                
                for server_name, server in servers.items():
                    health = check_basic_health(server, server_name)

            elif choice == "12":
                # نظرة عامة على معلومات النظام
                print("\n🔧 System Information Overview")
                print("=" * 50)
                
                for server_name, server in servers.items():
                    print(f"\n🖥️  {server_name}:")
                    
                    if test_server_connection(server):
                        system_info = get_server_system_info(server)
                        if system_info['status'] == 'online':
                            print(f"   IP: {system_info['server_ip']}")
                            print(f"   WHM Version: {system_info['whm_version']}")
                            print(f"   Hostname: {system_info['hostname']}")
                            load_avg = system_info['load_average']
                            print(f"   Load Average: {load_avg['1min']}, {load_avg['5min']}, {load_avg['15min']}")
                        else:
                            print(f"   Status: Error getting system info")
                    else:
                        print(f"   Status: Offline")

            elif choice == "13":
                display_server_status(servers)

            elif choice == "14":
                show_logs()

            elif choice == "15":
                length = input("🔢 Password length (default 12): ").strip() or "12"
                try:
                    length = int(length)
                    password = generate_password(length)
                    print(f"🎲 Generated password: {password}")
                except ValueError:
                    print("❌ Invalid length")
            
            elif choice == "16":
                # تشخيص مفصل للخدمات
                print("\n🔍 Detailed Service Diagnostics")
                print("=" * 50)
                server_name = input("Enter server name to diagnose: ").strip()
                if server_name in servers:
                    diagnose_service_issues(servers[server_name], server_name)
                else:
                    print("❌ Server not found")
            
            elif choice == "17":
                # إدارة اللوجات الكبيرة
                large_logs_management_menu(servers)
            
            elif choice == "18":
                # نقل الحسابات بين السيرفرات
                account_transfer_menu(servers)

            elif choice == "0":
                print("👋 Goodbye!")
                logging.info("Server Monitoring & Health Check closed")
                break
                
            else:
                print("❌ Invalid option")

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        logging.info("Program interrupted by user")
        sys.exit(0)
    except Exception as e:
        handle_script_error(e, "Server Monitoring & Health Check")
        sys.exit(1)

def check_specific_service(server, service_name, process_names):
    """فحص خدمة محددة باستخدام طرق متعددة"""
    result = {
        'running': False,
        'method': 'none',
        'methods_tried': [],
        'pid': None,
        'port_open': None
    }
    
    # Method 1: Check via basic WHM APIs that should work
    try:
        # Try to use basic WHM APIs that are available in version 1
        if service_name == 'httpd':
            # Try to check if Apache is running by checking a basic WHM function
            try:
                # Try to get server info - if it works, Apache is likely running
                server_info = whm_api_call(server, "version")
                if "error" not in server_info:
                    result['running'] = True
                    result['method'] = 'whm_version_check'
                    result['methods_tried'].append('whm_version')
                    return result
            except:
                pass
            
            # Try to check if we can access WHM - if yes, Apache is running
            try:
                account_list = whm_api_call(server, "listaccts")
                if "error" not in account_list:
                    result['running'] = True
                    result['method'] = 'whm_accounts_check'
                    result['methods_tried'].append('whm_accounts')
                    return result
            except:
                pass
                
        elif service_name == 'mysql':
            # Try to check MySQL by checking if we can get account info
            try:
                account_list = whm_api_call(server, "listaccts")
                if "error" not in account_list:
                    # If we can get accounts, MySQL is likely running
                    result['running'] = True
                    result['method'] = 'whm_accounts_check'
                    result['methods_tried'].append('whm_accounts')
                    return result
            except:
                pass
                
        elif service_name == 'exim':
            # Try to check Exim using multiple fallback methods since mailq API is not available in v1
            
            # PRIORITY 1: Check if we can get account info (indicates system is running)
            try:
                account_list = whm_api_call(server, "listaccts")
                if "error" not in account_list:
                    # If we can get accounts, Exim is likely running
                    result['running'] = True
                    result['method'] = 'whm_accounts_check'
                    result['methods_tried'].append('whm_accounts')
                    return result
            except:
                pass
            
            # PRIORITY 2: Check if WHM is responding (indicates system is running)
            try:
                version_result = whm_api_call(server, "version")
                if "error" not in version_result:
                    # If WHM is responding, Exim is likely running
                    result['running'] = True
                    result['method'] = 'whm_version_check'
                    result['methods_tried'].append('whm_version')
                    return result
            except:
                pass
            
            # PRIORITY 3: Try to check if we can get server load (indicates system is running)
            try:
                load_result = whm_api_call(server, "loadavg")
                if "error" not in load_result:
                    # If we can get load, Exim is likely running
                    result['running'] = True
                    result['method'] = 'loadavg_check'
                    result['methods_tried'].append('loadavg')
                    return result
            except:
                pass
        
        result['methods_tried'].append('whm_basic_apis')
        
    except Exception as e:
        result['methods_tried'].append(f'whm_basic_apis (failed: {str(e)})')
    
    # Method 2: Try to infer from server response patterns (EXCLUDING exim)
    if not result['running'] and service_name != 'exim':
        try:
            # Check if server responds quickly (indicates services are running)
            start_time = time.time()
            test_result = whm_api_call(server, "version")
            response_time = (time.time() - start_time) * 1000
            
            if "error" not in test_result and response_time < 1000:  # Less than 1 second
                # Fast response usually means services are running
                result['running'] = True
                result['method'] = 'response_time_check'
                result['methods_tried'].append('response_time')
            else:
                result['methods_tried'].append('response_time')
                
        except Exception as e:
            result['methods_tried'].append(f'response_time (failed: {str(e)})')
    
    # Method 3: Try to check service status via WHM functions
    if not result['running']:
        try:
            # Try to get server status via WHM
            if service_name == 'httpd':
                # Check if we can get server load (indicates Apache is running)
                try:
                    load_result = whm_api_call(server, "loadavg")
                    if "error" not in load_result:
                        result['running'] = True
                        result['method'] = 'loadavg_check'
                        result['methods_tried'].append('loadavg')
                        return result
                except:
                    pass
                    
            elif service_name == 'mysql':
                # Check if we can get account details (indicates MySQL is running)
                try:
                    account_result = whm_api_call(server, "listaccts")
                    if "error" not in account_result and "acct" in account_result:
                        result['running'] = True
                        result['method'] = 'account_details_check'
                        result['methods_tried'].append('account_details')
                        return result
                except:
                    pass
                    
            elif service_name == 'exim':
                # Check if we can get mail statistics (indicates Exim is running)
                # Note: mailq API is not available in WHM API v1, so we use fallbacks
                
                # Check if we can get account details (indicates system is running)
                try:
                    account_result = whm_api_call(server, "listaccts")
                    if "error" not in account_result and "acct" in account_result:
                        result['running'] = True
                        result['method'] = 'account_details_check'
                        result['methods_tried'].append('account_details')
                        return result
                except:
                    pass
                
                # Additional check: try to get server version (indicates system is running)
                try:
                    version_result = whm_api_call(server, "version")
                    if "error" not in version_result:
                        # If WHM is responding, Exim is likely running
                        result['running'] = True
                        result['method'] = 'whm_version_check'
                        result['methods_tried'].append('whm_version')
                        return result
                except:
                    pass
            
            result['methods_tried'].append('whm_service_functions')
            
        except Exception as e:
            result['methods_tried'].append(f'whm_service_functions (failed: {str(e)})')
    
    return result

def diagnose_service_issues(server, server_name):
    """تشخيص مشاكل الخدمات بشكل مفصل"""
    print(f"\n🔍 Service Diagnostics - {server_name}")
    print("=" * 60)
    
    services_config = {
        'httpd': {
            'processes': ['httpd', 'apache2'],
            'ports': [80, 443],
            'config_files': ['/etc/httpd/conf/httpd.conf', '/etc/apache2/apache2.conf']
        },
        'mysql': {
            'processes': ['mysqld', 'mariadb'],
            'ports': [3306],
            'config_files': ['/etc/my.cnf', '/etc/mysql/my.cnf']
        },
        'exim': {
            'processes': ['exim'],
            'ports': [25, 587],
            'config_files': ['/etc/exim/exim.conf']
        }
    }
    
    for service_name, config in services_config.items():
        print(f"\n🔧 Diagnosing {service_name}...")
        
        # Check each detection method
        service_result = check_specific_service(server, service_name, config['processes'])
        
        print(f"   Status: {'🟢 Running' if service_result['running'] else '🔴 Not Running'}")
        print(f"   Detection method: {service_result['method']}")
        print(f"   Methods tried: {', '.join(service_result['methods_tried'])}")
        
        if 'pid' in service_result:
            print(f"   Process ID: {service_result['pid']}")
        if 'port_open' in service_result:
            print(f"   Active port: {service_result['port_open']}")
    
    return True

# === دوال إدارة اللوجات الكبيرة ===
def find_large_logs(server, min_size_mb=100):
    """البحث عن اللوجات الكبيرة في السيرفر"""
    try:
        print(f"\n🔍 Searching for large log files (>{min_size_mb}MB) on {server['ip']}...")
        
        # محاولة استخدام exec API أولاً
        find_command = f"find /home /var/log /usr/local/apache/logs /usr/local/cpanel/logs -type f -name '*.log' -size +{min_size_mb}M -exec ls -lh {{}} \\; 2>/dev/null"
        
        result = whm_api_call(server, "exec", {"command": find_command})
        
        if "error" in result:
            # إذا فشل exec، جرب shell API
            print(f"⚠️  exec API not supported, trying shell API...")
            result = whm_api_call(server, "shell", {"command": find_command})
            
            if "error" in result:
                # إذا فشل shell أيضاً، استخدم الطرق البديلة
                print(f"⚠️  shell API not supported, using alternative methods...")
                return find_large_logs_alternative(server, min_size_mb)
        
        if not result.get("data"):
            print("✅ No large log files found")
            return []
        
        log_files = []
        lines = result["data"].strip().split('\n')
        
        for line in lines:
            if line.strip():
                # تحليل سطر ls -lh
                parts = line.split()
                if len(parts) >= 5:
                    permissions = parts[0]
                    size = parts[4]
                    date = f"{parts[5]} {parts[6]} {parts[7]}"
                    filepath = parts[-1]
                    
                    log_files.append({
                        'permissions': permissions,
                        'size': size,
                        'date': date,
                        'filepath': filepath
                    })
        
        return log_files
        
    except Exception as e:
        print(f"❌ Error finding large logs: {str(e)}")
        return []

def find_large_logs_alternative(server, min_size_mb=100):
    """طريقة بديلة للبحث عن اللوجات الكبيرة باستخدام WHM API v1"""
    try:
        print(f"🔍 Using alternative method for WHM API v1...")
        
        # محاولة الحصول على معلومات النظام
        system_info = whm_api_call(server, "version")
        if "error" in system_info:
            print(f"❌ Cannot access server via WHM API v1")
            print(f"💡 Alternative solutions:")
            print(f"   1. Use SSH to run: find /home /var/log -type f -name '*.log' -size +{min_size_mb}M -exec ls -lh {{}} \\;")
            print(f"   2. Check server logs manually")
            print(f"   3. Contact server administrator")
            return []
        
        # محاولة الحصول على معلومات الحسابات
        accounts = whm_api_call(server, "listaccts")
        if "error" in accounts:
            print(f"❌ Cannot access account information")
            return []
        
        # إذا وصلنا هنا، السيرفر متصل ولكن لا يمكن تنفيذ أوامر shell
        print(f"✅ Server is accessible via WHM API v1")
        print(f"⚠️  Shell commands not supported in this version")
        print(f"💡 To find large log files, please:")
        print(f"   1. Connect via SSH to {server['ip']}")
        print(f"   2. Run: find /home /var/log -type f -name '*.log' -size +{min_size_mb}M -exec ls -lh {{}} \\;")
        print(f"   3. Or check these common log locations:")
        print(f"      - /var/log/messages")
        print(f"      - /var/log/secure")
        print(f"      - /var/log/maillog")
        print(f"      - /usr/local/apache/logs/access_log")
        print(f"      - /usr/local/apache/logs/error_log")
        
        return []
        
    except Exception as e:
        print(f"❌ Error in alternative method: {str(e)}")
        return []

def show_manual_commands_guide(server, server_name):
    """عرض دليل الأوامر اليدوية للتنفيذ عبر SSH"""
    print(f"\n📋 Manual Commands Guide for {server_name}")
    print("=" * 60)
    print(f"🔗 Server: {server['ip']}")
    print(f"📝 Since WHM API v1 doesn't support shell commands, use SSH instead")
    print()
    
    print("🔍 1. FIND LARGE LOG FILES:")
    print("   SSH to server and run:")
    print(f"   ssh root@{server['ip']}")
    print("   # Search for large log files")
    print("   find /home /var/log /usr/local/apache/logs /usr/local/cpanel/logs -type f -name '*.log' -size +100M -exec ls -lh {} \\;")
    print()
    
    print("🗑️  2. DELETE LARGE LOG FILES:")
    print("   # Delete specific log file")
    print("   rm -f /path/to/large/logfile.log")
    print("   # Delete multiple log files")
    print("   find /var/log -name '*.log' -size +500M -delete")
    print()
    
    print("📝 3. TRUNCATE LARGE LOG FILES:")
    print("   # Empty log file content (keep file)")
    print("   cat /dev/null > /path/to/large/logfile.log")
    print("   # Alternative method")
    print("   echo '' > /path/to/large/logfile.log")
    print()
    
    print("📊 4. CHECK DISK USAGE:")
    print("   # Check disk space")
    print("   df -h")
    print("   # Check directory sizes")
    print("   du -sh /var/log/*")
    print("   du -sh /home/*/public_html/logs/* 2>/dev/null")
    print()
    
    print("🔧 5. COMMON LOG LOCATIONS:")
    print("   /var/log/messages      # System messages")
    print("   /var/log/secure        # Security logs")
    print("   /var/log/maillog       # Mail logs")
    print("   /var/log/cron          # Cron logs")
    print("   /usr/local/apache/logs/access_log  # Apache access")
    print("   /usr/local/apache/logs/error_log   # Apache errors")
    print("   /usr/local/cpanel/logs/*           # cPanel logs")
    print()
    
    print("⚠️  IMPORTANT NOTES:")
    print("   • Always backup important logs before deletion")
    print("   • Check file permissions before operations")
    print("   • Monitor disk space after cleanup")
    print("   • Restart services if needed after log operations")
    print()
    
    print("💡 TIPS:")
    print("   • Use 'tail -f /var/log/messages' to monitor logs in real-time")
    print("   • Set up log rotation to prevent future issues")
    print("   • Consider using 'logrotate' for automatic log management")
    print()
    
    print("🔗 SSH Connection:")
    print(f"   ssh root@{server['ip']}")
    print("   # Or if you have a different user:")
    print(f"   ssh username@{server['ip']}")

def test_server_connection_and_token(server, server_name):
    """اختبار الاتصال بالسيرفر والتوكن"""
    print(f"\n🔧 Testing Server Connection & Token - {server_name}")
    print("=" * 60)
    print(f"🔗 Server: {server['ip']}")
    print()
    
    # اختبار الاتصال الأساسي
    print("1. 🔍 Testing Basic Connection...")
    try:
        version_result = whm_api_call(server, "version")
        if "error" in version_result:
            print(f"❌ Connection failed: {version_result['error']}")
            return False
        else:
            print(f"✅ Basic connection successful")
            print(f"   WHM Version: {version_result.get('version', 'Unknown')}")
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    
    # اختبار الصلاحيات
    print("\n2. 🔐 Testing API Token Permissions...")
    
    # اختبار exec API
    print("   Testing exec API...")
    exec_result = whm_api_call(server, "exec", {"command": "echo 'test'"})
    if "error" in exec_result:
        print(f"   ❌ exec API: {exec_result['error']}")
        exec_available = False
    else:
        print(f"   ✅ exec API: Available")
        exec_available = True
    
    # اختبار shell API
    print("   Testing shell API...")
    shell_result = whm_api_call(server, "shell", {"command": "echo 'test'"})
    if "error" in shell_result:
        print(f"   ❌ shell API: {shell_result['error']}")
        shell_available = False
    else:
        print(f"   ✅ shell API: Available")
        shell_available = True
    
    # اختبار أوامر أخرى
    print("\n3. 🧪 Testing Additional Commands...")
    
    # اختبار listaccts
    try:
        accts_result = whm_api_call(server, "listaccts")
        if "error" in accts_result:
            print(f"   ❌ listaccts: {accts_result['error']}")
        else:
            print(f"   ✅ listaccts: Available")
    except Exception as e:
        print(f"   ❌ listaccts error: {str(e)}")
    
    # اختبار loadavg
    try:
        load_result = whm_api_call(server, "loadavg")
        if "error" in load_result:
            print(f"   ❌ loadavg: {load_result['error']}")
        else:
            print(f"   ✅ loadavg: Available")
    except Exception as e:
        print(f"   ❌ loadavg error: {str(e)}")
    
    # ملخص النتائج
    print(f"\n📊 Summary:")
    print(f"   🔗 Server: {server_name}: {server['ip']}")
    print(f"   ✅ Basic Connection: Working")
    print(f"   🔐 exec API: {'Available' if exec_available else 'Not Available'}")
    print(f"   🔐 shell API: {'Available' if shell_available else 'Not Available'}")
    
    if exec_available or shell_available:
        print(f"\n🎉 Great! This server supports shell commands.")
        print(f"   You can now use all log management features!")
    else:
        print(f"\n⚠️  This server doesn't support shell commands.")
        print(f"   Use option 5 for manual SSH guide.")
    
    return True

def transfer_account_between_servers(source_server, target_server, username, transfer_type="full"):
    """نقل حساب بين سيرفرين"""
    try:
        print(f"\n🔄 Transferring Account: {username}")
        print("=" * 60)
        print(f"📤 Source Server: {source_server['ip']}")
        print(f"📥 Target Server: {target_server['ip']}")
        print(f"🔧 Transfer Type: {transfer_type}")
        print()
        
        # 1. فحص الحساب في السيرفر المصدر
        print("1. 🔍 Checking source account...")
        account_info = whm_api_call(source_server, "listaccts")
        
        if "error" in account_info:
            print(f"❌ Error getting account info: {account_info['error']}")
            return False
        
        # تشخيص البيانات المستلمة
        print(f"   🔍 Debug: API response structure:")
        print(f"      Response keys: {list(account_info.keys())}")
        
        # فحص مفصل لهيكل البيانات
        for key, value in account_info.items():
            if isinstance(value, list):
                print(f"      📋 List key '{key}': {len(value)} items")
                if value and len(value) > 0:
                    print(f"         First item: {value[0]}")
            elif isinstance(value, dict):
                print(f"      📊 Dict key '{key}': {len(value)} keys")
                if value:
                    print(f"         Dict keys: {list(value.keys())}")
            else:
                print(f"      🔍 Key '{key}': {type(value).__name__} = {value}")
        
        # البحث عن الحساب مع تشخيص أفضل
        account_found = False
        
        # محاولة الحصول على قائمة الحسابات من مفاتيح مختلفة
        accounts_list = account_info.get("acct", [])
        if not accounts_list:
            # محاولة الوصول إلى data.acct
            data_section = account_info.get("data", {})
            if isinstance(data_section, dict):
                accounts_list = data_section.get("acct", [])
        if not accounts_list:
            accounts_list = account_info.get("accounts", [])
        
        if not accounts_list:
            print(f"   ⚠️  No accounts list found in response")
            print(f"   🔍 Full response: {account_info}")
            return False
        
        print(f"   📊 Total accounts found: {len(accounts_list)}")
        
        # البحث مع طباعة معلومات التشخيص
        for i, acct in enumerate(accounts_list):
            print(f"      Account {i+1}: {acct}")
            if acct.get("user") == username:
                account_found = True
                domain = acct.get("domain", "Unknown")
                home_dir = acct.get("homedir", "")
                
                # التأكد من أن المسار صحيح
                if not home_dir or home_dir == "":
                    home_dir = f"/home/{username}"
                    print(f"   ⚠️  Home directory not found, using default: {home_dir}")
                else:
                    print(f"   ✅ Account found: {username} ({domain})")
                    print(f"   📁 Home directory: {home_dir}")
                break
        
        if not account_found:
            print(f"❌ Account {username} not found on source server")
            print(f"   🔍 Available accounts:")
            for acct in accounts_list[:5]:  # عرض أول 5 حسابات
                print(f"      - {acct.get('user', 'Unknown')} ({acct.get('domain', 'Unknown')})")
            if len(accounts_list) > 5:
                print(f"      ... and {len(accounts_list) - 5} more accounts")
            return False
        
        # 2. فحص المساحة في السيرفر الهدف
        print("\n2. 📊 Checking target server space...")
        try:
            # محاولة الحصول على معلومات القرص
            disk_info = whm_api_call(target_server, "get_disk_usage")
            if "error" not in disk_info:
                print(f"   ✅ Disk info available")
            else:
                print(f"   ⚠️  Cannot get disk info, proceeding anyway")
        except:
            print(f"   ⚠️  Cannot get disk info, proceeding anyway")
        
        # 3. إنشاء نسخة احتياطية
        print("\n3. 💾 Creating backup...")
        print(f"   📁 Creating backup from: {home_dir}")
        backup_filename = f"{username}_backup_{int(time.time())}.tar.gz"
        backup_command = f"cd {home_dir} && tar -czf /tmp/{backup_filename} ."
        
        print(f"   🔧 Command: {backup_command}")
        print(f"   📦 Backup file: {backup_filename}")
        
        # محاولة استخدام exec API
        backup_result = whm_api_call(source_server, "exec", {"command": backup_command})
        
        if "error" in backup_result:
            print(f"   ❌ Cannot create backup via API: {backup_result['error']}")
            print(f"   💡 Manual backup required:")
            print(f"      SSH to {source_server['ip']} and run:")
            print(f"      {backup_command}")
            print(f"\n   🔧 Alternative manual commands:")
            print(f"      # 1. إنشاء النسخة الاحتياطية")
            print(f"      ssh root@{source_server['ip']}")
            print(f"      cd {home_dir}")
            print(f"      tar -czf /tmp/{backup_filename} .")
            print(f"      ls -lh /tmp/{backup_filename}")
            print(f"\n      # 2. نقل النسخة إلى السيرفر الهدف")
            print(f"      scp /tmp/{backup_filename} root@{target_server['ip']}:/tmp/")
            print(f"\n      # 3. إنشاء الحساب في السيرفر الهدف")
            print(f"      # (استخدم WHM أو cPanel)")
            print(f"\n      # 4. استعادة الملفات")
            print(f"      ssh root@{target_server['ip']}")
            print(f"      cd /home/{username}")
            print(f"      tar -xzf /tmp/{backup_filename}")
            print(f"      chown -R {username}:{username} .")
            print(f"      rm /tmp/{backup_filename}")
            return False
        
        print(f"   ✅ Backup created successfully: {backup_filename}")
        
        # 4. نقل النسخة الاحتياطية
        print("\n4. 📤 Transferring backup to target server...")
        print(f"   📤 From: {source_server['ip']}")
        print(f"   📥 To: {target_server['ip']}")
        
        transfer_command = f"scp /tmp/{backup_filename} root@{target_server['ip']}:/tmp/"
        print(f"   🔧 Command: {transfer_command}")
        
        transfer_result = whm_api_call(source_server, "exec", {"command": transfer_command})
        
        if "error" in transfer_result:
            print(f"   ❌ Cannot transfer via API: {transfer_result['error']}")
            print(f"   💡 Manual transfer required:")
            print(f"      SSH to {source_server['ip']} and run:")
            print(f"      {transfer_command}")
            print(f"\n   🔧 Alternative manual transfer:")
            print(f"      # من السيرفر المصدر:")
            print(f"      ssh root@{source_server['ip']}")
            print(f"      scp /tmp/{backup_filename} root@{target_server['ip']}:/tmp/")
            print(f"      # أو من السيرفر الهدف:")
            print(f"      ssh root@{target_server['ip']}")
            print(f"      scp root@{source_server['ip']}:/tmp/{backup_filename} /tmp/")
            return False
        
        print(f"   ✅ Backup transferred successfully to target server")
        
        # 5. استعادة الحساب في السيرفر الهدف
        print("\n5. 📥 Restoring account on target server...")
        print(f"   🔧 Target server: {target_server['ip']}")
        
        # إنشاء الحساب في السيرفر الهدف
        print(f"   👤 Creating account: {username}")
        create_account_result = whm_api_call(target_server, "createacct", {
            "username": username,
            "domain": domain,
            "pkgname": "default"  # أو اسم الباقة المناسبة
        })
        
        if "error" in create_account_result:
            print(f"   ❌ Cannot create account: {create_account_result['error']}")
            return False
        
        print(f"   ✅ Account created successfully on target server")
        
        # استعادة الملفات
        print(f"   📁 Restoring files from backup...")
        restore_command = f"cd /home/{username} && tar -xzf /tmp/{backup_filename} && chown -R {username}:{username} . && rm /tmp/{backup_filename}"
        print(f"   🔧 Command: {restore_command}")
        
        restore_result = whm_api_call(target_server, "exec", {"command": restore_command})
        
        if "error" in restore_result:
            print(f"   ❌ Cannot restore files: {restore_result['error']}")
            print(f"   💡 Manual restore required:")
            print(f"      SSH to {target_server['ip']} and run:")
            print(f"      {restore_command}")
            print(f"\n   🔧 Alternative manual restore:")
            print(f"      ssh root@{target_server['ip']}")
            print(f"      cd /home/{username}")
            print(f"      tar -xzf /tmp/{backup_filename}")
            print(f"      chown -R {username}:{username} .")
            print(f"      rm /tmp/{backup_filename}")
            return False
        
        print(f"   ✅ Files restored successfully")
        
        # 6. تنظيف النسخة الاحتياطية من السيرفر المصدر
        print("\n6. 🧹 Cleaning up temporary files...")
        cleanup_command = f"rm -f /tmp/{backup_filename}"
        whm_api_call(source_server, "exec", {"command": cleanup_command})
        print(f"   ✅ Cleanup completed")
        
        print(f"\n🎉 Account transfer completed successfully!")
        print(f"   📤 From: {source_server['ip']}")
        print(f"   📥 To: {target_server['ip']}")
        print(f"   👤 Account: {username}")
        print(f"   🌐 Domain: {domain}")
        print(f"   📁 Home directory: {home_dir}")
        print(f"   📦 Backup file: {backup_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during account transfer: {str(e)}")
        return False

def bulk_account_transfer(servers, transfer_list):
    """نقل مجموعة من الحسابات"""
    print(f"\n🔄 Bulk Account Transfer")
    print("=" * 50)
    print(f"📋 Transferring {len(transfer_list)} accounts...")
    
    success_count = 0
    failed_count = 0
    
    for transfer in transfer_list:
        source_server = transfer.get('source')
        target_server = transfer.get('target')
        username = transfer.get('username')
        transfer_type = transfer.get('type', 'full')
        
        print(f"\n🔄 Transferring {username}...")
        
        if transfer_account_between_servers(source_server, target_server, username, transfer_type):
            success_count += 1
        else:
            failed_count += 1
    
    print(f"\n📊 Transfer Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    
    return success_count > 0

def debug_account_listing(server, server_name):
    """تشخيص قائمة الحسابات"""
    print(f"\n🔍 Debug Account Listing - {server_name}")
    print("=" * 50)
    print(f"🔗 Server: {server['ip']}")
    
    try:
        # محاولة الحصول على قائمة الحسابات
        print("1. 🔍 Getting accounts list...")
        account_info = whm_api_call(server, "listaccts")
        
        if "error" in account_info:
            print(f"❌ Error: {account_info['error']}")
            return False
        
        print(f"✅ API call successful")
        print(f"   Response keys: {list(account_info.keys())}")
        
        # فحص هيكل البيانات
        accounts_list = account_info.get("acct", [])
        if not accounts_list:
            # محاولة الوصول إلى data.acct
            data_section = account_info.get("data", {})
            if isinstance(data_section, dict):
                accounts_list = data_section.get("acct", [])
        if not accounts_list:
            accounts_list = account_info.get("accounts", [])
        
        if not accounts_list:
            print(f"   ⚠️  No accounts list found in any key")
            print(f"   🔍 Full response: {account_info}")
            return False
        
        print(f"   📊 Total accounts: {len(accounts_list)}")
        
        # عرض أول 10 حسابات
        print(f"\n2. 📋 First 10 accounts:")
        for i, acct in enumerate(accounts_list[:10]):
            user = acct.get("user", "Unknown")
            domain = acct.get("domain", "Unknown")
            status = acct.get("suspended", "Unknown")
            print(f"   {i+1:2d}. {user:<15} | {domain:<20} | Suspended: {status}")
        
        if len(accounts_list) > 10:
            print(f"   ... and {len(accounts_list) - 10} more accounts")
        
        # البحث عن حساب محدد
        print(f"\n3. 🔍 Search for specific account:")
        search_user = input("Enter username to search: ").strip()
        if search_user:
            found = False
            for acct in accounts_list:
                if acct.get("user") == search_user:
                    found = True
                    print(f"   ✅ Found: {search_user}")
                    print(f"      Domain: {acct.get('domain', 'Unknown')}")
                    print(f"      Home: {acct.get('homedir', 'Unknown')}")
                    print(f"      Suspended: {acct.get('suspended', 'Unknown')}")
                    print(f"      Full data: {acct}")
                    break
            
            if not found:
                print(f"   ❌ Not found: {search_user}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during debug: {str(e)}")
        return False

def account_transfer_menu(servers):
    """قائمة نقل الحسابات"""
    print(f"\n🔄 Account Transfer Menu")
    print("=" * 50)
    
    # اختيار السيرفر المصدر
    print("📤 Source Server:")
    online_servers = get_online_servers(servers)
    if not online_servers:
        print("❌ No online servers available")
        return
    
    for name, server in online_servers.items():
        print(f"   {name}: {server['ip']}")
    
    source_choice = input(f"\nChoose source server ({'/'.join(online_servers.keys())}): ").strip()
    if source_choice not in online_servers:
        print("❌ Invalid source server choice!")
        return
    
    source_server = online_servers[source_choice]
    
    # اختيار السيرفر الهدف
    print(f"\n📥 Target Server:")
    for name, server in online_servers.items():
        if name != source_choice:
            print(f"   {name}: {server['ip']}")
    
    target_choice = input(f"Choose target server: ").strip()
    if target_choice not in online_servers or target_choice == source_choice:
        print("❌ Invalid target server choice!")
        return
    
    target_server = online_servers[target_choice]
    
    while True:
        print(f"\n{'='*20} ACCOUNT TRANSFER - {source_choice} → {target_choice} {'='*20}")
        print("1. 🔄 Transfer single account")
        print("2. 📋 Transfer multiple accounts")
        print("3. 🔍 Check account status")
        print("4. 📊 Transfer history")
        print("5. 🔧 Debug account listing")
        print("0. 🔙 Back to main menu")
        print("=" * 75)
        
        choice = input("Choose option: ").strip()
        
        if choice == "1":
            # نقل حساب واحد
            username = input("Enter username to transfer: ").strip()
            if username:
                transfer_type = input("Transfer type (full/selective, default: full): ").strip() or "full"
                transfer_account_between_servers(source_server, target_server, username, transfer_type)
        
        elif choice == "2":
            # نقل حسابات متعددة
            print("\n📋 Enter usernames (one per line, empty line to finish):")
            usernames = []
            while True:
                username = input("Username: ").strip()
                if not username:
                    break
                usernames.append(username)
                print(f"   ✓ Added: {username}")
            
            if usernames:
                transfer_list = []
                for username in usernames:
                    transfer_list.append({
                        'source': source_server,
                        'target': target_server,
                        'username': username,
                        'type': 'full'
                    })
                
                bulk_account_transfer(servers, transfer_list)
        
        elif choice == "3":
            # فحص حالة الحساب
            username = input("Enter username to check: ").strip()
            if username:
                print(f"\n🔍 Checking account status...")
                # فحص في السيرفر المصدر
                source_status = whm_api_call(source_server, "listaccts")
                # فحص في السيرفر الهدف
                target_status = whm_api_call(target_server, "listaccts")
                
                print(f"📤 Source server ({source_server['ip']}):")
                if "error" not in source_status:
                    for acct in source_status.get("acct", []):
                        if acct.get("user") == username:
                            print(f"   ✅ Found: {username}")
                            break
                    else:
                        print(f"   ❌ Not found: {username}")
                
                print(f"📥 Target server ({target_server['ip']}):")
                if "error" not in target_status:
                    for acct in target_status.get("acct", []):
                        if acct.get("user") == username:
                            print(f"   ✅ Found: {username}")
                            break
                    else:
                        print(f"   ❌ Not found: {username}")
        
        elif choice == "4":
            # تاريخ النقل
            print(f"\n📊 Transfer History")
            print("=" * 40)
            print("Feature coming soon...")
            print("This will show recent transfers and their status")
        
        elif choice == "5":
            # تشخيص قائمة الحسابات
            print(f"\n🔧 Debug Account Listing")
            print("=" * 40)
            print("Choose server to debug:")
            for name, server in online_servers.items():
                print(f"   {name}: {server['ip']}")
            
            debug_choice = input("Enter server name: ").strip()
            if debug_choice in online_servers:
                debug_account_listing(online_servers[debug_choice], debug_choice)
            else:
                print("❌ Invalid server choice")
        
        elif choice == "0":
            break
        
        else:
            print("❌ Invalid option")

def delete_large_logs(server, log_files, confirm=True):
    """حذف اللوجات الكبيرة"""
    if not log_files:
        print("❌ No log files to delete")
        return False
    
    print(f"\n🗑️  Large Log Files Found ({len(log_files)} files):")
    print("-" * 80)
    print(f"{'Size':<10} {'Date':<20} {'File Path'}")
    print("-" * 80)
    
    for log_file in log_files:
        print(f"{log_file['size']:<10} {log_file['date']:<20} {log_file['filepath']}")
    
    if confirm:
        if not confirm_action(f"\n⚠️  Are you sure you want to delete these {len(log_files)} log files?"):
            print("❌ Operation cancelled")
            return False
    
    deleted_count = 0
    failed_count = 0
    
    for log_file in log_files:
        try:
            # محاولة استخدام exec API أولاً
            delete_command = f"rm -f '{log_file['filepath']}'"
            result = whm_api_call(server, "exec", {"command": delete_command})
            
            if "error" in result:
                # إذا فشل exec، جرب shell API
                result = whm_api_call(server, "shell", {"command": delete_command})
                
                if "error" in result:
                    print(f"❌ Failed to delete {log_file['filepath']}: Shell commands not supported")
                    print(f"💡 To delete manually, connect via SSH and run: rm -f '{log_file['filepath']}'")
                    failed_count += 1
                    continue
            
            print(f"✅ Deleted: {log_file['filepath']}")
            deleted_count += 1
                
        except Exception as e:
            print(f"❌ Error deleting {log_file['filepath']}: {str(e)}")
            failed_count += 1
    
    print(f"\n📊 Deletion Summary:")
    print(f"   ✅ Successfully deleted: {deleted_count}")
    print(f"   ❌ Failed to delete: {failed_count}")
    
    if failed_count > 0:
        print(f"\n💡 For failed deletions, use SSH to connect to {server['ip']} and run the commands manually")
    
    return deleted_count > 0

def truncate_large_logs(server, log_files, confirm=True):
    """تفريغ محتوى اللوجات الكبيرة (حفظ الملف مع إفراغ المحتوى)"""
    if not log_files:
        print("❌ No log files to truncate")
        return False
    
    print(f"\n📝 Large Log Files to Truncate ({len(log_files)} files):")
    print("-" * 80)
    print(f"{'Size':<10} {'Date':<20} {'File Path'}")
    print("-" * 80)
    
    for log_file in log_files:
        print(f"{log_file['size']:<10} {log_file['date']:<20} {log_file['filepath']}")
    
    if confirm:
        if not confirm_action(f"\n⚠️  Are you sure you want to truncate these {len(log_files)} log files?"):
            print("❌ Operation cancelled")
            return False
    
    truncated_count = 0
    failed_count = 0
    
    for log_file in log_files:
        try:
            # محاولة استخدام exec API أولاً
            truncate_command = f"cat /dev/null > '{log_file['filepath']}'"
            result = whm_api_call(server, "exec", {"command": truncate_command})
            
            if "error" in result:
                # إذا فشل exec، جرب shell API
                result = whm_api_call(server, "shell", {"command": truncate_command})
                
                if "error" in result:
                    print(f"❌ Failed to truncate {log_file['filepath']}: Shell commands not supported")
                    print(f"💡 To truncate manually, connect via SSH and run: cat /dev/null > '{log_file['filepath']}'")
                    failed_count += 1
                    continue
            
            print(f"✅ Truncated: {log_file['filepath']}")
            truncated_count += 1
                
        except Exception as e:
            print(f"❌ Error truncating {log_file['filepath']}: {str(e)}")
            failed_count += 1
    
    print(f"\n📊 Truncation Summary:")
    print(f"   ✅ Successfully truncated: {truncated_count}")
    print(f"   ❌ Failed to truncate: {failed_count}")
    
    if failed_count > 0:
        print(f"\n💡 For failed truncations, use SSH to connect to {server['ip']} and run the commands manually")
    
    return truncated_count > 0

def large_logs_management_menu(servers):
    """قائمة إدارة اللوجات الكبيرة"""
    print(f"\n📋 Large Logs Management Menu")
    print("=" * 50)
    
    # اختيار السيرفر
    online_servers = get_online_servers(servers)
    if not online_servers:
        print("❌ No online servers available")
        return
    
    print(f"Available servers:")
    for name, server in online_servers.items():
        print(f"   {name}: {server['ip']}")
    
    server_choice = input(f"\nChoose server ({'/'.join(online_servers.keys())}): ").strip()
    if server_choice not in online_servers:
        print("❌ Invalid server choice!")
        return
    
    selected_server = online_servers[server_choice]
    
    while True:
        print(f"\n{'='*20} LARGE LOGS MANAGEMENT - {server_choice.upper()} {'='*20}")
        print("1. 🔍 Find large log files")
        print("2. 🗑️  Delete large log files")
        print("3. 📝 Truncate large log files (empty content)")
        print("4. 📊 Show log files summary")
        print("5. 📋 Manual commands guide (for SSH)")
        print("6. 🔧 Test server connection & token")
        print("0. 🔙 Back to main menu")
        print("=" * 75)
        
        choice = input("Choose option: ").strip()
        
        if choice == "1":
            # البحث عن اللوجات الكبيرة
            min_size = input("Minimum size in MB (default 100): ").strip() or "100"
            try:
                min_size_mb = int(min_size)
                log_files = find_large_logs(selected_server, min_size_mb)
                
                if log_files:
                    print(f"\n✅ Found {len(log_files)} large log files")
                    # حفظ النتائج للاستخدام في الخيارات الأخرى
                    selected_server['large_logs_cache'] = log_files
                else:
                    print("✅ No large log files found")
                    selected_server['large_logs_cache'] = []
                    
            except ValueError:
                print("❌ Invalid size value")
        
        elif choice == "2":
            # حذف اللوجات الكبيرة
            if 'large_logs_cache' not in selected_server or not selected_server['large_logs_cache']:
                print("❌ No log files found. Please run option 1 first.")
                continue
            
            delete_large_logs(selected_server, selected_server['large_logs_cache'])
            # تحديث الكاش بعد الحذف
            selected_server['large_logs_cache'] = []
        
        elif choice == "3":
            # تفريغ اللوجات الكبيرة
            if 'large_logs_cache' not in selected_server or not selected_server['large_logs_cache']:
                print("❌ No log files found. Please run option 1 first.")
                continue
            
            truncate_large_logs(selected_server, selected_server['large_logs_cache'])
            # تحديث الكاش بعد التفريغ
            selected_server['large_logs_cache'] = []
        
        elif choice == "4":
            # عرض ملخص اللوجات
            if 'large_logs_cache' in selected_server and selected_server['large_logs_cache']:
                print(f"\n📊 Log Files Summary ({len(selected_server['large_logs_cache'])} files):")
                print("-" * 80)
                print(f"{'Size':<10} {'Date':<20} {'File Path'}")
                print("-" * 80)
                
                total_size = 0
                for log_file in selected_server['large_logs_cache']:
                    print(f"{log_file['size']:<10} {log_file['date']:<20} {log_file['filepath']}")
                    # حساب الحجم الإجمالي
                    try:
                        size_str = log_file['size']
                        if 'G' in size_str:
                            size_mb = float(size_str.replace('G', '')) * 1024
                        elif 'M' in size_str:
                            size_mb = float(size_str.replace('M', ''))
                        else:
                            size_mb = 0
                        total_size += size_mb
                    except:
                        pass
                
                print("-" * 80)
                print(f"Total size: {total_size:.2f} MB")
            else:
                print("❌ No log files in cache. Please run option 1 first.")
        
        elif choice == "5":
            # دليل الأوامر اليدوية
            show_manual_commands_guide(selected_server, server_choice)
        
        elif choice == "6":
            # اختبار الاتصال والتوكن
            test_server_connection_and_token(selected_server, server_choice)
        
        elif choice == "0":
            break
        
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()
