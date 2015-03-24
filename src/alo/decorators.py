from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.forms import ModelForm
from functools import wraps


class validate(object):
    def __init__(self, form_class, add_instance_using='pk'):#, extra=None):
        self.form_class = form_class
        self.add_instance_using = add_instance_using
        # self.extra = extra
        
    def __call__(self, view):
        
        @wraps(view)
        def wrapper(*args, **kwargs):
            
            def get_form_kwargs(request):
                data = request.GET if request.method=='GET' else request.POST
                form_kwargs = {'data': data}
                if not hasattr(request, "FILES"): 
                    form_kwargs['files'] = request.FILES
                if issubclass(self.form_class, ModelForm) and kwargs:
                    value = kwargs.get(self.add_instance_using, None)
                    if value != None:
                        model = self.form_class.Meta.model
                        instance = get_object_or_404(model, pk=value)
                        form_kwargs['instance'] = instance    
                # if self.extra != None:
                #     form_kwargs.update(self.extra(request))
                return form_kwargs
                
            for each in args:
                if isinstance(each, HttpRequest):
                    each.form = self.form_class(**get_form_kwargs(each))
                    if each.form.is_valid():
                        return view(*args, **kwargs)
                    return JsonResponse(each.form.errors, status=400, safe=False)
        
        return wrapper
        