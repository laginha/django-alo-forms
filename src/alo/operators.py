from django.core.exceptions import ValidationError
from django.forms.fields import Field


class BaseOperator(object):
    
    @classmethod
    def create(cls, *args):
        instance = cls(*args)
        instance.required = any(each.required for each in instance.operands)
        return instance
    
    def __init__(self, *args):
        self.operands = args

    def __len__(self):
        size = lambda x: len(x) if isinstance(x, BaseOperator) else 1
        return sum(size(each) for each in self.operands)
        
    def __str__(self):
        func = lambda x,y: "%s %s %s" %(
            x.attrname if hasattr(x, 'attrname') else x, 
            self.__class__.__name__ ,
            y.attrname if hasattr(y, 'attrname') else y,
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
    def is_valid(self, validated_data):
        for each in self.operands:
            if self.is_valid_data(each, validated_data):
                return True
        return False


class AND(BaseOperator): 
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
    