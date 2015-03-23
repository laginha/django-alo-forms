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
        response = decorator(view)(request)
        self.assertNotEqual(response.content, 'success')
        request = factory.get('', {'a':1, 'b':1})
        response = decorator(view)(request)
        self.assertEqual(response.content, 'success')
        request = factory.get('')
        response = decorator(view)(request)
        self.assertEqual(response.content, 'success')
    
    
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
        
    def test_no_defaults(self):
        
        class Form(QueryForm):
            a = Field(required=False, initial=1)
            
            class Meta:
                no_defaults = True
        
        f = Form({})
        self.assertTrue(f.is_valid())
        self.assertFalse('a' in f.validated_data)
        self.assertFalse('a' in f.parameters)
    
    def test_is_valid_with_or(self):
        
        class Form(QueryForm):
            a, b, c = A, B, C
    
            class Meta:
                extralogic = [
                    OR('a', 'b', 'c'),
                ]
        
        f = Form({})
        self.assertTrue(f.is_valid())
        f = Form({'a':1})
        self.assertTrue(f.is_valid())
        f = Form({'b':1})
        self.assertTrue(f.is_valid())
        f = Form({'c':1})
        self.assertTrue(f.is_valid())
        f = Form({'a':1, 'b':1})
        self.assertTrue(f.is_valid())
        f = Form({'a':1, 'b':1, 'c':1})
        self.assertTrue(f.is_valid())
    
    def test_is_valid_with_and(self):
        
        class Form(QueryForm):
            a, b, c = A, B, C
    
            class Meta:
                extralogic = [
                    AND('a', 'b', 'c'),
                ]
        
        f = Form({})
        self.assertTrue(f.is_valid())
        f = Form({'a':1})
        self.assertFalse(f.is_valid())
        f = Form({'a':1, 'b':1})
        self.assertFalse(f.is_valid())
        f = Form({'a':1, 'b':1, 'c':1})
        self.assertTrue(f.is_valid())
        
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
        assert str(logic[2]) == "( c AND ( d OR e ) AND a )"
        assert len(logic[2]) == 4
                
        assert isinstance(logic[3], OR)
        assert isinstance(logic[3].operands[0], AND)
        assert isinstance(logic[3].operands[1], Field)
        assert isinstance(logic[3].operands[0].operands[0], Field)
        assert isinstance(logic[3].operands[0].operands[1], Field)
        assert isinstance(logic[3].operands[0].operands[2], Field)
        assert str(logic[3]) == "( ( b AND c AND d ) OR e )" 
        assert len(logic[3]) == 4
        