from django import template
from django.template.base import Node
from django.templatetags.future import url as url_tag

register = template.Library()

class LinkNode(Node):
    def __init__(self, url, label):
        self.url = url
        self.label = label
    
    def render(self, context):
        return '<a href="%s">%s</a>' % (self.url.render(context), self.label)

@register.tag
def link(parser, token):
    tokens = token.split_contents()
    contents = token.contents
    label = tokens[-1]
    contents = contents.replace(tokens[-1], '')
    contents = contents.strip()
    token.contents = contents
    url = url_tag(parser, token)
    return LinkNode(url, label)