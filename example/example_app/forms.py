from alo import forms
from alo.operators import AND, OR
from .models import Book


class BookModelForm(forms.QueryModelForm):
    class Meta:
        model = Book
        fields = ('publication_date', 'title', 'genres', 'author')
        lookups = {
            'publication_date': 'publication_date__year',
            'title': 'title__icontains',
        }
        extralogic = [
            AND('genres', OR('author', 'title'))   
        ]


class BookForm(forms.QueryForm):
    year   = forms.IntegerField(required=False, min_value=1970, max_value=2012)
    range  = forms.IntegerField(required=False, initial=1)
    title  = forms.CharField(required=False)
    genre  = forms.CharField(required=False)
    author = forms.CharField(required=False)
    
    class Meta:
        lookups = {
            'year': 'publication_date__year',
            'title': 'title__icontains',
            'genre': 'genres',
            'author': 'author_id',
        }
        multifield_lookups = {
            ('year', 'range'): lambda year,range: {
                'publication_date__year__range': (year-range, year+range)
            },
        }
        extralogic = [
            AND('genre', OR('author', 'title')),
            AND('range', 'year')
        ]
    