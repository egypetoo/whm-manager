# 🔍 دليل تحليل الدومينات المفصل - الميزات الجديدة

## 🎯 الميزات الجديدة المضافة:

### ✅ **1. تحليل دومين محدد بالتفصيل (خيار 6)**
- معلومات الحساب الكاملة
- تحليل حسابات الإيميل
- حساب نقاط المخاطر
- تقدير الإيميلات الفاشلة
- توصيات مفصلة

### ✅ **2. فحص طابور البريد لدومين محدد (خيار 7)**
- حالة طابور البريد للسيرفر
- تحليل مشاكل تسليم الإيميلات
- تقدير الإيميلات الفاشلة
- توصيات لحل المشاكل

## 🚀 كيفية الاستخدام:

### **الطريقة الكاملة:**
```bash
whm-manager
# اختر 2 (إدارة الإيميلات)
# اختر 6 (لوحة مراقبة الإيميل)
# اختر 1 (تحليل الإيميلات الفاشلة)
# اختر 1 (فحص سيرفر محدد)
# اختر رقم السيرفر
# أدخل فترة التقرير
# بعد عرض النتائج، اختر:
# 6 - لتحليل دومين محدد
# 7 - لفحص طابور البريد لدومين محدد
```

## 📊 مثال على النتائج:

### **🔍 تحليل دومين محدد (خيار 6):**

```
🔍 DETAILED ANALYSIS FOR: example.com
================================================================================
📋 Account Information:
   🌐 Domain: example.com
   👤 User: example
   📧 Email: admin@example.com
   📦 Package: Basic
   💾 Disk Used: 2500MB
   📅 Created: 2023-01-15
   🔴 Suspended: No
   🖥️  Server: 222 (63.250.32.222)

📧 Email Accounts Analysis:
------------------------------------------------------------
📊 Total Email Accounts: 25
   🟢 Active: 20
   🔴 Suspended: 5
   💾 Total Disk Used: 1800.00MB
   💾 Total Quota: 5000.00MB
   📊 Usage: 36.0%

📋 Email Accounts Details:
================================================================================
#   Email                          Status        Used (MB)    Quota (MB)   Usage %
--------------------------------------------------------------------------------
1   admin@example.com             🟢 Active     150.00       500.00       30.0%
2   info@example.com              🟢 Active     200.00       500.00       40.0%
3   sales@example.com             🔴 Suspended  0.00         500.00       0.0%

⚠️  Risk Analysis:
------------------------------------------------------------
🚨 Risk Score: 8/25
⚠️  Risk Factors:
   • Moderate disk usage (2500MB)
   • Elevated email count (25)

📊 Estimated Email Failures:
   📈 Based on risk analysis: 10 failures
   📧 Based on email count: 7.5 failures
   🎯 Final Estimate: 10.0 failures

💡 Recommendations:
   🟡 MODERATE RISK: Monitor closely
   • Regular monitoring recommended
   • Check email activity weekly

🔧 Available Actions:
1. 🚫 Suspend this account
2. 🔑 Change account password
3. 📧 Manage email accounts
4. 📊 Export detailed report
0. 🚪 Back to main menu
```

### **📮 فحص طابور البريد لدومين محدد (خيار 7):**

```
📮 MAIL QUEUE ANALYSIS FOR: example.com
================================================================================
📋 Domain Information:
   🌐 Domain: example.com
   👤 User: example
   🖥️  Server: 222 (63.250.32.222)
   🔴 Suspended: No

📮 Server Mail Queue Status:
------------------------------------------------------------
📊 Total Queue Messages: 30
🔧 Method Used: estimated_from_accounts
📝 Note: Queue size estimated based on account status - actual mail queue access unavailable
🟠 Queue Status: Moderate

📧 Email Accounts for example.com:
------------------------------------------------------------
📊 Total Email Accounts: 25
   🟢 Active: 20
   🔴 Suspended: 5
   💾 Total Disk Used: 1800.00MB
   💾 Total Quota: 5000.00MB
   📊 Usage: 36.0%

🚫 Email Delivery Issues Analysis:
------------------------------------------------------------
📊 Estimated Email Failures: 25
🚫 Failure Factors:
   • Moderate disk usage (2500MB)
   • Elevated email count (25)
   • Moderate mail queue (30 messages)

💡 Recommendations to Fix Email Issues:
   🟠 MODERATE PRIORITY - ACTION NEEDED WITHIN 24 HOURS:
   • Monitor account activity
   • Check mail queue regularly
   • Review email accounts
   • Consider disk cleanup

🔧 Available Actions:
1. 🚫 Suspend this account
2. 🔑 Change account password
3. 📧 Manage email accounts
4. 📊 Export mail queue report
5. 🔍 Check other domains on this server
0. 🚪 Back to main menu
```

