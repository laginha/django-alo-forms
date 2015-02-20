from django.db import models
from django.utils import timezone
        
    
class Author( models.Model ):
    name = models.CharField( max_length=100 )
    gender = models.CharField( max_length=1, 
        choices=(('M', 'male'),('F','female')) )
    birthday = models.DateField( default=timezone.now )
    
    def __str__(self):
        return self.name


class Genre( models.Model ):
    name = models.CharField(unique=True, max_length=100)        

    def __str__(self):
        return self.name


class Book( models.Model ):
    author = models.ForeignKey( Author )
    title = models.CharField( max_length=100 )
    genres = models.ManyToManyField( Genre )
    publication_date = models.DateField( default=timezone.now )
    number_of_pages = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.title
