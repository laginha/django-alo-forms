from django.forms import *
from .mixins import QueryFormMixin
from .operators import AND, OR


class QueryModelForm(ModelForm, QueryFormMixin):
    def __init__(self, *args, **kwargs):
        super(QueryModelForm, self).__init__(*args, **kwargs)
        self.set_meta()
        choice_fields = (ModelChoiceField, ModelMultipleChoiceField)
        for field in self.fields.values():
            if not isinstance(field, choice_fields):
                field.required = False
                    
    def full_clean(self):
        super(QueryModelForm, self).full_clean()
        self.clean_extralogic()


class QueryForm(Form, QueryFormMixin):    
    def __init__(self, *args, **kwargs):
        super(QueryForm, self).__init__(*args, **kwargs)
        self.set_meta()
    
    def full_clean(self):
        super(QueryForm, self).full_clean()
        self.clean_extralogic()
