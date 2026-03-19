from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)


@register.filter
def currency(value):
    try:
        return f'${float(value):,.2f}'
    except (TypeError, ValueError):
        return '$0.00'
