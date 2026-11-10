"""
6 oylik simulyatsiya ma'lumotlari bilan Database Seeder.
Buyruq: python manage.py seed
"""
import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import (
    UserProfile, Warehouse, Category, Supplier, Product,
    WarehouseStock, InventoryTransaction
)


class Command(BaseCommand):
    help = "6 oylik simulyatsiya malumotlari bilan bazani toldirish"

    def handle(self, *args, **options):
        self.stdout.write("Seeder boshlandi...")

        # --- USERS ---
        users_data = [
            {'username': 'admin', 'first_name': 'Sardor', 'last_name': 'Rahimov', 'role': 'admin'},
            {'username': 'mudir', 'first_name': 'Jasur', 'last_name': 'Karimov', 'role': 'manager'},
            {'username': 'tahlilchi', 'first_name': 'Dilshod', 'last_name': 'Toshmatov', 'role': 'analyst'},
            {'username': 'kuzatuvchi', 'first_name': 'Gulnora', 'last_name': 'Azimova', 'role': 'observer'},
        ]

        created_users = []
        for ud in users_data:
            user, created = User.objects.get_or_create(
                username=ud['username'],
                defaults={
                    'first_name': ud['first_name'],
                    'last_name': ud['last_name'],
                    'is_staff': ud['role'] == 'admin',
                    'is_superuser': ud['role'] == 'admin',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            UserProfile.objects.get_or_create(user=user, defaults={'role': ud['role']})
            created_users.append(user)
            self.stdout.write("  [+] %s (%s)" % (user.get_full_name(), ud['role']))

        # --- WAREHOUSES ---
        warehouses_data = [
            {'name': 'Toshkent asosiy ombori', 'address': 'Toshkent sh., Mirzo Ulugbek tumani'},
            {'name': 'Samarqand filiali', 'address': 'Samarqand sh., Registon kochasi 42'},
            {'name': 'Buxoro filiali', 'address': 'Buxoro sh., Amir Temur kochasi 78'},
            {'name': "Fargona filiali", 'address': 'Fargona sh., Mustaqillik shoh kochasi 33'},
        ]

        warehouses = []
        for i, wd in enumerate(warehouses_data):
            wh, _ = Warehouse.objects.get_or_create(
                name=wd['name'],
                defaults={
                    'address': wd['address'],
                    'manager': created_users[1] if i == 0 else None,
                    'phone': '+998 %d %d %d %d' % (random.randint(90, 99), random.randint(100, 999), random.randint(10, 99), random.randint(10, 99)),
                }
            )
            warehouses.append(wh)
            self.stdout.write("  [+] %s" % wh.name)

        # --- CATEGORIES ---
        categories_data = [
            'Elektronika', 'Oziq-ovqat', 'Kiyim-kechak', 'Maishiy texnika',
            'Qurilish materiallari', 'Avtomobil ehtiyot qismlari', 'Tibbiyot buyumlari',
            'Kantselyariya', 'Mebel', 'Kosmetika'
        ]
        categories = []
        for cn in categories_data:
            cat, _ = Category.objects.get_or_create(name=cn)
            categories.append(cat)
        self.stdout.write("  [+] %d ta kategoriya yaratildi" % len(categories))

        # --- SUPPLIERS ---
        suppliers_data = [
            {'name': 'TechSupply LLC', 'contact_person': 'Anvar Sobirov', 'phone': '+998 90 123 45 67'},
            {'name': 'FoodMart Import', 'contact_person': 'Bekzod Xolmatov', 'phone': '+998 91 234 56 78'},
            {'name': 'TextilPro', 'contact_person': 'Malika Karimova', 'phone': '+998 93 345 67 89'},
            {'name': 'BuildMax', 'contact_person': 'Rustam Ergashev', 'phone': '+998 94 456 78 90'},
            {'name': 'AutoParts Uz', 'contact_person': 'Sherzod Mirzayev', 'phone': '+998 95 567 89 01'},
            {'name': 'MedEquip Plus', 'contact_person': 'Nilufar Rahimova', 'phone': '+998 97 678 90 12'},
        ]
        suppliers = []
        for sd in suppliers_data:
            sup, _ = Supplier.objects.get_or_create(
                name=sd['name'],
                defaults={
                    'contact_person': sd['contact_person'],
                    'phone': sd['phone'],
                    'email': 'info@%s.uz' % sd['name'].lower().replace(' ', ''),
                }
            )
            suppliers.append(sup)
        self.stdout.write("  [+] %d ta yetkazib beruvchi" % len(suppliers))

        # --- PRODUCTS ---
        products_data = [
            {'sku': 'EL-001', 'name': 'Samsung Galaxy A54 smartfon', 'cat': 0, 'sup': 0, 'price': 3200000, 'cost': 2800000},
            {'sku': 'EL-002', 'name': 'Lenovo IdeaPad noutbuk', 'cat': 0, 'sup': 0, 'price': 8500000, 'cost': 7200000},
            {'sku': 'EL-003', 'name': 'JBL Flip 5 kolonka', 'cat': 0, 'sup': 0, 'price': 950000, 'cost': 750000},
            {'sku': 'EL-004', 'name': 'Apple AirPods Pro', 'cat': 0, 'sup': 0, 'price': 2800000, 'cost': 2400000},
            {'sku': 'EL-005', 'name': 'Xiaomi Mi Band 8', 'cat': 0, 'sup': 0, 'price': 450000, 'cost': 320000},
            {'sku': 'OO-001', 'name': 'Makaron (Barilla 500g)', 'cat': 1, 'sup': 1, 'price': 18000, 'cost': 12000},
            {'sku': 'OO-002', 'name': "Osimlik yogi (1L)", 'cat': 1, 'sup': 1, 'price': 28000, 'cost': 22000},
            {'sku': 'OO-003', 'name': 'Shakar (1kg)', 'cat': 1, 'sup': 1, 'price': 14000, 'cost': 10500},
            {'sku': 'OO-004', 'name': 'Guruch (Premium 5kg)', 'cat': 1, 'sup': 1, 'price': 85000, 'cost': 65000},
            {'sku': 'OO-005', 'name': 'Choy (Ahmad Tea 200g)', 'cat': 1, 'sup': 1, 'price': 42000, 'cost': 32000},
            {'sku': 'KK-001', 'name': "Erkaklar koylagi (M)", 'cat': 2, 'sup': 2, 'price': 180000, 'cost': 120000},
            {'sku': 'KK-002', 'name': "Ayollar koylagi (S)", 'cat': 2, 'sup': 2, 'price': 250000, 'cost': 170000},
            {'sku': 'KK-003', 'name': 'Sport poyabzal (Nike)', 'cat': 2, 'sup': 2, 'price': 890000, 'cost': 650000},
            {'sku': 'KK-004', 'name': "Jinsi shim (Levis)", 'cat': 2, 'sup': 2, 'price': 520000, 'cost': 380000},
            {'sku': 'MT-001', 'name': 'Artel kir yuvish mashinasi', 'cat': 3, 'sup': 0, 'price': 4500000, 'cost': 3800000},
            {'sku': 'MT-002', 'name': 'Samsung muzlatgich', 'cat': 3, 'sup': 0, 'price': 6200000, 'cost': 5100000},
            {'sku': 'MT-003', 'name': "Mikrotolqinli pech", 'cat': 3, 'sup': 0, 'price': 1200000, 'cost': 900000},
            {'sku': 'QM-001', 'name': 'Sement (50kg)', 'cat': 4, 'sup': 3, 'price': 65000, 'cost': 48000},
            {'sku': 'QM-002', 'name': "Gisht (1000 dona)", 'cat': 4, 'sup': 3, 'price': 1200000, 'cost': 900000},
            {'sku': 'QM-003', 'name': "Boyoq (10L oq)", 'cat': 4, 'sup': 3, 'price': 320000, 'cost': 240000},
            {'sku': 'AE-001', 'name': "Motor yogi (Castrol 4L)", 'cat': 5, 'sup': 4, 'price': 280000, 'cost': 210000},
            {'sku': 'AE-002', 'name': 'Tormoz nakladkasi', 'cat': 5, 'sup': 4, 'price': 180000, 'cost': 120000},
            {'sku': 'AE-003', 'name': 'Akkumulyator (60Ah)', 'cat': 5, 'sup': 4, 'price': 850000, 'cost': 650000},
            {'sku': 'TB-001', 'name': 'Tibbiy niqob (50 dona)', 'cat': 6, 'sup': 5, 'price': 35000, 'cost': 22000},
            {'sku': 'TB-002', 'name': "Qol sanitayzeri (500ml)", 'cat': 6, 'sup': 5, 'price': 25000, 'cost': 15000},
            {'sku': 'KN-001', 'name': "A4 qogoz (500 varaq)", 'cat': 7, 'sup': 5, 'price': 55000, 'cost': 38000},
            {'sku': 'KN-002', 'name': "Ruchka toplami (12 dona)", 'cat': 7, 'sup': 5, 'price': 28000, 'cost': 18000},
            {'sku': 'MB-001', 'name': 'Ofis stuli (ergonomik)', 'cat': 8, 'sup': 3, 'price': 1800000, 'cost': 1300000},
            {'sku': 'MB-002', 'name': 'Kompyuter stoli', 'cat': 8, 'sup': 3, 'price': 2200000, 'cost': 1600000},
            {'sku': 'KO-001', 'name': 'Shampun (Head and Shoulders)', 'cat': 9, 'sup': 1, 'price': 45000, 'cost': 30000},
            {'sku': 'KO-002', 'name': 'Krem (Nivea 150ml)', 'cat': 9, 'sup': 1, 'price': 65000, 'cost': 42000},
        ]

        products = []
        for pd in products_data:
            holding = round(float(pd['cost']) * 0.02, 2)
            ordering = round(float(pd['cost']) * 0.05, 2)

            product, _ = Product.objects.get_or_create(
                sku=pd['sku'],
                defaults={
                    'name': pd['name'],
                    'category': categories[pd['cat']],
                    'supplier': suppliers[pd['sup']],
                    'price': Decimal(str(pd['price'])),
                    'cost_price': Decimal(str(pd['cost'])),
                    'holding_cost': Decimal(str(holding)),
                    'ordering_cost': Decimal(str(ordering)),
                    'lead_time_days': random.randint(3, 14),
                    'min_stock': random.randint(5, 50),
                    'unit': 'dona',
                }
            )
            products.append(product)
        self.stdout.write("  [+] %d ta mahsulot yaratildi" % len(products))

        # --- INITIAL STOCK ---
        for product in products:
            for warehouse in warehouses:
                qty = random.randint(20, 200)
                WarehouseStock.objects.get_or_create(
                    warehouse=warehouse,
                    product=product,
                    defaults={'quantity': qty}
                )
        self.stdout.write("  [+] Boshlangich zaxira kiritildi")

        # --- 6 MONTHS SIMULATED TRANSACTIONS ---
        self.stdout.write("  [*] 6 oylik tranzaksiyalar generatsiya qilinmoqda...")

        now = timezone.now()
        start_date = now - timedelta(days=180)
        transaction_count = 0
        batch = []

        for day_offset in range(180):
            current_date = start_date + timedelta(days=day_offset)
            daily_count = random.randint(5, 15)

            for _ in range(daily_count):
                product = random.choice(products)
                warehouse = random.choice(warehouses)
                user = random.choice(created_users)

                r = random.random()
                if r < 0.40:
                    t_type = 'in'
                    qty = random.randint(10, 100)
                    target = None
                elif r < 0.85:
                    t_type = 'out'
                    qty = random.randint(1, 30)
                    target = None
                else:
                    t_type = 'transfer'
                    qty = random.randint(5, 40)
                    others = [w for w in warehouses if w != warehouse]
                    target = random.choice(others) if others else None

                price = float(product.price) * random.uniform(0.9, 1.1)
                hour = random.randint(8, 18)
                minute = random.randint(0, 59)

                batch.append(InventoryTransaction(
                    transaction_type=t_type,
                    product=product,
                    warehouse=warehouse,
                    target_warehouse=target,
                    quantity=qty,
                    unit_price=Decimal(str(round(price, 2))),
                    total_price=Decimal(str(round(price * qty, 2))),
                    created_by=user,
                    note='',
                ))
                transaction_count += 1

            if day_offset % 30 == 0 and day_offset > 0:
                self.stdout.write("    [*] %d kun... (%d tranzaksiya)" % (day_offset, transaction_count))

        # Bulk create all transactions
        InventoryTransaction.objects.bulk_create(batch, batch_size=500)

        # Fix created_at dates
        self.stdout.write("  [*] Sanalar yangilanmoqda...")
        all_txns = InventoryTransaction.objects.all().order_by('id')
        idx = 0
        for day_offset in range(180):
            current_date = start_date + timedelta(days=day_offset)
            daily_count = 0
            # Count transactions for this day from our batch pattern
            while idx < len(batch):
                txn = all_txns[idx] if idx < all_txns.count() else None
                if txn is None:
                    break
                hour = random.randint(8, 18)
                minute = random.randint(0, 59)
                txn_time = current_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))
                InventoryTransaction.objects.filter(id=txn.id).update(created_at=txn_time)
                idx += 1
                daily_count += 1
                if daily_count >= random.randint(5, 15):
                    break

        self.stdout.write(self.style.SUCCESS(
            "\n[OK] Seeder muvaffaqiyatli yakunlandi!\n"
            "   Foydalanuvchilar: %d\n"
            "   Omborlar: %d\n"
            "   Kategoriyalar: %d\n"
            "   Yetkazib beruvchilar: %d\n"
            "   Mahsulotlar: %d\n"
            "   Tranzaksiyalar: ~%d\n"
            "\n   Login: admin / password123\n"
            % (len(created_users), len(warehouses), len(categories), len(suppliers), len(products), transaction_count)
        ))
