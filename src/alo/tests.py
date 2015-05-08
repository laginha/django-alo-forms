#!/usr/bin/env python
# encoding: utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client, RequestFactory
from django.http import HttpResponse
from .forms import QueryForm, QueryModelForm, Field
from .operators import AND, OR, BaseOperator
from .decorators import validate


A = Field(required=False)
B = Field(required=False)
C = Field(required=False)
D = Field(required=False)
E = Field(required=False)
F = Field(required=False)
            

class QueryModelFormTestCase(TestCase):
    
    def test_validate_decorator(self):
        
        class Form(QueryModelForm):
            class Meta:
                model = User
                fields = ('username', 'email')
                extralogic = [AND('username', 'email'),]
        
        def view(request, pk):
            return HttpResponse('success')
            
        def another_view(request, id):
            return HttpResponse('success')
                
        user = User.objects.create(username='user', email='user@email')
        factory = RequestFactory()
        decorator = validate(Form)
        
        request = factory.get('', {'username':1})
        response = decorator(view)(request, pk=user.pk)
        self.assertNotEqual(response.content, 'success')
        self.assertEqual(request.form.instance, user)
        
        request = factory.get('', {'username':'user', 'email':'1@email.com'})
        response = decorator(view)(request, pk=user.pk)
        self.assertEqual(response.content, 'success')
        self.assertEqual(request.form.instance, user)
        
        request = factory.get('')
        response = decorator(view)(request, pk=user.pk)
        self.assertNotEqual(response.content, 'success')
        self.assertEqual(request.form.instance, user)
        
        decorator = validate(Form, add_instance_using='id')
        request = factory.get('', {})
        response = decorator(another_view)(request, id=user.pk)
        self.assertNotEqual(response.content, 'success')
        self.assertEqual(request.form.instance, user)
        
        decorator = validate(Form, add_instance_using='id')
        request = factory.get('', {'username':1})
        response = decorator(another_view)(request, pk=user.pk)
        self.assertNotEqual(response.content, 'success')
        self.assertNotEqual(request.form.instance, user)
        

