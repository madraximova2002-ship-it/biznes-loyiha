"""
Optimallashtirish xizmatlari: EOQ, ROP, Safety Stock
"""
import math
import numpy as np
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Avg
from core.models import Product, InventoryTransaction, WarehouseStock


class OptimizationService:

    Z_95 = 1.645  # 95% service level

    @staticmethod
    def calculate_eoq(product):
        """
        EOQ (Optimal buyurtma miqdori)
        EOQ = sqrt((2 * D * S) / H)
        D = yillik talab, S = buyurtma xarajati, H = saqlash xarajati
        """
        since = timezone.now() - timedelta(days=180)
        total_demand = InventoryTransaction.objects.filter(
            product=product, transaction_type='out', created_at__gte=since
        ).aggregate(total=Sum('quantity'))['total'] or 0

        annual_demand = float(total_demand) * 2  # 6 oylik → yillik
        ordering_cost = float(product.ordering_cost)
        holding_cost = float(product.holding_cost)

        if annual_demand <= 0 or ordering_cost <= 0 or holding_cost <= 0:
            return {
                'eoq': 0,
                'annual_demand': annual_demand,
                'ordering_cost': ordering_cost,
                'holding_cost': holding_cost,
                'message': "Ma'lumotlar yetarli emas"
            }

        eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)

        return {
            'eoq': round(eoq, 0),
            'annual_demand': annual_demand,
            'ordering_cost': ordering_cost,
            'holding_cost': holding_cost,
        }

    @staticmethod
    def calculate_safety_stock(product):
        """
        Safety Stock = Z × σ × √(Lead Time)
        σ = kunlik talabning standart og'ishi
        """
        since = timezone.now() - timedelta(days=180)
        txns = InventoryTransaction.objects.filter(
            product=product, transaction_type='out', created_at__gte=since
        )

        daily_demands = []
        for d in range(180):
            day = since + timedelta(days=d)
            day_end = day + timedelta(days=1)
            qty = txns.filter(
                created_at__gte=day, created_at__lt=day_end
            ).aggregate(total=Sum('quantity'))['total'] or 0
            daily_demands.append(float(qty))

        if not daily_demands or sum(daily_demands) == 0:
            return {
                'safety_stock': 0,
                'std_dev': 0,
                'lead_time': product.lead_time_days,
                'message': "Ma'lumotlar yetarli emas"
            }

        std_dev = float(np.std(daily_demands))
        lead_time = product.lead_time_days
        safety_stock = OptimizationService.Z_95 * std_dev * math.sqrt(lead_time)

        return {
            'safety_stock': round(safety_stock, 0),
            'std_dev': round(std_dev, 2),
            'lead_time': lead_time,
            'z_score': OptimizationService.Z_95,
        }

    @staticmethod
    def calculate_rop(product):
        """
        ROP (Qayta buyurtma nuqtasi)
        ROP = (Kunlik o'rtacha talab × Yetkazish muddati) + Safety Stock
        """
        since = timezone.now() - timedelta(days=180)
        total_demand = InventoryTransaction.objects.filter(
            product=product, transaction_type='out', created_at__gte=since
        ).aggregate(total=Sum('quantity'))['total'] or 0

        daily_avg_demand = float(total_demand) / 180.0
        ss = OptimizationService.calculate_safety_stock(product)
        safety_stock = ss['safety_stock']
        lead_time = product.lead_time_days

        rop = (daily_avg_demand * lead_time) + safety_stock

        return {
            'rop': round(rop, 0),
            'daily_avg_demand': round(daily_avg_demand, 2),
            'lead_time': lead_time,
            'safety_stock': safety_stock,
        }

    @staticmethod
    def get_product_recommendations(product):
        """Mahsulot uchun to'liq optimallashtirish tavsiyalari"""
        eoq = OptimizationService.calculate_eoq(product)
        rop = OptimizationService.calculate_rop(product)
        ss = OptimizationService.calculate_safety_stock(product)

        # Hozirgi umumiy zaxira
        current_stock = WarehouseStock.objects.filter(
            product=product
        ).aggregate(total=Sum('quantity'))['total'] or 0

        needs_reorder = current_stock <= rop['rop']

        # Buyurtma berish sanasini taxmin qilish
        from datetime import date
        if needs_reorder:
            reorder_date = date.today()
        elif rop['daily_avg_demand'] > 0:
            days_until_rop = (current_stock - rop['rop']) / rop['daily_avg_demand']
            reorder_date = date.today() + timedelta(days=max(0, days_until_rop))
        else:
            reorder_date = None

        return {
            'product': product,
            'current_stock': current_stock,
            'eoq': eoq,
            'rop': rop,
            'safety_stock': ss,
            'needs_reorder': needs_reorder,
            'recommended_quantity': eoq['eoq'],
            'reorder_date': reorder_date,
        }
