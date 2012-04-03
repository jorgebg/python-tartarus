from django import template

register = template.Library()

@register.filter
def model_fields(model):
    fields = []
    for field_name in model._meta.get_all_field_names():
        field = {'label':field_name, 'data':getattr(model, field_name)}
        fields.append(field)
    fields.reverse()
    return fields