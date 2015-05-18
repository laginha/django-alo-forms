from django.core.exceptions import ValidationError
from django import forms
from .operators import BaseOperator, AND, OR


class ValidatedValue(object):
    def __init__(self, value, is_default=False):
        self.object = value
        self.is_default = is_default
    
    def __cmp__(self, other):
        if self.object < other:
            return -1
        elif self.object > other:
            return 1
        return 0

        
class QueryFormMixin(object):
    
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
    
    def get_validated_data(self):
        return {k:v.object for k,v in self._validated_data.iteritems()}
    
    def set_validated_data(self):
        self._validated_data = {}
        for fieldname,lookup in self._meta.lookups.iteritems():
            value = self.cleaned_data.get(fieldname)
            if value not in [None, '']:
                value = ValidatedValue(value, is_default=False)
                self._validated_data[fieldname] = value
            else:
                default_value = self._meta.defaults.get(fieldname)
                if default_value:
                    value = ValidatedValue(default_value, is_default=True)
                    self._validated_data[fieldname] = value 

    @property
    def parameters(self):
        if not hasattr(self, '_parameters'):
            self._parameters = self.get_parameters()
        return self._parameters
        
    def get_parameters(self):
        meta = self._meta
        items = self._validated_data.iteritems()
        parameters = {
            meta.lookups[k]:v.object for k,v in items if k not in meta.ignore
        }
        for fields,call in meta.multifield_lookups.iteritems():
            values = []
            for fieldname in fields:
                value = self._validated_data.get(fieldname)
                if value != None:
                    parameters.pop(meta.lookups.get(fieldname), None)
                    values.append(value.object)
            if len(values) == len(fields):
                parameters.update(call(*values))
        return parameters
    
    def add_validation_error(self, name, messages):
        try:
            self.add_error(name, messages)
        except AttributeError:
            self._errors[name] = messages
           
    def clean_extralogic(self):
        self.set_validated_data()
        for each in self._meta.extralogic:
            try:
                result = each.is_valid(self._validated_data)
            except ValidationError as e:
                for field in each.iter_all_operands():
                    if field.attrname in self._validated_data:
                        if self._validated_data[field.attrname].is_default:
                            self._validated_data.pop(field.attrname)
                        else:
                            self.add_validation_error(field.attrname, e.messages)
                            break
                    elif each.required:
                        self.add_validation_error(field.attrname, e.messages)
                        break
            else:
                if isinstance(each, OR):
                    for field in each.iter_all_operands():
                        if field.attrname != result:
                            self._validated_data.pop(field.attrname, None)
                
