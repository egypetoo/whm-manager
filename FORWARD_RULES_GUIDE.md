# 📤 دليل إدارة Forward Rules في WHM Email Manager

## 🎯 ما هي Forward Rules؟
Forward Rules هي قواعد تسمح بإعادة توجيه الإيميلات الواردة إلى إيميل آخر. مثال:
- `info@company.com` → `manager@company.com`
- `support@company.com` → `team1@company.com, team2@company.com`

## 🚀 كيفية الوصول للميزة

### 1. تشغيل السكريبت
```bash
python3 email_management_script.py
```

### 2. اختيار الخيار 6
```
6.  📤 Manage email forward rules
```

### 3. إدخال الدومين
```
🌐 Enter domain: be-group.com
```

## 📋 الميزات المتاحة

### 1. 📋 List all forward rules
- عرض جميع قواعد إعادة التوجيه للدومين
- يظهر: الإيميل المصدر → الإيميل الهدف + الحالة

### 2. ➕ Add new forward rule
- إضافة قاعدة إعادة توجيه جديدة
- خيارات:
  - **Keep copy**: الاحتفاظ بنسخة في الصندوق الأصلي
  - **Delete**: حذف الإيميل من الصندوق الأصلي

### 3. ✏️ Edit forward rule
- تعديل قاعدة موجودة
- تغيير الإيميل الهدف

### 4. 🗑️ Delete forward rule
- حذف قاعدة إعادة توجيه
- تأكيد قبل الحذف

### 5. 📊 Export forward rules report
- تصدير تقرير مفصل بصيغة TXT
- يحتوي على جميع القواعد مع التفاصيل

### 6. 🔍 Search forward rules
- البحث في القواعد
- البحث بالإيميل المصدر أو الهدف

## 📊 عرض Forward Rules في تقرير الإيميلات

عند اختيار **خيار 5 (List & export emails)**، ستجد عمود جديد:

```
#   Email Address                       Quota        Used         Usage %   Forward                    
-------------------------------------------------------------------------------------
1   info@be-group.com                   Unlimited    0MB          0.0%      → manager@be-group.com    
2   support@be-group.com                Unlimited    0MB          0.0%      → team@be-group.com       
3   sales@be-group.com                  Unlimited    0MB          0.0%      No Forward                
```

## 📁 ملفات التصدير

### تقرير الإيميلات (يشمل Forward Rules)
- **Excel**: `emails_be-group_com_20241201_143022.xlsx`
- **CSV**: `emails_be-group_com_20241201_143022.csv`

### تقرير Forward Rules فقط
- **TXT**: `forward_rules_be-group_com_20241201_143022.txt`

## 🔧 أمثلة عملية

### مثال 1: إعادة توجيه info@ إلى مدير
```
📧 Enter email address: info@be-group.com
📤 Forward to: manager@be-group.com
🔧 Additional Options:
1. Keep copy in original mailbox
2. Delete from original mailbox
Choose option: 1
```

### مثال 2: إعادة توجيه support@ إلى فريق متعدد
```
📧 Enter email address: support@be-group.com
📤 Forward to: team1@be-group.com, team2@be-group.com
```

## ⚠️ ملاحظات مهمة

1. **التحقق من صحة الإيميل**: يجب أن يكون الإيميل المصدر من نفس الدومين
2. **الإيميل الهدف**: يمكن أن يكون أي إيميل صحيح
3. **النسخ**: اختر "Keep copy" إذا كنت تريد الاحتفاظ بنسخة في الصندوق الأصلي
4. **الحذف**: اختر "Delete" إذا كنت تريد حذف الإيميل من الصندوق الأصلي

## 🎉 الفوائد

- ✅ **سهولة الإدارة**: إدارة مركزية لقواعد إعادة التوجيه
- ✅ **المرونة**: إضافة/تعديل/حذف القواعد بسهولة
- ✅ **التتبع**: معرفة أي إيميل يتبع لأي قاعدة
- ✅ **التصدير**: تقارير مفصلة بصيغ مختلفة
- ✅ **البحث**: البحث السريع في القواعد

## 🆘 استكشاف الأخطاء

### مشكلة: "Error fetching forward rules"
- تأكد من صحة بيانات الدخول
- تحقق من صلاحيات cPanel

### مشكلة: "Email must be a valid address from domain"
- تأكد من أن الإيميل ينتمي للدومين المحدد
- مثال صحيح: `info@be-group.com`

### مشكلة: "Forward address must be a valid email"
- تأكد من صحة الإيميل الهدف
- يجب أن يحتوي على @

---

**تم تطوير هذه الميزة بواسطة WHM Email Management Script** 🚀
