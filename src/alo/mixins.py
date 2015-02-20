from django.core.exceptions import ValidationError
from django import forms
from .operators import BaseOperator, AND, OR


class Parameters(dict):
    def __init__(self):
        self.validated = {}


class QueryFormMixin(object):

    @property
    def parameters(self):
        if not hasattr(self, '_parameters'):
            self._parameters = Parameters()
            items = self.fields.iteritems()
            name_to_aliases = {
                name: self._meta.aliases[name] for name,field in items
            }
            for name,value in self.cleaned_data.iteritems():
                if value:
                    self._parameters.validated[name] = value
                    for each in name_to_aliases[name]:
                        self._parameters[ each ] = value
        return self._parameters
    
    def set_meta(self):
        if not hasattr(self, '_meta'):
            self._meta = type('Meta', (object,), {})()
        self.set_aliases()
        self.set_extralogic()
    
    def set_aliases(self):
        self._meta.aliases = {}
        for name,field in self.fields.iteritems():
             self._meta.aliases[name] = (name,)
        if hasattr(self.Meta, 'aliases'):
            for fieldname,alias in self.Meta.aliases.items():
                if isinstance(alias, (str, unicode)):
                    self._meta.aliases[fieldname] = (alias,)
                else:
                    self._meta.aliases[fieldname] = alias
                
    def set_extralogic(self):
        def get_logic(operator):
            args = []
            for value in operator.operands:
                if isinstance(value, (str, unicode)):
                    self.fields[value].attrname = value
                    args.append( self.fields[value] )
                elif isinstance(value, BaseOperator):
                    args.append( get_logic(value) )
            return operator.__class__.create(*args)
        
        self._meta.extralogic = []
        if hasattr(self.Meta, 'extralogic'):
            for each in self.Meta.extralogic:
                self._meta.extralogic.append( get_logic(each) )
                
    def clean_extralogic(self):
        for each in self._meta.extralogic:
            try:
                each.is_valid(self.cleaned_data)
            except ValidationError as e:
                self.add_error(e.subject, e.message)