class QueryFormTestCase(TestCase):

    def test_BoundingBoxField(self):
        try:
            from .forms import BoundingBoxField
        except ImportError:
            return
            
        class Form(QueryForm):
            box = BoundingBoxField()
        
        lat0, lng0 = 40.0, -8.1 
        lat1, lng1 = 41.0, -9.1   
        f = Form({
            'box_0': '%s,%s'%(lng0,lat0),
            'box_1': '%s,%s'%(lng1,lat1),
        })
        self.assertTrue(f.is_valid())
        self.assertTrue('box' in f.cleaned_data)
        polygon1 = f.cleaned_data['box']
        self.assertEqual(polygon1.num_points, 5)
        self.assertEqual(polygon1, f.parameters['box'])
        
        class Form(QueryForm):
            box = BoundingBoxField(latitude_first=True)
            
            class Meta:
                lookups = {
                    'box': 'point__contained'
                }
            
        f = Form({
            'box_0': '%s,%s'%(lat0,lng0),
            'box_1': '%s,%s'%(lat1,lng1),
        })
        self.assertTrue(f.is_valid())
        self.assertTrue('box' in f.cleaned_data)
        polygon2 = f.cleaned_data['box']
        self.assertEqual(polygon2.num_points, 5)
        self.assertEqual(polygon2, f.parameters['point__contained'])
        self.assertEqual(polygon1, polygon2)
        
    def test_CoordsField(self):
        try:
            from .forms import CoordsField
        except ImportError:
            return
            
        lat, lng = 40.0, -8.1
        
        def assert_form(lat, lng, form):
            self.assertTrue(form.is_valid())
            self.assertTrue('coords' in form.cleaned_data)
            coords = form.cleaned_data['coords'].coords
            self.assertEqual(coords[0], lng)
            self.assertEqual(coords[1], lat)
            self.assertEqual(form.cleaned_data['coords'], form.parameters['coords'])
            
        class Form(QueryForm):
            coords = CoordsField()
        
        f = Form({'coords': '%s,%s'%(lng,lat)})
        assert_form(lat=lat, lng=lng, form=f)

        class Form(QueryForm):
            coords = CoordsField(latitude_first=True)
        
        f = Form({'coords': '%s,%s'%(lat,lng)})
        assert_form(lat=lat, lng=lng, form=f)

    def test_CircleField(self):
        try:
            from .forms import CircleField
        except ImportError:
            return
        
        class Form(QueryForm):
            center = CircleField()
        
        lat, lng = 40.0, -8.1
        f = Form({'center': '%s,%s'%(lng,lat)})
        self.assertTrue(f.is_valid())
        self.assertTrue('center' in f.cleaned_data)
        self.assertTrue(isinstance(f.cleaned_data['center'], tuple))
        coords = f.cleaned_data['center'][0].coords
        self.assertEqual(coords[0], lng)
        self.assertEqual(coords[1], lat)
        self.assertEqual(f.cleaned_data['center'], f.parameters['center'])

    def test_validate_decorator(self):
        
        class Form(QueryForm):
            a, b = A, B
    
            class Meta:
                extralogic = [AND('a', 'b'),]
        
        def view(request):
            return HttpResponse('success')
        
        factory = RequestFactory()
        decorator = validate(Form)
        request = factory.get('', {'a':1})
        wrapper = decorator(view)
        self.assertEqual(wrapper.__name__, view.__name__)
        self.assertNotEqual(wrapper(request).content, 'success')
        request = factory.get('', {'a':1, 'b':1})
        self.assertEqual(wrapper(request).content, 'success')
        request = factory.get('')
        self.assertEqual(wrapper(request).content, 'success')
    
    def test_lookups(self):
        
        class Form(QueryForm):
            a, b, c = A, B, C
    
            class Meta:
                lookups = {
                    'a': 'a__contains',
                    'b': 'b__id',
                }
            
        f = Form({'a': 1, 'b':1, 'c':1})
        lookups = f._meta.lookups.values()
        self.assertEqual(len(lookups), len(f.fields))
        self.assertTrue('a__contains' in lookups)
        self.assertEqual(f._meta.lookups['a'], 'a__contains')
        self.assertTrue('b__id' in lookups)
        self.assertEqual(f._meta.lookups['b'], 'b__id')
        self.assertTrue('c' in lookups)
        self.assertEqual(f._meta.lookups['c'], 'c')
        self.assertFalse('c__year' in lookups)
    
    def test_multifield_lookups(self):
        
        class Form(QueryForm):
            a, b = A, B
    
            class Meta:
                multifield_lookups = {
                    ('a', 'b'): lambda a,b: {'a__range': (a-b, a)}
                }
                
        f = Form({'a':2, 'b':1})
        lookups = f._meta.multifield_lookups
        self.assertTrue(('a', 'b') in lookups)
        self.assertTrue(f.is_valid())
        self.assertTrue('a__range' in f.parameters)
        self.assertTrue('a' in f.validated_data)
        self.assertTrue('b' in f.validated_data)
        self.assertEqual(f.parameters['a__range'], (1, 2))
        
    def test_parameters(self):
        
        class Form(QueryForm):
            a, b, c = A, B, C
    
            class Meta:
                lookups = {
                    'a': 'a__contains',
                    'b': 'b__id',
                    'c': 'c__year',
                }
        
        f = Form({'a': 1, 'b':1, 'c':1})
        self.assertTrue(f.is_valid())
        for fieldname,lookup in f._meta.lookups.items():
            self.assertTrue(f.parameters.get(lookup, None))
            self.assertEqual(f.cleaned_data[fieldname], f.parameters[lookup])
        f = Form({'a': 1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a__contains' in f.parameters)
        self.assertTrue('a' in f.cleaned_data)
        self.assertFalse('b__id' in f.parameters)
        self.assertTrue('b' in f.cleaned_data)
        
    def test_default_data(self):
        class Form(QueryForm):
            a = Field(required=False, initial=1)
        
        f = Form({})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.validated_data)
        self.assertTrue('a' in f.parameters)
        self.assertEqual(f.validated_data['a'], f.fields['a'].initial)
        self.assertEqual(f.validated_data['a'], f.parameters['a'])
        f = Form({'a': 2})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.validated_data)
        self.assertTrue('a' in f.parameters)
        self.assertNotEqual(f.validated_data['a'], f.fields['a'].initial)
        self.assertEqual(f.validated_data['a'], f.parameters['a'])
        
        class Form(QueryForm):
            a = Field(required=False, initial=1)
            b = Field(required=False)
            
            class Meta:
                extralogic = [AND('a', 'b')]
        
        f = Form({})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.validated_data)
        self.assertTrue('a' not in f.parameters)
        self.assertEqual(f.validated_data['a'], f.fields['a'].initial)
        
    def test_no_defaults(self):
        
        class Form(QueryForm):
            a = Field(required=False, initial=1)
            
            class Meta:
                no_defaults = True
        
        f = Form({})
        self.assertTrue(f.is_valid())
        self.assertFalse('a' in f.validated_data)
        self.assertFalse('a' in f.parameters)
    
    def test_required(self):
        class Form(QueryForm):
            a = Field()
            
            class Meta:
                required = ['a']
                
        f = Form()
        self.assertFalse(f.is_valid())
        f = Form({'a': 1})
        self.assertTrue(f.is_valid())
        
    def test_ignore(self):
        
        class Form(QueryForm):
            a, b = A, B
            
            class Meta:
                ignore = ['a']
                
        f = Form({'a': 1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.validated_data)
        self.assertFalse('a' in f.parameters)
        f = Form({'b': 1})
        self.assertTrue(f.is_valid())
        self.assertTrue('b' in f.validated_data)
        self.assertTrue('b' in f.parameters)
    
    def test_is_valid_with_or(self):
        
        class Form(QueryForm):
            a, b, c = A, B, C
    
            class Meta:
                extralogic = [
                    OR('a', 'b', 'c'),
                ]
        
        f = Form({})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' not in f.parameters)
        self.assertTrue('b' not in f.parameters)
        self.assertTrue('c' not in f.parameters)
        f = Form({'a':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertTrue('b' not in f.parameters)
        self.assertTrue('c' not in f.parameters)
        f = Form({'b':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' not in f.parameters)
        self.assertTrue('b' in f.parameters)
        self.assertTrue('c' not in f.parameters)
        f = Form({'c':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' not in f.parameters)
        self.assertTrue('b' not in f.parameters)
        self.assertTrue('c' in f.parameters)
        f = Form({'a':1, 'b':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertTrue('b' not in f.parameters)
        self.assertTrue('c' not in f.parameters)
        f = Form({'a':1, 'b':1, 'c':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertTrue('b' not in f.parameters)
        self.assertTrue('c' not in f.parameters)
        
        class Form(QueryForm):
            a, b = A, B
    
            class Meta:
                extralogic = [
                    OR('a', 'b', required=True),
                ]
        
        f = Form({})
        self.assertFalse(f.is_valid())
        self.assertTrue('a' not in f.parameters)
        self.assertTrue('b' not in f.parameters)
        f = Form({'a':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertTrue('b' not in f.parameters)
        f = Form({'b':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' not in f.parameters)
        self.assertTrue('b' in f.parameters)
        f = Form({'a':1, 'b':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertTrue('b' not in f.parameters)
    
    def test_is_valid_with_and(self):  
        
        class Form(QueryForm):
            a, b, c = A, B, C
    
            class Meta:
                extralogic = [
                    AND('a', 'b', 'c'),
                ]
        
        f = Form({})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' not in f.parameters)
        self.assertTrue('b' not in f.parameters)
        self.assertTrue('c' not in f.parameters)
        f = Form({'a':1})
        self.assertFalse(f.is_valid())
        f = Form({'a':1, 'b':1})
        self.assertFalse(f.is_valid())
        f = Form({'a':1, 'b':1, 'c':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertTrue('b' in f.parameters)
        self.assertTrue('c' in f.parameters)
        
        class Form(QueryForm):
            a = Field(required=False, initial=1)
            b = Field(required=False)
    
            class Meta:
                extralogic = [
                    AND('a', 'b'),
                ]
        
        f = Form({})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' not in f.parameters)
        self.assertTrue('b' not in f.parameters)
        f = Form({'a':1})
        self.assertTrue(f.is_valid())
        f = Form({'a':2})
        self.assertFalse(f.is_valid())
        f = Form({'a':1, 'b':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertTrue('b' in f.parameters)
        
        class Form(QueryForm):
            a = Field(required=False, initial=1)
            b = Field(required=False)
            c = Field(required=False)
    
            class Meta:
                extralogic = [
                    AND('a', 'b', 'c'),
                ]
                
        f = Form({'b':1})
        self.assertFalse(f.is_valid())
        f = Form({'a':1, 'b':1})
        self.assertFalse(f.is_valid())
        f = Form({'a':2, 'b':1})
        self.assertFalse(f.is_valid())
        
        class Form(QueryForm):
            a = Field(required=True)
            b = Field(required=False, initial=1)
    
            class Meta:
                extralogic = [
                    AND('a', 'b'),
                ]
        
        f = Form({})
        self.assertFalse(f.is_valid())
        f = Form({'a':1})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertEqual(f.parameters['a'], 1)
        self.assertTrue('b' in f.parameters)
        self.assertEqual(f.parameters['b'], 1)
        f = Form({'a':1, 'b':2})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertEqual(f.parameters['a'], 1)
        self.assertTrue('b' in f.parameters)
        self.assertEqual(f.parameters['b'], 2)
        f = Form({'b':1})
        self.assertFalse(f.is_valid())
        f = Form({'b':2})
        self.assertFalse(f.is_valid())
    
    def test_nexted_logic(self):
        
        class Form(QueryForm):
            a, b, c = A, B, C
    
            class Meta:
                extralogic = [
                    AND('a', OR('b', 'c')),
                ]
        
        f = Form({})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' not in f.parameters)
        self.assertTrue('b' not in f.parameters)
        self.assertTrue('c' not in f.parameters)
        f = Form({'a':1})
        self.assertFalse(f.is_valid())
        f = Form({'a':1, 'b':2})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertTrue('b' in f.parameters)
        self.assertTrue('c' not in f.parameters)
        f = Form({'a':1, 'c':2})
        self.assertTrue(f.is_valid())
        self.assertTrue('a' in f.parameters)
        self.assertTrue('b' not in f.parameters)
        self.assertTrue('c' in f.parameters)
        
        
    def test_extralogic(self):
        
        class Form(QueryForm):
            a, b, c, d, e, f = A, B, C, D, E, F
    
            class Meta:
                extralogic = [
                    AND('b', 'c', 'd'),
                    OR('e', 'a', 'f'),
                    AND('c', OR('d', 'e'), 'a'),
                    OR(AND('b', 'c', 'd'), 'e'),
                ]
        
        form = Form()
        logic = form._meta.extralogic
        assert len(logic) == 4
        
        assert isinstance(logic[0], AND)
        assert isinstance(logic[0].operands[0], Field)
        assert isinstance(logic[0].operands[1], Field)
        assert isinstance(logic[0].operands[2], Field)
        assert str(logic[0]) == "( b AND c AND d )"
        assert len(logic[0]) == 3
        
        assert isinstance(logic[1], OR)
        assert isinstance(logic[1].operands[0], Field)
        assert isinstance(logic[1].operands[1], Field)
        assert isinstance(logic[1].operands[2], Field)
        assert str(logic[1]) == "( e OR a OR f )"
        assert len(logic[1]) == 3
        
        assert isinstance(logic[2], AND)
        assert isinstance(logic[2].operands[0], Field)
        assert isinstance(logic[2].operands[1], OR)
        assert isinstance(logic[2].operands[2], Field)
        assert isinstance(logic[2].operands[1].operands[0], Field)
        assert isinstance(logic[2].operands[1].operands[1], Field)
        assert str(logic[2]) == "( c AND ( d OR e ) AND a )", str(logic[2])
        assert len(logic[2]) == 4
                
        assert isinstance(logic[3], OR)
        assert isinstance(logic[3].operands[0], AND)
        assert isinstance(logic[3].operands[1], Field)
        assert isinstance(logic[3].operands[0].operands[0], Field)
        assert isinstance(logic[3].operands[0].operands[1], Field)
        assert isinstance(logic[3].operands[0].operands[2], Field)
        assert str(logic[3]) == "( ( b AND c AND d ) OR e )" 
        assert len(logic[3]) == 4
        