from django import template

register = template.Library()

@register.filter(name='format_money')
def format_money(value):
    """
    Format a number with commas as thousand separators.
    Example: 16986566 -> 16,986,566
    """
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "0"
