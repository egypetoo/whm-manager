# 🚀 WHM Manager Scripts

مجموعة شاملة من السكريبتات لإدارة خوادم WHM/cPanel مع ميزات متقدمة للمراقبة والصيانة.

## 📋 الميزات الرئيسية

### 1. 📋 ACCOUNTS & DOMAINS MANAGEMENT
- إدارة حسابات cPanel
- إدارة النطاقات
- مراقبة استخدام الموارد
- تحليل الأمان

### 2. 📧 EMAIL MANAGEMENT & MONITORING ⭐ **NEW FEATURES!**
- إنشاء وحذف حسابات الإيميل
- تغيير كلمات المرور (مفردة أو مجمعة)
- **📤 إدارة Forward Rules** 🆕
  - إضافة/تعديل/حذف قواعد إعادة التوجيه
  - البحث في القواعد
  - تصدير تقارير مفصلة
  - عرض Forward Rules في تقارير الإيميلات
- مراقبة صحة الإيميلات
- كشف الحسابات المشبوهة
- فحص قوائم الحظر
- مراقبة قوائم البريد

### 3. 🖥️ SERVER MONITORING & SITE CHECK
- مراقبة حالة الخوادم
- فحص المواقع
- تحليل الأداء

### 4. 🔧 SERVER STATUS CHECK
- فحص حالة الخوادم
- مراقبة الموارد

### 5. 📊 VIEW LOGS
- عرض سجلات العمليات
- تحليل الأخطاء

## 🆕 الميزات الجديدة - Forward Rules Management

### 📤 ما هي Forward Rules؟
قواعد تسمح بإعادة توجيه الإيميلات الواردة إلى إيميل آخر. مثال:
- `info@company.com` → `manager@company.com`
- `support@company.com` → `team@company.com`

### 🎯 الميزات المتاحة
- ✅ **إضافة قواعد جديدة** مع خيارات النسخ
- ✅ **تعديل القواعد الموجودة**
- ✅ **حذف القواعد** مع تأكيد
- ✅ **البحث في القواعد**
- ✅ **تصدير تقارير مفصلة**
- ✅ **عرض Forward Rules في تقارير الإيميلات**

### 📊 مثال على التقرير المحسن
```
#   Email Address                       Quota        Used         Usage %   Forward                    
-------------------------------------------------------------------------------------
1   info@be-group.com                   Unlimited    0MB          0.0%      → manager@be-group.com    
2   support@be-group.com                Unlimited    0MB          0.0%      → team@be-group.com       
3   sales@be-group.com                  Unlimited    0MB          0.0%      No Forward                
```

## 🚀 كيفية الاستخدام

### 1. تشغيل السكريبت الرئيسي
```bash
python3 run_script.py
```

### 2. اختيار السكريبت المطلوب
```
1. 📋 ACCOUNTS & DOMAINS MANAGEMENT
2. 📧 EMAIL MANAGEMENT & MONITORING
3. 🖥️ SERVER MONITORING & SITE CHECK
4. 🔧 SERVER STATUS CHECK
5. 📊 VIEW LOGS
```

### 3. الوصول لميزة Forward Rules
```
2. 📧 EMAIL MANAGEMENT & MONITORING
6. 📤 Manage email forward rules
```

## 📁 ملفات الدليل

- 📖 `FORWARD_RULES_GUIDE.md` - دليل شامل لإدارة Forward Rules
- 📖 `EMAIL_USAGE_FIX_GUIDE.md` - دليل إصلاح مشاكل استخدام الإيميل
- 📖 `PASSWORD_DISPLAY_GUIDE.md` - دليل عرض كلمات المرور
- 📖 `DOMAIN_ANALYSIS_GUIDE.md` - دليل تحليل النطاقات

## 🔧 المتطلبات

- Python 3.7+
- مكتبات Python المطلوبة (سيتم تثبيتها تلقائياً)
- وصول SSH للخوادم
- صلاحيات cPanel/WHM

## 📦 التثبيت

```bash
# استنساخ المستودع
git clone <repository-url>
cd whm-manager

# إنشاء البيئة الافتراضية
python3 -m venv venv
source venv/bin/activate

# تشغيل السكريبت
python3 run_script.py
```

## 🎯 حالات الاستخدام

### للمديرين
- مراقبة شاملة لجميع الخوادم
- تقارير مفصلة عن الموارد
- إدارة مركزية للحسابات

### لمدراء النظام
- مراقبة الأداء والصحة
- كشف المشاكل مبكراً
- صيانة استباقية

### لمدراء الإيميلات
- إدارة Forward Rules بسهولة
- مراقبة صحة الإيميلات
- كشف الحسابات المشبوهة

## 🆘 الدعم

- 📖 راجع ملفات الدليل المرفقة
- 🔍 ابحث في الكود عن حلول
- 📧 تواصل مع فريق التطوير

## 🎉 المميزات

- 🚀 **سهولة الاستخدام**: واجهة بسيطة وواضحة
- 🔒 **الأمان**: تشفير البيانات والاتصالات
- 📊 **التقارير**: تصدير بصيغ متعددة
- 🔍 **البحث**: بحث سريع في البيانات
- 📱 **التوافق**: يعمل على جميع الأنظمة

---

**تم تطوير هذه المجموعة بواسطة فريق WHM Manager** 🚀
