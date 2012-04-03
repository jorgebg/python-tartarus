from django.template.base import TemplateSyntaxError, Library, token_kwargs
from django.template.loader_tags import do_include, IncludeNode
from django.template.loader import select_template
from django.conf import settings
import os

register = Library()

class ResourceIncludeNode(IncludeNode):
    def render(self, context):
        try:
            template_name = self.template_name.resolve(context)
            template_names = []
            if context.has_key('resource'):
                template_names.append(os.path.join(context['resource'], template_name))
            template_names.append(template_name)
            template = select_template(template_names)
            return self.render_template(template, context)
        except:
            if settings.TEMPLATE_DEBUG:
                raise
            return ''

@register.tag('include')
def do_resource_include(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("%r tag takes at least one argument: the name of the template to be included." % bits[0])
    options = {}
    remaining_bits = bits[2:]
    while remaining_bits:
        option = remaining_bits.pop(0)
        if option in options:
            raise TemplateSyntaxError('The %r option was specified more '
                                      'than once.' % option)
        if option == 'with':
            value = token_kwargs(remaining_bits, parser, support_legacy=False)
            if not value:
                raise TemplateSyntaxError('"with" in %r tag needs at least '
                                          'one keyword argument.' % bits[0])
        elif option == 'only':
            value = True
        else:
            raise TemplateSyntaxError('Unknown argument for %r tag: %r.' %
                                      (bits[0], option))
        options[option] = value
    isolated_context = options.get('only', False)
    namemap = options.get('with', {})
    path = bits[1]
    return ResourceIncludeNode(parser.compile_filter(bits[1]), extra_context=namemap,
                       isolated_context=isolated_context)
