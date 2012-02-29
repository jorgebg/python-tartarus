import re

def indent(str, level=1, spaces=4):
    return "\n".join((level * spaces * " ") + i for i in str.splitlines())

def camelcase_split(str, char='_'):
    pattern = r'\1%s\2' % char
    s1 = re.sub('(.)([A-Z][a-z]+)', pattern, str)
    return re.sub('([a-z0-9])([A-Z])', pattern, s1).lower()