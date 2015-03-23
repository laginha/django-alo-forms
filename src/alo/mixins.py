from django.core.exceptions import ValidationError
from django import forms
from .operators import BaseOperator, AND, OR


class QueryFormMixin(object):

    @property
    def non_empty_data(self):
        # legacy
        return self.validated_data

    @property
    def validated_data(self):
        if not hasattr(self, '_validated_data'):
            self.set_parameters()
        return self._validated_data

    @property
    def parameters(self):
        if not hasattr(self, '_parameters'):
            self.set_parameters()
        return self._parameters
    
    def get_data(self, name):
        value = self.cleaned_data.get(name, None)
        return value if value else self._meta.defaults.get(name, None)
    
    def set_parameters(self):
        self._parameters = {}
        self._validated_data = {}
        for fieldname,lookup in self._meta.lookups.iteritems():
            value = self.get_data(fieldname)
            if value:
                self._validated_data[fieldname] = value
                self._parameters[self._meta.lookups[fieldname]] = value
        for fields,call in self._meta.multifield_lookups.iteritems():
            values = []
            for fieldname in fields:
                value = self.get_data(fieldname)
                if value:
                    self._validated_data[fieldname] = value
                    self._parameters.pop(self._meta.lookups[fieldname])
                    values.append(value)
            if len(values) == len(fields):
                self._parameters.update(call(*values))
    
    def set_meta(self):                        
        if not hasattr(self, '_meta'):
            self._meta = type('Meta', (object,), {})()
        if not hasattr(self, 'Meta'):
            self.Meta = type('Meta', (object,), {})()
        self.set_lookups_and_defaults()
        self.set_multifield_lookups()
        self.set_extralogic()
    
    def set_lookups_and_defaults(self):
        self._meta.defaults = {}
        self._meta.lookups = {}
        self._meta.no_defaults = getattr(self.Meta, 'no_defaults', False)
        for name,field in self.fields.iteritems():
             self._meta.lookups[name] = name
             if not self._meta.no_defaults:
                 self._meta.defaults[name] = field.initial
        if hasattr(self.Meta, 'lookups'):
            for fieldname,alias in self.Meta.lookups.iteritems():
                self._meta.lookups[fieldname] = alias
    
    def set_multifield_lookups(self):
        self._meta.multifield_lookups = {}
        if hasattr(self.Meta, 'multifield_lookups'):
            for fields,alias in self.Meta.multifield_lookups.iteritems():
                self._meta.multifield_lookups[fields] = alias
    
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
                each.is_valid(self.validated_data)
            except ValidationError as e:
                try:
                    self.add_error(e.subject, e.message)
                except AttributeError:
                    self.__errors[e.subject] = e.message
