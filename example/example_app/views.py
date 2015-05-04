from django.http import JsonResponse
from .forms import BookModelForm, BookForm

def example(request):
    form = BookModelForm(request.GET)
    if form.is_valid():
        return JsonResponse({
            'cleaned_data': form.cleaned_data,
            'parameters': form.parameters,
            'validated_data': form.validated_data,
        }, safe=False)
    return JsonResponse(form.errors)
    