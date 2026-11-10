"""
Prognozlash xizmatlari: Moving Average, Exponential Smoothing, MAPE
"""
import numpy as np
from datetime import timedelta, date
from django.utils import timezone
from django.db.models import Sum
from core.models import Product, InventoryTransaction, Forecast


class ForecastService:

    @staticmethod
    def get_daily_demand(product, days=180):
        """Kunlik talab ma'lumotlarini olish"""
        since = timezone.now() - timedelta(days=days)
        txns = InventoryTransaction.objects.filter(
            product=product, transaction_type='out', created_at__gte=since
        )
        daily = []
        for d in range(days):
            day = since + timedelta(days=d)
            day_end = day + timedelta(days=1)
            qty = txns.filter(
                created_at__gte=day, created_at__lt=day_end
            ).aggregate(total=Sum('quantity'))['total'] or 0
            daily.append(float(qty))
        return daily

    @staticmethod
    def moving_average(product, window=7, forecast_days=7):
        """Moving Average yordamida prognoz"""
        daily = ForecastService.get_daily_demand(product)
        if len(daily) < window:
            return {'predictions': [], 'mape': None, 'message': "Ma'lumotlar yetarli emas"}

        predictions = []
        today = date.today()

        for d in range(forecast_days):
            recent = daily[-(window):]
            ma = np.mean(recent)
            forecast_date = today + timedelta(days=d + 1)
            predictions.append({
                'date': forecast_date,
                'predicted': round(ma, 2),
            })
            daily.append(ma)

            Forecast.objects.update_or_create(
                product=product,
                method='ma',
                forecast_date=forecast_date,
                defaults={'predicted_demand': round(ma, 2)}
            )

        # MAPE hisoblash (oxirgi 30 kunlik ma'lumotlar asosida)
        original = ForecastService.get_daily_demand(product)
        mape = ForecastService._calculate_mape(original, window)

        return {
            'predictions': predictions,
            'mape': round(mape, 2) if mape is not None else None,
            'window': window,
        }

    @staticmethod
    def exponential_smoothing(product, alpha=0.3, forecast_days=7):
        """Exponential Smoothing yordamida prognoz"""
        daily = ForecastService.get_daily_demand(product)
        if len(daily) < 2:
            return {'predictions': [], 'mape': None, 'message': "Ma'lumotlar yetarli emas"}

        # Smoothing
        smoothed = [daily[0]]
        for i in range(1, len(daily)):
            s = alpha * daily[i] + (1 - alpha) * smoothed[-1]
            smoothed.append(s)

        predictions = []
        today = date.today()
        last_value = smoothed[-1]

        for d in range(forecast_days):
            forecast_date = today + timedelta(days=d + 1)
            predictions.append({
                'date': forecast_date,
                'predicted': round(last_value, 2),
            })

            Forecast.objects.update_or_create(
                product=product,
                method='es',
                forecast_date=forecast_date,
                defaults={'predicted_demand': round(last_value, 2)}
            )

        # MAPE
        mape = ForecastService._calculate_mape_es(daily, alpha)

        return {
            'predictions': predictions,
            'mape': round(mape, 2) if mape is not None else None,
            'alpha': alpha,
        }

    @staticmethod
    def _calculate_mape(data, window):
        """MAPE (Mean Absolute Percentage Error) hisoblash"""
        if len(data) < window + 1:
            return None
        errors = []
        for i in range(window, len(data)):
            actual = data[i]
            predicted = np.mean(data[i - window:i])
            if actual > 0:
                errors.append(abs((actual - predicted) / actual) * 100)
        return np.mean(errors) if errors else None

    @staticmethod
    def _calculate_mape_es(data, alpha):
        """Exponential Smoothing uchun MAPE"""
        if len(data) < 3:
            return None
        smoothed = [data[0]]
        for i in range(1, len(data)):
            s = alpha * data[i] + (1 - alpha) * smoothed[-1]
            smoothed.append(s)
        errors = []
        for i in range(1, len(data)):
            if data[i] > 0:
                errors.append(abs((data[i] - smoothed[i - 1]) / data[i]) * 100)
        return np.mean(errors) if errors else None

    @staticmethod
    def generate_full_forecast(product):
        """Mahsulot uchun to'liq prognoz"""
        ma_7 = ForecastService.moving_average(product, window=7, forecast_days=7)
        ma_30 = ForecastService.moving_average(product, window=30, forecast_days=30)
        es_7 = ForecastService.exponential_smoothing(product, alpha=0.3, forecast_days=7)
        es_30 = ForecastService.exponential_smoothing(product, alpha=0.3, forecast_days=30)

        return {
            'ma_7': ma_7,
            'ma_30': ma_30,
            'es_7': es_7,
            'es_30': es_30,
        }
