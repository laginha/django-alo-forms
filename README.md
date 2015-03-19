# django-alo-forms

Add extra logic to your Django forms!


## Install

    pip install django_alo_forms


## Basic usage

in *forms.py*

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
        lookups = {
            # field_name: model_field__lookups
            'year': 'publication_date__year',
            'title': 'title__icontains',
            'genre': 'genres',
            'author': 'author_id',
            'house': 'publishing_house__id',
        }
        extralogic = [
            # Combine the form fields with boolean logic
            AND('genre', OR('author', 'house')) 
            # if 'genre' provided, so should also be either 'author' or 'house'
        ]

class BookModelForm(forms.QueryModelForm):
    
    class Meta:
        model = Book
        fields = (
            'publication_date', 'title', 'genres', 
            'author', 'publishing_house'
        )
        lookups = {
            # field_name: model_field__lookups
            'publication_date': 'publication_date__year',
            'title': 'title__icontains',
        }
        extralogic = [
            # Combine the form fields with boolean logic
            AND('genres', OR('author', 'publishing_house'))
            # if 'genre' provided, so should also be either 'author' or 'house' 
        ]
```

in *views.py*

```python
from .forms import BookForm
from .models import Book

def example(request):
    form = BookForm(request.GET)
    if form.is_valid():
        # form.parameters is like form.cleaned_data but 
        # with lookups applied and without empty values
        Book.objects.filter(**form.parameters)
        ...
    ...
```

## Other meta options

### multifield_lookups

Group multiple fields to a single lookup. Useful for ranges and geo-lookups.

```python
from django.contrib.gis.measure import D

class StoreForm(forms.QueryForm):
    books  = forms.IntegerField(required=False)
    range  = forms.IntegerField(required=False)
    center = forms.PointField(required=False)
    radius = forms.IntegerField(required=False)
    
    class Meta:
        multifield_lookups = {
            # tuple_of_field_names: callable_that_returns_a_dict
            ('center', 'radius'): lambda center,radius: {
                'stores__distance': (center, D(km=radius))
            },
            ('books', 'range'):  lambda books,range: {
                'pages__range': (books-range, books+range)
            },
        }
        extralogic = [
            AND('books', 'ranges'),
            AND('center', 'radius'),   
        ]
```

### no_defaults

By default, `QueryForm.parameter` and `QueryModelForm.parameter` instance attribute use the `initial` field's argument as the default value when no input is given for that particular field.

```python
class BookForm(forms.QueryForm):
    pages = forms.IntegerField(required=False)
    range = forms.IntegerField(required=False, initial=50)
    
    class Meta:
        multifield_lookups = {
            ('pages', 'range'):  lambda pages,range: {
                'pages__range': (pages-range, pages+range)
            },
        }
        extralogic = [
            # no need to add AND('pages', 'range')
            # since 'range' has a default value (50)
        ]
```

To disable this feature, set `no_defaults` meta option to `True`.
