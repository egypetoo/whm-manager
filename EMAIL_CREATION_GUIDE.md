# 📧 دليل إنشاء الإيميلات الجديدة - WHM Manager

## 🎉 تم تحديث إنشاء الإيميلات بنجاح!

### ✅ **ما تم تغييره:**

**قبل التحديث:**
```
📧 Email prefix (before @): heba
Enter password: 
💾 Quota in MB (default: 250): 
```

**بعد التحديث:**
```
📧 Email prefix (before @): heba

🔑 Password Options:
1. Enter password manually
2. Generate random strong password
Choose option [1/2]: 2

✅ Generated strong password: vaX0$hG#%y6h
💾 Quota in MB (default: 250): 
```

## 🚀 **الخيارات الجديدة لكلمة المرور:**

### **1. 📝 إدخال كلمة مرور يدوياً:**
- **الخيار 1**: إدخال كلمة مرور يدوياً
- **التحقق**: تأكيد كلمة المرور
- **المتطلبات**: 8 أحرف على الأقل
- **الأمان**: كلمة مرور مخصصة

### **2. 🎲 توليد كلمة مرور عشوائية:**
- **الخيار 2**: توليد كلمة مرور قوية تلقائياً
- **الطول**: 16 حرف
- **الأمان**: كلمة مرور معقدة وقوية
- **السهولة**: لا حاجة للتذكر

## 📊 **مقارنة الخيارات:**

| الخيار | الطول | الأمان | السهولة | الاستخدام |
|--------|--------|--------|----------|-----------|
| **1. يدوي** | 8+ أحرف | ⭐⭐⭐⭐ | ⭐⭐⭐ | كلمات مرور مخصصة |
| **2. عشوائي** | 16 حرف | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | أمان عالي |

## 🔧 **أين تجد هذه الميزة:**

### **1. 📧 إنشاء إيميل واحد:**
- **القائمة الرئيسية** → **خيار 2** (إدارة الإيميلات)
- **خيار 1** (Create single email account)
- **أدخل الدومين** (مثل: egypetoo.com)
- **أدخل بادئة الإيميل** (مثل: heba)
- **اختر خيار كلمة المرور**

### **2. 📧 إنشاء إيميلات متعددة:**
- **القائمة الرئيسية** → **خيار 2** (إدارة الإيميلات)
- **خيار 2** (Bulk create emails)
- **أدخل الدومين**
- **أدخل الإيميلات بالتنسيق**: `prefix,password,quota`

## 📱 **أمثلة عملية:**

### **مثال 1: إنشاء إيميل واحد مع كلمة مرور عشوائية**
```
📧 Create Single Email Account
==================================================
🌐 Enter domain: egypetoo.com

🔍 Searching for domain: egypetoo.com...

✅ Domain found on Server 93
📋 Domain: egypetoo.com
👤 cPanel User: egypetoo

📧 Email prefix (before @): heba

🔑 Password Options:
1. Enter password manually
2. Generate random strong password
Choose option [1/2]: 2

✅ Generated strong password: vaX0$hG#%y6h
💾 Quota in MB (default: 250): 500

📋 Email Details:
   Email: heba@egypetoo.com
   Password Length: 16 characters
   Quota: 500MB
   Server: 93

Create email account heba@egypetoo.com? (y/N): y

✅ Email account created successfully!
==================================================
📧 Email Address: heba@egypetoo.com
🌐 Domain: egypetoo.com
👤 Username: heba
🔑 Password: vaX0$hG#%y6h
💾 Quota: 500MB
💻 Webmail URL: https://webmail.egypetoo.com
🖥️  Server: 93 (184.168.1.93)
==================================================
```

### **مثال 2: إنشاء إيميل واحد مع كلمة مرور يدوية**
```
📧 Email prefix (before @): admin

🔑 Password Options:
1. Enter password manually
2. Generate random strong password
Choose option [1/2]: 1

Enter password: mySecurePassword123
Enter password: mySecurePassword123

💾 Quota in MB (default: 250): 1000

📋 Email Details:
   Email: admin@egypetoo.com
   Password Length: 22 characters
   Quota: 1000MB
   Server: 93

Create email account admin@egypetoo.com? (y/N): y

✅ Email account created successfully!
==================================================
📧 Email Address: admin@egypetoo.com
🌐 Domain: egypetoo.com
👤 Username: admin
🔑 Password: mySecurePassword123
💾 Quota: 1000MB
💻 Webmail URL: https://webmail.egypetoo.com
🖥️  Server: 93 (184.168.1.93)
==================================================
```

## 📈 **الفوائد الجديدة:**

### **✅ مرونة في كلمات المرور:**
- خيار إدخال كلمة مرور مخصصة
- خيار توليد كلمة مرور قوية تلقائياً
- تحقق من قوة كلمة المرور

### **✅ أمان محسن:**
- كلمات مرور بطول 16 حرف
- متطلبات أمان (8 أحرف على الأقل)
- تأكيد كلمة المرور

### **✅ عرض منظم:**
- معلومات شاملة عن الإيميل المُنشأ
- روابط مباشرة للويب ميل
- تفاصيل السيرفر والحصة

### **✅ سهولة الاستخدام:**
- خيارات واضحة وبسيطة
- رسائل تأكيد مفصلة
- عرض النتائج بتنسيق جميل

## 🎯 **كيفية الاستخدام:**

### **1. إنشاء إيميل واحد:**
```bash
whm-manager
# اختر 2 (إدارة الإيميلات)
# اختر 1 (Create single email account)
# أدخل الدومين
# أدخل بادئة الإيميل
# اختر خيار كلمة المرور
# أدخل الحصة
# أكد الإنشاء
```

### **2. إنشاء إيميلات متعددة:**
```bash
whm-manager
# اختر 2 (إدارة الإيميلات)
# اختر 2 (Bulk create emails)
# أدخل الدومين
# أدخل الإيميلات بالتنسيق
# أكد الإنشاء
```

## 🔒 **نصائح الأمان:**

### **✅ لكلمات المرور اليدوية:**
- استخدم 8 أحرف على الأقل
- ادمج أحرف كبيرة وصغيرة
- أضف أرقام ورموز خاصة
- تجنب المعلومات الشخصية

### **✅ لكلمات المرور العشوائية:**
- احفظها في مكان آمن
- استخدم مدير كلمات المرور
- لا تشاركها مع أحد
- غيّرها دورياً

## 🎉 **النتيجة النهائية:**

الآن يمكنك:
- ✅ **اختيار طريقة كلمة المرور** (يدوية أو عشوائية)
- ✅ **إنشاء إيميلات آمنة** بكلمات مرور قوية
- ✅ **رؤية النتائج منظمة** بتنسيق جميل
- ✅ **الوصول المباشر** للويب ميل
- ✅ **إدارة الحصص** بسهولة

**إنشاء الإيميلات أصبح أكثر أماناً وسهولة!** 🚀
