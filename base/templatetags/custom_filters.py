from django import template

register = template.Library()

@register.filter
def replace_spaces(value):
    """
    Mengganti spasi dengan tanda hubung.
    """
    return value.replace(" ", "-")
