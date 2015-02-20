from django.forms.fields import *
from django.forms import Form, ModelForm
from .mixins import QueryFormMixin
from .operators import AND, OR


class QueryModelForm(ModelForm, QueryFormMixin):
    def __init__(self, *args, **kwargs):
        super(QueryModelForm, self).__init__(*args, **kwargs)
        self.set_meta()
    
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
