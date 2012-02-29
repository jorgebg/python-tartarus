"""Extendable metaclass set with different funcionalities"""
class RegisteredMetaclass(type):
    """Registers all the defined subclasses.

    The metaclass must be named as follows: '<baseclass>Metaclass', or its class must define a class attribute named 'baseclass' with the name of the base class.

    Usage:

    from tartarus.metaclass import RegisteredMetaclass

    class TestMetaclass(RegisteredMetaclass):
        pass

    class Test(object):
        __metaclass__ = TestMetaclass

    class FirstTest(Test):
        pass

    class SecondTest(Test):
        pass


    print Test.registered
    Out: [<class '__main__.FirstTest'>, <class '__main__.SecondTest'>]

    """

    def __new__(self, classname, bases, classDict):
        cls = type.__new__(self, classname, bases, classDict)
        if hasattr(self, 'baseclass'):
            baseclass = self.baseclass
        else:
            baseclass = self.__name__[:-len('Metaclass')]
        if classname == baseclass:
            self.registered = []
        else:
            self.registered.append(cls)
        return cls


class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None 

    def __call__(cls,*args,**kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance