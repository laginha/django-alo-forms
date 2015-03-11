# django-alo-forms

## Install

    pip install django_alo_forms


## Usage

Add extra logic to your Django forms!

```python
from alo import forms
from alo.operators import AND, OR

class BookForm(forms.QueryForm):
    # Django form fields
    year   = forms.IntegerField(required=False, min_value=1970, max_value=2012)
    title  = forms.CharField(required=False)
    genre  = forms.CharField(required=False)
    author = forms.CharField(required=False)
    house  = forms.CharField(required=False)
 
    class Meta:
        aliases = {
            # query_name: model_field__lookups
            'year': 'publication_date__year',
            'title': 'title__icontains',
            'genre': 'genres',
            'author': 'author_id',
            'house': 'publishing_house__id',
        }
        extralogic = [
            # Combine the form fields with boolean logic
            AND('genre', OR('author', 'house'))   
        ]

class BookModelForm(forms.QueryModelForm):
    
    class Meta:
        model = Book
        fields = (
            'publication_date', 'title', 'genres', 
            'author', 'publishing_house'
        )
        aliases = {
            # query_name: model_field__lookups
            'publication_date': 'publication_date__year',
            'title': 'title__icontains',
        }
        extralogic = [
            # Combine the form fields with boolean logic
            AND('genres', OR('author', 'publishing_house'))   
        ]
```

in *urls.py*

```python
from .forms import BookForm
from .models import Book

def example(request):
    form = BookForm(request.GET)
    if form.is_valid():
        # form.parameters is like form.cleaned_data but 
        # with aliases applied and without empty values
        Book.objects.filter(**form.parameters)
        ...
    ...
```
