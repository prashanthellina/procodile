# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="karthik"
__date__ ="$Oct 16, 2009 4:11:52 PM$"

from procodile.repository.server.core.models import *

user = User.objects.get(username='core')
cats = Generator.objects.filter(user=user)
for cat in cats:
    print cat.gen_id
    CategoryTree.objects.create(category=cat)
