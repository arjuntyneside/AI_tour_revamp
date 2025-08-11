from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def calculate_commission(price, rate):
    """Calculate commission amount"""
    try:
        return float(price) * float(rate) / 100
    except (ValueError, TypeError):
        return 0

@register.filter
def calculate_net_revenue(revenue, commission_amount):
    """Calculate net revenue after commission"""
    try:
        return float(revenue) - float(commission_amount)
    except (ValueError, TypeError):
        return 0
