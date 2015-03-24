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

## Decorator

Instead of the example view above, you can use the `validate` decorator as follows:

```python
from alo.decorators import validate
from .forms import BookForm
from .models import Book

@validate(BookForm)
def example(request):
    # enters view if form is valid
    Book.objects.filter(**form.parameters)
    ...
```

If `form` is not valid, `validate` returns a JsonResponse with `form.errors` as content and status code `400`. 

It is worth noting that `validate` works in any kind of views (function-base, class-bases, custom-bases) since it scans the view arguments for the `HttpRequest` object to validate the form.

Besides, `validate` is able to detect if the given form class is a subclass `Form` or `ModelForm`. In case of the latter, the decorator instantiates the form with the `instance` argument if the *named group* `pk` is present in the *urlpattern* (useful for getting or updating a resource). You can change the expected *named group* using the decorator argument `add_instance_using`.


## Other fields

Besides the fields that django already provides, there are three more fields that you may find useful: `CoordsField`, `BoundingBoxField` and `CircleField`. All require the **GEOS library** to be available.

### CoordsField

```python
from alo import forms 

class CityForm(forms.QueryForm):
    coords = forms.CoordsField()
    
    class Meta:
        lookups = {
            'coords': 'area__contains'
        }
```

- inherits from `CharField`
- similar to `PointField` but with a friendlier input format
- expected input format: `'<float>,<float>'`
- converts the input to a `Point`
- takes an additional argument: `latitude_first` (default to `False`). If set to `True`, it is expected that the first given `float` to be the latitude and the second the longitude.

### BoundingBoxField

```python
from alo import forms 

class StoreForm(forms.QueryForm):
    box = forms.BoundingBoxField()
    
    class Meta:
        lookups = {
            'box': 'point__contained'
        }
```

- inherits directly from `MultiValueField`
- expected inputs: `<fieldname>_0` and `<fieldname>_1`
- converts the input to a `Polygon`
- takes an additional argument: `latitude_first` (defaults to `False`)

### CircleField

```python
from alo import forms 

class StoreForm(forms.QueryForm):
    center = forms.CircleField(distance=5, unit='km') #default values
    
    class Meta:
        lookups = {
            'center': 'point__distance__lte'
        }
```

- inherits directly from `CoordsField`
- expected the same inputs as its parent class
- converts the input to a tuple: `(<Point>, <Distance object>)`
- takes two additional argument: `distance` (defaults to `5`) and `unit` (defaults to `km`)


## Other meta options

### multifield_lookups

Group multiple fields to a single lookup. Useful for ranges and geo-lookups.

```python
from django.contrib.gis.measure import D
from alo import forms

class StoreForm(forms.QueryForm):
    books  = forms.IntegerField(required=False)
    range  = forms.IntegerField(required=False)
    center = forms.PointField(required=False)
    radius = forms.IntegerField(required=False)
    
    class Meta:
        multifield_lookups = {
            # tuple_of_field_names: callable_that_returns_a_dict
            ('center', 'radius'): lambda center,radius: {
                'location__distance_lte': (center, D(km=radius))
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
from alo import forms

class BookForm(forms.QueryForm):
    pages = forms.IntegerField(required=False)
    range = forms.IntegerField(required=False, initial=50)
    
    class Meta:
        extralogic = [
            # no need to add AND('pages', 'range')
            # since 'range' has a default value (50)
        ]
```

To disable this feature, set `no_defaults` meta option to `True`.

