from django import template
register = template.Library()

@register.filter
def format_time(time):
    return round(time/3600,3)

