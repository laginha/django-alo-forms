from django.contrib.gis.forms import *
from django.contrib.gis.geos import MultiPoint, Point
from django.contrib.gis.measure import D
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
import math


class CoordsField(CharField):
    def __init__(self, latitude_first=False, **kwargs):
        self.latitude_first = latitude_first
        kwargs['error_messages'] = {
            'invalid': _('Enter valid coordinate numbers.'),
            'no_pair': _('Enter a pair of numbers, separated by a comma.'),
            'out_of_range': _('Enter coordinates within range'),
        }
        super(CoordsField, self).__init__(**kwargs)
        
    def to_python(self, value):
        if not value:
            return None
        in_range = lambda lon,lat: (-90 < lat < 90) and (-180 < lon < 180)
        coords = value.split(',')
        if len(coords) != 2:
            raise ValidationError(self.error_messages['no_pair'])
        try:
            x,y = [float(each) for each in coords]
        except ValueError:
            raise ValidationError(self.error_messages['invalid'])
        else:
            if math.isnan( x ) or math.isnan( y ):
                raise ValidationError(self.error_messages['invalid'])
            elif self.latitude_first:
                if in_range(y, x):
                    return Point(y, x)
            elif in_range(x, y):
                return Point(x, y)
            raise ValidationError(self.error_messages['out_of_range'])
            

class BoundingBoxWidget(MultiWidget):
    def __init__(self, attrs=None):
        widgets = (CoordsField.widget, CoordsField.widget)
        super(BoundingBoxWidget, self).__init__(widgets, attrs)
    
    def decompress(self, value):
        if value is None:
            return [None, None]
        return [Point(*each) for each in value[0]]


class BoundingBoxField(MultiValueField):
    def __init__(self, latitude_first=False, **kwargs):
        self.latitude_first = latitude_first
        fields = (
            CoordsField(latitude_first=latitude_first),
            CoordsField(latitude_first=latitude_first),
        )
        super(BoundingBoxField, self).__init__(
            fields=fields, widget=BoundingBoxWidget, **kwargs)
        
    def compress(self, data_list):
        if len(data_list)==2:
            return MultiPoint(*data_list).envelope
        return None


class CircleField(CoordsField):
    def __init__(self, distance=5, unit='km', **kwargs):
        self.distance = D(**{unit: distance})
        super(CircleField, self).__init__(**kwargs)
        
    def to_python(self, value):
        if not value:
            return None
        point = super(CircleField, self).to_python(value)
        return (point, self.distance)
