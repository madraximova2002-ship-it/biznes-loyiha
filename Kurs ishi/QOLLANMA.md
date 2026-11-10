# Ombor Boshqaruv Tizimi (Inventory Management System)
## To'liq Foydalanish Qo'llanmasi 🚀

Bu loyiha har qanday korxona yoki kichik va o'rta bizneslar uchun ombor jarayonlarini to'liq raqamlashtiruvchi zamonaviy dastur hisoblanadi.

---

### 1. Tizim Asoslari va O'rnatish

Tizim ishlashi uchun kerak bo'ladigan kutubxonalar va texnologiyalar:
* **Asosiy Fraymvork:** Python va Django 6
* **Texnologiyalar:** HTML5, CSS3, JavaScript (Vanilla), SQLite
* **Ishlatilgan Kutubxonalar (Libraries):**
  * `openpyxl`: Excel fayllarni yuklash (Export) va bazaga yozish (Import) uchun.
  * `xhtml2pdf`: Qog'oz cheklari (Invoice) va hisobotlarni PDF shaklda generatsiya qilish.
  * `Pillow` & `reportlab`: Rasm va PDF ishlash imkoniyatlari.

**O'rnatish:**
1. Loyiha papkasiga kiring: `cd "c:\Users\DELL PC\Desktop\Kurs ishi"`
2. Talab qilinadigan kutubxonalarni o'rnating: `pip install -r requirements.txt`
3. Ma'lumotlar bazasini yangilang: `python manage.py migrate`
4. Serverni ishga tushiring: `python manage.py runserver`
5. Brauzer orqali `http://127.0.0.1:8000/` manziliga kiring.

---

### 2. Rollar va Huquqlar

Tizimda barchaning vazifasi chegaralangan. Qaysi xodim tizimga kirganiga qarab quyidagi vakolatlarga ega:
* **Admin (Boshqaruvchi):** Hamma funksiyalarga ruxsati bor. Foydalanuvchi qo'shish, o'chirish, tahlil qilish, hamda tizim Audit logini ko'rish.
* **Manager (Ombor mudiri):** Ombor, tovar va yetkazib beruvchilarni boshqaradi, tranzaksiyalar (Kirim/Chiqim) ni tasdiqlaydi.
* **Analyst (Tahlilchi):** Faqat `Analitika` va `Prognoz` bo'limlarini ko'rib, jadvallar yasaydi, kelajakni tahlil qiladi (Lekin u mol qo'sha olmaydi yoki o'chira olmaydi).
* **Observer (Kuzatuvchi):** Faqat natijalarni ekrandan tomosha qiladigan huquqi cheklangan shaxs.

---

### 3. Asosiy Bo'limlar va Qanday Ishlatiladi?

#### 📊 Boshqaruv paneli (Dashboard)
Kirishingiz bilan umumiy moliyaviy hisobot va diagrammalar yuzingizga chiqadi. 
* **Tun/Kun rejimi:** Tepadagi 🌓 belgisini bossangiz ko'zlarga zarar bermaydigan "Dark Mode" yonadi.
* **Bildirishnoma (Notification):** 🔔 Qo'ng'iroqcha yonib tursa demak qaysidir mol tugayapti yoki muddati o'tyapti degani.
* **Alertlar:** Ekranda `Qoldiq Min dan tushib qolgan` tovarlar Qizil panelda turadi.

#### 🏭 Omborlar va Yetkazib beruvchilar (Warehouses & Suppliers)
* **Omborlar** sahifasidan hududlarga ko'ra istalgancha yangi ombor qo'sha olasiz (Masalan: *Chilonzor ombori, Bosh ombor*). U yerdagi mollar qiymati yig'indisi hisoblab turiladi.
* **Yetkazib beruvchilar (Suppliers)** oynasidan hamkorlarning Ism, Telefon, Email lari kiritiladi va ulardan eng ko'p nechta mol olinayotgani ko'rinib turadi.

#### 📦 Mahsulotlar (Products) qanday qo'shiladi?
1. **+ Yangi mahsulot** degan yashil tugmani bosing.
2. Formaga quyidagilarni kiriting: *Nomi (Olma), SKU (QR Kod unikal belgisi), Kategoriya turi, Qanchadan sotamiz va qanchaga olamiz, Minimal qoldiq qancha*.
3. **QR Kod:** Mahsulot ustiga kirsangiz tizim unga o'ziga xos 📲 QR Kod shakllantiradi! Sknerlab molni telefon orqali bemalol topsangiz bo'ladi.
4. **Exceldan Yuklash (Import):** Yuzlab mollarni bittalab kiritish o'rniga  tepadagi *📤 Import* tugmasidan kerakli `.xlsx` faylni tanlang ва 1 sekundda hamma tovarlaringiz tizimda paydo bo'ladi.
5. **Excelga Yuklash (Export):** *📥 Export*ni bosib saytdagi mollarni Excel fayl qilib kompyuterga saqlang.

#### 🔄 Kirim-Chiqim va Transfer (Transactions)
* Mollar bazada bor, lekin ularni 0 ta emas balki Qoldig'ini (Zaxira) to'ldirish uchun Shu bo'limni ishlatasiz.
* **+ Yangi tranzaksiya** bosing.
* Tipi (Kirim, Chiqim) tanlang, mahsulot va omborni tanlang, Soni hamda Ulgurji summasini yozib Saqlash bosing.
* **Natija:** Mahsulotlar qoldig'i avtomatik qo'shiladi (Yoki chiqimda ayiriladi). 
* Har bir ishdan so'ng **🖨️ Chek** tugmasi orqali qog'oz formatidagi Invoice (PDF) printer chiqarishga tayyor turadi! Siz PDFni saqlab mijozga telegram yuborishingiz yoki A4 ga onlayn pechat qilishingiz mumkin.

#### 📈 Analitika va Optimallashtirish (Eng qiyin Qism)
Tizim sun'iy matematika orqali omborni o'zi "Davolaydi":
1. **ABC Tahlil:** Eng ko'p pul olib keladigan A-mollar (Fokus shularda), B-mollar hamda hech kim olmaydigan foydasiz C-mollarga tizim o'zi tovarni ajratadi. Siz bu orqali "O'lik mollar"ni ko'ra olasiz.
2. **XYZ Tahlil:** Savdosi juda doimiy, barqaror mollar X-klassga ajratiladi, juda injiq va tartibsiz ketadiganlar Z-klassga.
3. **Matematik Optimallashtirish:** Har bir molning "Jami qoldig'i" asosida tizim *EOQ va ROP* (Qachon yangi molni qanchadan zakaz berish) formulasini yechib ekranga "Tavsiya"ni ko'rsatadi. 

---

### 4. Qoshimcha Texnik Imkoniyatlar
* **Auditoriya Tizimi (Audit Log):** Agar kimdir parolni bilib olib Nimadir qilsa-chi? Havotir olmang! Admin *Audit Log* oynasidan aynan Kim, qaysi kuni, Qaysi sahifada, Nimani O'zgartirgani / O'chirganini Izma-Iz ko'rib turadi. Tizimda firibgarlik o'tmaydi.
* **To'liq Moslashuv (Responsive):** Agar planshet yoki Katta telefon ishlatishni xohlasangiz, barcha tablitsalar siqilib-kichiklashib "Jadval emas, Chiroyli Kartalar"ga o'zgaradi va harakatlanish osonlashadi.

Tizim kelajakdagi rivojlanish standartlarini ko'zlab OOP metodikalar va eng so'nggi trendlar bilan dizayn qilingan! ✨