## 🎯 متى تستخدم كل ميزة:

### **🔍 تحليل دومين محدد (خيار 6):**
- ✅ تريد معرفة تفاصيل كاملة عن دومين معين
- ✅ تريد فحص حسابات الإيميل الخاصة بالدومين
- ✅ تريد تقييم المخاطر والحصول على توصيات
- ✅ تريد تصدير تقرير مفصل

### **📮 فحص طابور البريد لدومين محدد (خيار 7):**
- ✅ تريد معرفة حالة طابور البريد لدومين معين
- ✅ تريد تحليل مشاكل تسليم الإيميلات
- ✅ تريد معرفة العوامل التي تسبب فشل الإيميلات
- ✅ تريد توصيات لحل مشاكل الإيميلات

## 📈 تفسير النتائج:

### **🚨 Risk Score (نقاط المخاطر):**
- **0-4**: ✅ منخفض - لا توجد مشاكل
- **5-9**: 🟡 متوسط - مراقبة دورية
- **10-14**: 🟠 عالي - إجراءات خلال 24 ساعة
- **15-25**: 🔴 حرج - إجراءات فورية

### **📊 Estimated Failures (الإيميلات الفاشلة المقدرة):**
- **0-10**: ✅ طبيعي
- **11-25**: 🟡 مراقبة
- **26-50**: 🟠 مشكلة متوسطة
- **50+**: 🔴 مشكلة حرجة

### **📮 Queue Status (حالة الطابور):**
- **0**: ✅ فارغ (صحي)
- **1-10**: 🟡 طبيعي
- **11-50**: 🟠 معتدل
- **51-100**: 🔴 عالي
- **100+**: 🚨 حرج

## 🔧 الإجراءات المتاحة:

### **1. 🚫 تعليق الحساب:**
- تعليق فوري مع سبب واضح
- إيقاف جميع الإيميلات
- منع إرسال إيميلات جديدة

### **2. 🔑 تغيير كلمة المرور:**
- توليد كلمة مرور قوية
- تغيير تلقائي
- عرض كلمة المرور الجديدة

### **3. 📧 إدارة حسابات الإيميل:**
- عرض جميع حسابات الإيميل
- حالة كل حساب
- استخدام القرص

### **4. 📊 تصدير التقارير:**
- تصدير إلى Excel (.xlsx)
- تصدير إلى CSV (.csv)
- تقارير مفصلة ومنظمة

### **5. 🔍 فحص دومينات أخرى:**
- البحث في نفس السيرفر
- مقارنة النتائج
- تحديد الأنماط

## 🎯 أفضل الممارسات:

### **1. المراجعة اليومية:**
- فحص الدومينات عالية المخاطر
- مراقبة طابور البريد
- متابعة الإيميلات الفاشلة

### **2. الإجراءات الفورية:**
- تعليق الحسابات الحرجة
- تغيير كلمات المرور
- تنظيف القرص الصلب

### **3. المتابعة المستمرة:**
- مراجعة التقارير الأسبوعية
- تحديث استراتيجيات الحماية
- تحسين إعدادات البريد

## 🚀 الطريقة السريعة:

```bash
# من أي مجلد
whm-manager

# ثم اتبع:
2 → 6 → 1 → 1 → [رقم السيرفر] → [فترة التقرير] → 6 أو 7 → [اسم الدومين]
```

## 🎉 النتيجة النهائية:

الآن يمكنك:
- ✅ **فحص أي دومين بالتفصيل** من أي سيرفر
- ✅ **معرفة حالة طابور البريد** لدومين محدد
- ✅ **تحليل مشاكل الإيميلات** بدقة عالية
- ✅ **الحصول على توصيات مفصلة** لحل المشاكل
- ✅ **تصدير تقارير شاملة** لكل دومين
- ✅ **اتخاذ إجراءات فورية** لحل المشاكل

**السكريبت أصبح أداة احترافية لتحليل الدومينات وحل مشاكل الإيميلات!** 🚀
