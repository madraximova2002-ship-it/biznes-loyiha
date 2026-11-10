from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter
def som_format(value):
    """Format number as Uzbek so'm currency"""
    try:
        value = float(value)
        formatted = intcomma(int(value))
        return f"{formatted} so'm"
    except (ValueError, TypeError):
        return "0 so'm"


@register.filter
def percentage(value, decimals=1):
    try:
        return f"{float(value):.{decimals}f}%"
    except (ValueError, TypeError):
        return "0.0%"


@register.filter
def status_badge(value):
    badges = {
        'in': '<span class="badge badge-success">Kirim</span>',
        'out': '<span class="badge badge-danger">Chiqim</span>',
        'transfer': '<span class="badge badge-info">Transfer</span>',
    }
    return badges.get(value, value)


@register.filter
def abc_badge(value):
    colors = {
        'A': 'badge-success',
        'B': 'badge-warning',
        'C': 'badge-danger',
        'X': 'badge-success',
        'Y': 'badge-warning',
        'Z': 'badge-danger',
    }
    css = colors.get(value, 'badge-secondary')
    return f'<span class="badge {css}">{value}</span>'


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def user_theme(user):
    if user.is_authenticated:
        try:
            return 'dark' if user.profile.dark_mode else 'light'
        except Exception:
            return 'light'
    return 'light'


@register.simple_tag
def user_role(user):
    if user.is_authenticated:
        if user.is_superuser:
            return "Administrator"
        try:
            return user.profile.get_role_display()
        except Exception:
            return "Foydalanuvchi"
    return ""


@register.filter(name='has_role')
def has_role(user, roles):
    """
    Ruxsatlarni tekshirish - Misol: {% if request.user|has_role:"admin,manager" %}
    """
    if user.is_authenticated:
        if user.is_superuser:
            return True
        try:
            role = user.profile.role
            role_list = [r.strip() for r in roles.split(',')]
            return role in role_list
        except Exception:
            pass
    return False
