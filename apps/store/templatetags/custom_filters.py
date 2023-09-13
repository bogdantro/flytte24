# myapp/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='add_space_separator')
def add_space_separator(value):
    return '{:,}'.format(value).replace(',', ' ').replace('.', ',')
