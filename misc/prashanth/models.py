from django.db import models

class Generator(models.Model):
    id  = models.IntegerField(primary_key=True)
#    user = models.ForeignKey('User')
    user_id = models.IntegerField()
    version = models.CharField(max_length=20)
    path = models.URLField(verify_exists=False, max_length=100, blank=True)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    config = models.TextField(blank=True)
    views = models.IntegerField(blank=True)
    package = models.ForeignKey('Package')

class GeneratorThumbnail(models.Model):
    id  = models.IntegerField(primary_key=True)
    index = models.CharField(max_length=100)
    type = models.CharField(max_length=10)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    thumb_path = models.CharField(max_length=100)
    generator = models.ForeignKey('Generator')

class GeneratorRelationship(models.Model):
    gen1_id = models.CharField(max_length=100)
    gen2_id = models.CharField(max_length=100)
    type = models.CharField(max_length=50) #sub_generator, parent

class GeneratorTag(models.Model):
    user_id = models.CharField(max_length=100)
    generator = models.ForeignKey('Generator')
    tag = models.CharField(max_length=20) #:hate, :like

class CategoryTree(models.Model):
    generator = models.ForeignKey('Generator')

class Package(models.Model):
    id  = models.IntegerField(primary_key=True)
    user_id = models.CharField(max_length=100)
    version = models.FloatField()
    path = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(max_length=100, blank=True)
    num_downloaded = models.IntegerField(blank=True)
    date_uploaded = models.DateTimeField(auto_now_add=True)