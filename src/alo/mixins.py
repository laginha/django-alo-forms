from django.core.exceptions import ValidationError
from django import forms
from .operators import BaseOperator, AND, OR


class QueryFormMixin(object):

    @property
    def non_empty_data(self):
        if not hasattr(self, '_non_empty_data'):
            self.set_parameters()
        return self._non_empty_data

    @property
    def parameters(self):
        if not hasattr(self, '_parameters'):
            self.set_parameters()
        return self._parameters
    
    def set_parameters(self):
        self._parameters = {}
        self._non_empty_data = {}
        items = self.fields.iteritems()
        name_to_lookups = {
            name: self._meta.lookups[name] for name,field in items
        }
        for name,value in self.cleaned_data.iteritems():
            if value:
                self._non_empty_data[name] = value
                for each in name_to_lookups[name]:
                    self._parameters[ each ] = value
    
    def set_meta(self):
        if not hasattr(self, '_meta'):
            self._meta = type('Meta', (object,), {})()
        self.set_lookups()
        self.set_extralogic()
    
    def set_lookups(self):
        self._meta.lookups = {}
        for name,field in self.fields.iteritems():
             self._meta.lookups[name] = (name,)
        if hasattr(self.Meta, 'lookups'):
            for fieldname,alias in self.Meta.lookups.items():
                if isinstance(alias, (str, unicode)):
                    self._meta.lookups[fieldname] = (alias,)
                else:
                    self._meta.lookups[fieldname] = alias
                
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
