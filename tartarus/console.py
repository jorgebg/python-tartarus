import argparse
import inspect
import sys
import os
import re
from tartarus.string import indent
from tartarus.reflection import isprivate
from tartarus.collection import lower_keys

class Application(object):
    controllers = []
    name = 'Application'
    default_action_name = 'default'

    def __init__(self, name=None, controllers=None, default_action_name=None):
        if name:
            self.name = name
        if controllers:
            self.controllers = controllers
        if default_action_name:
            self.default_action_name = default_action_name
        if len(self.controllers)==0:
            self.controllers = Controller.__subclasses__()

    @property
    def controllers_names(self):
        return [self.get_system_name(c) for c in self.controllers]

    @property
    def controllers_map(self):
        map = {}
        for c in self.controllers:
            map[self.get_system_name(c)] = c
        return map

    @property
    def file(self):
        return os.path.basename(sys.argv[0])

    def print_documentation(self, objects):
        for object in objects:
            name = indent(self.get_system_name(object), level=1)
            doc = indent(getattr(object, '__doc__') or '', level=2)+'\n'
            print '\n'.join([name, doc])

    def get_system_name(self, cls):
        name =  getattr(cls, 'name',
                    getattr(cls, '__name__',
                        getattr(cls, '__class__').__name__
                    )
                )
        return name.lower()

    def get_actions(self, controller):
        actions = [v for k, v in inspect.getmembers(controller, predicate=inspect.ismethod) if not isprivate(v)]
        return actions

    def get_actions_names(self, actions):
        return [action.__name__ for action in actions if not isprivate(action)]

    def run(self, controllers=None):
        if controllers:
            self.controllers = controllers
        
        self.controllers = [c() if inspect.isclass(c) else c for c in self.controllers]
        
        if len(sys.argv) is 1:
            print "usage: %s [-h] <controller>\n" % self.file
            print "available controllers:\n"
            self.print_documentation(self.controllers)
            exit()
                
        controller_name = sys.argv[1]
        if controller_name not in self.controllers_names:
            print "controller '%s' not found.\n" % controller_name
            print "available controllers:\n"
            self.print_documentation(self.controllers)
            exit()
        controller = self.controllers_map[controller_name]
        default_action_name = getattr(controller, 'default_action', self.default_action_name)

        actions = self.get_actions(controller)
        actions_names = self.get_actions_names(actions)
        has_default_action = default_action_name in actions_names
        if len(sys.argv) is 2:
            if has_default_action:
                sys.argv.append(default_action_name)
            else:
                print "usage: %s [-h] %s <action>\n" % (self.file, self.get_system_name(controller))
                print "available actions:\n"
                self.print_documentation(actions)
                exit()
        
        action_name = sys.argv[2]

        
        if action_name not in actions_names:
            if has_default_action:
                sys.argv.append(sys.argv[2])
                sys.argv[2]=default_action_name
                action_name = sys.argv[2]
            else:
                print "action '%s' not found.\n" % action_name
                print "available actions:\n"
                self.print_documentation(actions)
                exit()
        action = getattr(controller, action_name)

        parser = argparse.ArgumentParser()
        parser.add_argument('controller', metavar=controller_name)
        parser.add_argument('action', metavar=action_name)

        argspec = inspect.getargspec(action) #(args, varargs, keywords, defaults)
        action_args = argspec[0][1:]
        threshold = len(action_args)
        if argspec[-1]:
            threshold -= len(argspec[-1])
        for i, arg in enumerate(action_args):
            required = i < threshold
            if required:
                named_args = { 'required': required }
            else:
                default = argspec[-1][i-threshold]
                named_args = { 'default': default }
                if not isinstance(default, bool):
                    named_args['type']=default.__class__
                elif default:
                    named_args['action']='store_false'
                else:
                    named_args['action']='store_true'

            if len(arg) == 1:
                parser.add_argument('-'+arg, **named_args)
            else:
                parser.add_argument('-'+arg[0], '--'+arg, **named_args)
        
        args = parser.parse_args()
        action_args_values = {}
        for key in action_args:
            action_args_values[key]=getattr(args, key)
        getattr(controller, args.action)(**action_args_values)

class Controller(object):
    pass

class Input(object):

    @classmethod
    def string(self, question, default=None, sensitive=False, pattern='^.+$'):
        if isinstance(pattern, str):
            pattern=re.compile(pattern)
        while True:
            sys.stdout.write(question)
            choice = raw_input()
            if not sensitive:
                choice = choice.lower()
            if not pattern.match(choice):
                if default is not None:
                    return default
                else:
                    sys.stdout.write("Please respond with this pattern: %s \n" % pattern)
            return choice

    @classmethod
    def choices(self, question, choices, default=None, sensitive=False):
        if not isinstance(choices, dict):
            choices_dict={}
            for c in choices:
                choices[c]=c
            choices = choices_dict

        if not sensitive:
            choices = lower_keys(choices)

        if default not in choices.values():
            if default not in choices.keys():
                raise ValueError("invalid default answer: '%s'" % default)
            else:
                default=choices[default]

        while True:
            sys.stdout.write(question)
            choice = raw_input()
            if not sensitive:
                choice = choice.lower()
            if default is not None and choice == '':
                if default in choices.values():
                    return default
                else:
                    return choices[default]
            elif choice in choices:
                return choices[choice]
            else:
                sys.stdout.write("Please respond with %s \n" % 'or '.join(choices))

    @classmethod
    def bool(self, question, default="yes"):
        """Ask a yes/no question via raw_input() and return their answer.

        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

        The "answer" return value is one of "yes" or "no".
        """
        valid = {"yes":True,   "y":True,  "ye":True,
                 "no":False,     "n":False}
        if isinstance(default, str):
            if not valid.has_key(default):
                raise ValueError("invalid default answer: '%s'" % default)
            else:
                default=valid[default]
        if default == None:
            prompt = " [y/n] "
        elif default == True:
            prompt = " [Y/n] "
        elif default == False:
            prompt = " [y/N] "

        return self.choices(question+prompt, valid, default)

