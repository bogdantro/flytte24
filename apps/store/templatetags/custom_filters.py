
from django import template

register = template.Library()

@register.filter(name='add_space_separator')
def add_space_separator(value):
    return '{:,}'.format(value).replace(',', ' ').replace('.', ',')


@register.filter(name='image_count_range')
def image_count_range(car):
    return range(1, car.num_active_images + 1)
