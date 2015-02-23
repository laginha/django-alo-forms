from django.http import JsonResponse
from .forms import BookModelForm, BookForm

def example(request):
    form = BookForm(request.GET)
    if form.is_valid():
        return JsonResponse(form.cleaned_data)
    return JsonResponse(form.errors)
    