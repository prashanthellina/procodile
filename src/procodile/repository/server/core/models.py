from django.db import models
from django.contrib.auth.models import User

class Package(models.Model):
    pack_id  = models.CharField(max_length=50)
    user = models.ForeignKey(User)
    version = models.CharField(max_length=20)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(max_length=100, blank=True)
    num_downloaded = models.IntegerField(null=True, blank=True)
    date_uploaded = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("pack_id", "user", "version")

    def __unicode__(self):
        return self.title

class Generator(models.Model):
    gen_id  = models.CharField(max_length=100)
    package = models.ForeignKey(Package)
    user = models.ForeignKey(User)
    version = models.CharField(max_length=20)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    parents = models.ManyToManyField('self', symmetrical=False,
                                     related_name='children', blank=True)
    config = models.TextField(blank=True)
    views = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("gen_id", "package", "version")

    def __unicode__(self):
        return self.title

class GeneratorRelations(models.Model):
    from_gen = models.ForeignKey(Generator)
    to_gen = models.CharField(max_length=100)
    relation = models.CharField(max_length=100)

    def __unicode__(self):
        return self.relation

class Thumbnail(models.Model):
    generator = models.ForeignKey(Generator)
    index = models.CharField(max_length=100)
    fname = models.CharField(max_length=100)

    class Meta:
        unique_together = ("generator", "index")

    def __unicode__(self):
        return self.fname

class Tag(models.Model):
    user = models.ForeignKey(User)
    generator = models.ForeignKey(Generator)
    name = models.CharField(max_length=20) #:hate, :like
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "generator", "name")

    def __unicode__(self):
        return self.name

class CategoryTree(models.Model):
    category = models.ForeignKey(Generator)

    def __unicode__(self):
        return self.category

class Bugs(models.Model):
    user = models.ForeignKey(User, null=True)
    type = models.TextField()
    description = models.TextField()
    file = models.FileField(upload_to='bugs/%Y/%m/%d')
    machine_details = models.TextField(null=True) #TODO
    time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.type + ':\n' + self.description
