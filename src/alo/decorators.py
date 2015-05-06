from django.http import HttpRequest
try:
    from django.http import JsonResponse
    native_json_response = True
except ImportError:
    from easy_response.http import JsonResponse
    native_json_response = False
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
            
            def error_response(form):
                content = {'Errors': form.errors}
                if native_json_response:
                    return JsonResponse(content, status=400, safe=False)
                else:
                    return JsonResponse(content, status=400)
            
            def validate(request):
                request.form = self.form_class(**get_form_kwargs(each))
                if request.form.is_valid():
                    return view(*args, **kwargs)
                return error_response(request.form)
                
            for each in args:
                if isinstance(each, HttpRequest):
                    return validate( each )
            return validate( args[0] )        
        
        return wrapper
        