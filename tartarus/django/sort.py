from tartarus.utils import underscore_to_label

class Sort(object):
    def __init__(self, object_list, choices, request=None, default=None):
        self.object_list = object_list
        self.default = default
        if not self.default:
            self.default = choices.keys()[0]
        self.request = request
        self.choices_dict = {}
        for choice, args in choices.items():
            if isinstance(args, Choice):
                choice_obj = args
            else:
                kwargs = args[-1]
                if isinstance(kwargs, dict):
                    choice_obj = Choice(*args[:-1], **kwargs)
                else:
                    choice_obj = Choice(*args)
                
            choice_obj.sort = self
            choice_obj.id = choice
            self.choices_dict[choice] = choice_obj
        
        self.choices = self.choices_dict.values()
        
        if self.request:
            self.base_queryset = self.request.GET.copy()
            self.base_queryset['sort'] = 'sort'
            self.base_queryset = self.base_queryset.urlencode().replace('%', '%%').replace('sort=sort', 'sort=%s')
                
    def get_choice(self, choice):
        if self.choices_dict.has_key(choice):
            return self.choices_dict[choice]
        raise InvalidChoice()

    def sort_object_list(self, choice=None):
        if not choice:
            choice = self.default
        if not isinstance(choice, Choice):
            choice = self.get_choice(choice)
        if choice.extra:
            self.object_list=self.object_list.extra(**choice.extra)
        self.object_list=self.object_list.order_by(*choice.order_by)
        
        
        
        
class ChoiceRepresentation(str):
    def __new__(cls, choice, querystring):
        obj = str.__new__(cls, choice)
        obj.querystring = querystring
        return obj
        
class Choice(object):
    def __init__(self, *args, **kwargs):
        self.order_by = args
        self.id = kwargs.get('id')
        self.extra = kwargs.get('extra', None)
        self.sort = kwargs.get('sort')            
        self._label = kwargs.get('label')
    
    def get_default_label(self):
        return underscore_to_label(self.id)
    
    @property
    def label(self):
        return self._label or self.get_default_label()
    
    @property
    def queryset(self):
        """
        Returns a query string for the given choice, preserving any
        GET parameters present.
        """
        if self.sort.base_queryset:
            return self.sort.base_queryset %self.id
        
        return 'sort=%s' %self.id
    
    @property
    def representation(self):
        return ChoiceRepresentation(self.label, self.queryset)
        

class InvalidChoice(Exception):
    pass