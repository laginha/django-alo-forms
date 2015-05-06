from django.core.exceptions import ValidationError
from django import forms
from .operators import BaseOperator, AND, OR


class QueryFormMixin(object):

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
        is_valid = lambda x: x not in [None, '']
        value = self.cleaned_data.get(name, None)
        return value if is_valid(value) else self._meta.defaults.get(name, None)
    
    def set_parameters(self):
        self._parameters = {}
        self._validated_data = {}
        for fieldname,lookup in self._meta.lookups.iteritems():
            value = self.get_data(fieldname)
            if value != None:
                self._validated_data[fieldname] = value
                if fieldname not in self._meta.ignore:
                    self._parameters[lookup] = value
        for fields,call in self._meta.multifield_lookups.iteritems():
            values = []
            for fieldname in fields:
                value = self.get_data(fieldname)
                if value != None:
                    self._validated_data[fieldname] = value
                    self.pop_from_parameters(fieldname)
                    values.append(value)
            if len(values) == len(fields):
                self._parameters.update(call(*values))
    
    def reset_required_fields(self):
        if self._meta.required != None:
            for name,field in self.fields.iteritems():
                field.required = name in self._meta.required
    
    def set_meta(self):                        
        if not hasattr(self, '_meta'):
            self._meta = type('Meta', (object,), {})()
        if not hasattr(self, 'Meta'):
            self.Meta = type('Meta', (object,), {})()
        self._meta.required = getattr(self.Meta, 'required', None)
        self._meta.ignore = getattr(self.Meta, 'ignore', [])
        self.set_lookups_and_defaults()
        self.set_multifield_lookups()
        self.set_extralogic()
            
    def set_lookups_and_defaults(self):
        self._meta.defaults = {}
        self._meta.lookups = {}
        self._meta.no_defaults = getattr(self.Meta, 'no_defaults', False)
        for name,field in self.fields.iteritems():
            if hasattr(self.Meta, 'lookups'):
                self._meta.lookups[name] = self.Meta.lookups.get(name, name)
            else:
                self._meta.lookups[name] = name
            if not self._meta.no_defaults:
                if callable(field.initial):
                    self._meta.defaults[name] = field.initial()
                else:
                    self._meta.defaults[name] = field.initial
    
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
            return operator.create(*args, required=operator.required)
            
        self._meta.extralogic = []
        if hasattr(self.Meta, 'extralogic'):
            for each in self.Meta.extralogic:
                self._meta.extralogic.append( get_logic(each) )
    
    def add_validation_error(self, name, messages):
        try:
            self.add_error(name, messages)
        except AttributeError:
            self._errors[name] = messages
    
    def pop_from_parameters(self, fieldname):
        lookup = self._meta.lookups[fieldname]
        self._parameters.pop(lookup, None)
           
    def clean_extralogic(self):
        
        def is_default_value(name):
            validated_data = self.validated_data.get(name, None)
            default_data = self._meta.defaults.get(name, None)
            return validated_data and validated_data == default_data
        
        for each in self._meta.extralogic:
            try:
                result = each.is_valid(self.validated_data)
            except ValidationError as e:
                if is_default_value(e.subject):
                    self.pop_from_parameters(e.subject)
                    for name in e.subjects:
                        if not is_default_value(name):
                            self.add_validation_error(name, e.messages)
                            break
                        self.pop_from_parameters(name)
                else:
                    self.add_validation_error(e.subject, e.messages)
            else:
                if isinstance(each, OR):
                    for field in each.iter_all_operands():
                        if field.attrname != result:
                            self.pop_from_parameters(field.attrname)
                
