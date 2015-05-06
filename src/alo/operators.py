from django.core.exceptions import ValidationError
from django.forms.fields import Field


class BaseOperator(object):
    attrname = '__logic__'
    
    def __init__(self, *args, **kwargs):
        self.operands = args
        self.required = kwargs.get('required', False)

    def __len__(self):
        size = lambda x: len(x) if isinstance(x, BaseOperator) else 1
        return sum(size(each) for each in self.operands)
        
    def iter_all_operands(self):
        for each in self.operands:
            if isinstance(each, BaseOperator):
                for i in each.get_all_operands():
                    yield i
            else:
                yield each
        
    def __str__(self):
        func = lambda x,y: "%s %s %s" %(
            x.attrname if isinstance(x, Field) else x, 
            self.__class__.__name__ ,
            y.attrname if isinstance(y, Field) else y,
        )
        return "( %s )" % reduce(func, self.operands)

    def raise_exception(self, subject, subjects=None):
        text = 'Expected logic: %s' %self
        exception = ValidationError(text)
        exception.subject = subject
        exception.subjects = subjects or []
        raise exception
    
    def is_valid_data(self, obj, validated_data):
        if isinstance(obj, Field):
            return validated_data.get(obj.attrname)
        else:
            return obj.is_valid(validated_data)
        

class OR(BaseOperator):
    
    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)
    
    def is_valid(self, validated_data):
        for each in self.operands:
            if self.is_valid_data(each, validated_data):
                return each.attrname
        if self.required:
            self.raise_exception(subject=each.attrname)


class AND(BaseOperator):
    
    @classmethod
    def create(cls, *args, **kwargs):
        instance = cls(*args, **kwargs)
        if not instance.required:
            instance.required = any(each.required for each in instance.operands)
        return instance
    
    def is_valid(self, validated_data):
        validated = []
        for each in self.operands:
            if not self.is_valid_data(each, validated_data):
                if self.required:
                    self.raise_exception(subject=each.attrname)
            else:
                validated.append( each.attrname )
        if 0 < len(validated) < len(self.operands):
            self.raise_exception(subject=validated[0], subjects=validated[1:])
        return True
    