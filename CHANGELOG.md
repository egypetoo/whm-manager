# 📋 CHANGELOG - WHM Manager Scripts

## [Unreleased] - 2025-01-XX

### 🆕 Added
- **Large Logs Management Feature** - ميزة إدارة اللوجات الكبيرة
  - 🔍 البحث عن اللوجات الكبيرة في السيرفرات
  - 🗑️ حذف اللوجات الكبيرة مع تأكيد
  - 📝 تفريغ محتوى اللوجات الكبيرة (حفظ الملف مع إفراغ المحتوى)
  - 📊 عرض ملخص اللوجات مع حساب الحجم الإجمالي
  - 🔒 حماية إضافية مع تأكيد جميع العمليات الخطرة
  - 📋 قائمة إدارة منفصلة للوجات الكبيرة

### 🔧 Technical Improvements
- إضافة دالة `find_large_logs()` للبحث عن اللوجات الكبيرة
- إضافة دالة `delete_large_logs()` لحذف اللوجات الكبيرة
- إضافة دالة `truncate_large_logs()` لتفريغ محتوى اللوجات
- إضافة دالة `large_logs_management_menu()` لقائمة الإدارة
- إضافة دالة `show_manual_commands_guide()` لدليل SSH
- تحديث القائمة الرئيسية مع الخيار الجديد (17)
- إضافة دعم WHM API v1 مع حلول بديلة

### 🔄 Account Transfer Functions
- إضافة دالة `transfer_account_between_servers()` للنقل الفردي
- إضافة دالة `bulk_account_transfer()` للنقل الجماعي
- إضافة دالة `account_transfer_menu()` لقائمة النقل
- تحديث القائمة الرئيسية مع الخيار الجديد (18)
- نظام نقل آلي مع نسخ احتياطية

### 📚 Documentation
- إنشاء ملف `LARGE_LOGS_MANAGEMENT.md` مع دليل شامل
- إنشاء ملف `demo_large_logs.py` للعرض التوضيحي
- إنشاء ملف `ACCOUNT_TRANSFER_GUIDE.md` مع دليل شامل
- تحديث هذا الملف CHANGELOG

### 🎯 Features
- البحث في مجلدات متعددة: `/home`, `/var/log`, `/usr/local/apache/logs`, `/usr/local/cpanel/logs`
- دعم تحديد الحد الأدنى للحجم (افتراضي: 100 ميجابايت)
- كاش ذكي لحفظ نتائج البحث للاستخدام في العمليات اللاحقة
- تقارير مفصلة لجميع العمليات
- معالجة الأخطاء والاستثناءات

### ⚠️ Security & Safety
- تأكيد إجباري لجميع عمليات الحذف والتفريغ
- تحقق من الصلاحيات قبل تنفيذ العمليات
- رسائل تحذير واضحة للمستخدمين
- إمكانية إلغاء العمليات في أي وقت

### 🔄 WHM API Compatibility
- **WHM API v1**: دعم محدود مع حلول بديلة
- **WHM API v2+**: دعم كامل لجميع الميزات
- **Fallback Methods**: اكتشاف تلقائي للإصدارات المدعومة
- **SSH Guide**: دليل مفصل للعمليات اليدوية

### 🆕 Account Transfer System
- **نقل الحسابات بين السيرفرات**: نظام آلي كامل
- **نقل فردي وجماعي**: دعم نقل حساب واحد أو مجموعة
- **نسخ احتياطية تلقائية**: حماية البيانات أثناء النقل
- **فحص حالة الحسابات**: تأكيد نجاح النقل
- **إدارة الأخطاء**: حلول بديلة عند فشل API

---

## [Previous Versions]
- Initial release with basic WHM management features
- Server monitoring and health check capabilities
- Account and domain management tools
- Email management and analysis features
