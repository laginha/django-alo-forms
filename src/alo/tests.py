#!/usr/bin/env python
# encoding: utf-8
from django.test import TestCase
from .forms import QueryForm, Field
from .operators import AND, OR, BaseOperator


A = Field()
B = Field()
C = Field()
D = Field()
E = Field()

class SomeForm(QueryForm):
    a, b, c, d, e = A, B, C, D, E
    
    class Meta:
        extralogic = [
            AND('b', 'c', 'd'),
            OR('e', 'a', 'b'),
            AND('c', OR('d', 'e'), 'a'),
            OR(AND('b', 'c', 'd'), 'e'),
        ]


class FormTestCase(TestCase):
    
    def test_logic(self):
        form = SomeForm()
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
        assert str(logic[1]) == "( e OR a OR b )"
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
        