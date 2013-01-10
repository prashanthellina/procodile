import os

from django import forms
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from procodile.repository.server.core.api_views import get_image_path, upload
from procodile.repository.server.core import query
from procodile.repository.server.config import Config as config

ITEMS_PER_PAGE = 9

class Category():
    def __init__(self, id, title):
        self.id = id
        self.title = title

def get_category_tree():
    categories = query.get_categories_list()
    parents = query.get_base_categories()

    cats = [(Category(cat[0], cat[0].rsplit('.', 1)[-1]), get_subcat(cat[1], [])) \
            for cat in categories if cat[0] in parents ]
    cats = dict(cats)

    return cats

def get_subcat(categories, subcats):
    for id, sub_cat in categories:
        subcats.append(Category(id, id.rsplit('.', 1)[-1]))
        if sub_cat:
           get_subcat(sub_cat, subcats)

    return subcats

def render_response(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req)
    args[1]['cats'] = get_category_tree()
    return render_to_response(*args, **kwargs)

def get_fimages(gen, size):
    fimages = []
    for fname in gen['images']:
        image_path = get_image_path(gen['generator_id'], fname, size)

        image_path = image_path.split(config.user_dir, 1)[-1]
        image_path = image_path.replace(os.path.sep, '/')

        fimages.append(image_path)

    return fimages

def gens_view(request, item_type=None, item_name=None,
              ordering='popular', search_term=None,
              page_no=1, num=ITEMS_PER_PAGE):
    num = num or ITEMS_PER_PAGE
    type = item_name or 'Popular'
    if item_type == 'category':
        type = item_name.rsplit('.', 1)[-1]

    item_name = query.get_user(item_name) if item_type == 'user' else item_name
    keywords = {str(item_type): item_name} if item_type else {}
    gens = query.get_generators_list(ordering, search_term, **keywords)

    for gen in gens:
        gen['fimages'] = get_fimages(gen, '160x120')
       
    paginator = Paginator(gens, int(num))
    try:
        gens = paginator.page(int(page_no))
    except (EmptyPage, InvalidPage):
        gens = paginator.page(paginator.num_pages)

    return render_response(request, 'ui/home.html', {
        'type': type,
        'gens': gens,
        'item_type': item_type,
        'item_name': item_name,
        'top_authors': get_top_authors(),
        'recent_gens': get_recent_gens()})

def get_top_authors():
    packs = query.get_packages_list('popular', limit=4)

    unique = set()
    top_authors = []
    
    for pack in packs:
        if pack['username'] not in unique:
            unique.add(pack['username'])
            top_authors.append(pack['username'])

    return top_authors

def get_recent_gens():
    gens = query.get_generators_list('recent', limit=4)
    for gen in gens:
        gen['fimages'] = get_fimages(gen, '30x30')

    return gens

def gen_view(request, item_name=None):
    gen_info = query.get_generator_info(item_name)

    gen = query.get_generator(item_name)
    if gen:
        views = gen.views+1 if gen.views else 1
        gen_info['views'] = views
        gen.views = views
        gen.save()

    gen_info['fimages'] = get_fimages(gen_info, '180x120')

    package_info = query.get_package_info(gen_info['package_id'])

    for gen in package_info['gens']:
        gen['fimages'] = get_fimages(gen, '30x30')

    user=query.get_user(package_info['username'])
    user_top = query.get_generators_list('popular', user=user, limit=5)
    for gen in user_top:
        gen['fimages'] = get_fimages(gen, '30x30')

    return render_response(request, 'ui/generator.html', {
        'gen': gen_info,
        'package': package_info,
        'user_top': user_top
        })

def pack_view(request, item_name=None):
    pass

def user_view(request, username):
    user=query.get_user(username)
    user_info = query.get_user_info(record=user)

    for gen in user_info['favs']:
        gen['fimages'] = get_fimages(gen, '30x30')

    user_gens = query.get_generators_list(user=user, limit=10)
    for gen in user_gens:
        gen['fimages'] = get_fimages(gen, '30x30')

    user_packs = query.get_packages_list(user=user)
    for pack in user_packs:
        for gen in pack['gens'][:1]:
            pack['fimages'] = get_fimages(gen, '30x30')

    return render_response(request, 'ui/user.html', {
        'username': username,
        'user_info': user_info,
        'user_gens': user_gens,
        'user_packs': user_packs
        })

class RegisterForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs=\
                {'class':'text'}), max_length=15)
    email = forms.EmailField(widget=forms.TextInput(attrs=\
                {'class':'text'}))
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

def register(request):    
    error = None
    form = RegisterForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

            if password1 != password2:
                error = "Re-enter password correctly."

            try:
                if User.objects.get(username=username):
                    error = "Username already exists."
            except User.DoesNotExist:
                pass

            if error:
                return render_response(request, 'ui/register.html', {
                                    'form': form,
                                    'avoid': True,
                                    'error': error
                                    })

            User.objects.create_user(username=username,
                                     email=email,
                                     password=password1)
            user = authenticate(username=username, password=password1)
            login(request, user)
            
            return HttpResponseRedirect(reverse('home_page'))

    return render_response(request, 'ui/register.html', {
        'form': form,
        'avoid': True,
    })

class LoginForm(forms.Form):
    username = forms.CharField(max_length=50)
    password = forms.CharField(max_length=50)

def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            next = request.POST['next'] if 'next' in request.POST else ''
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                else:
                    return render_response(request, 'ui/login.html', {
                                'next': next,
                                'form': form,
                                'avoid': True,
                                'error': "Your account is de-activated"
                                })

            else:
                return render_response(request, 'ui/login.html', {
                                'next': next,
                                'form': form,
                                'avoid': True,
                                'error': "Your Username or Password was incorrect"
                                })
                                
            return HttpResponseRedirect(next or reverse('home_page'))
    else:
        next = request.GET['next'] if 'next' in request.GET else ''
        form = LoginForm()

    return render_response(request, 'ui/login.html', {
        'next': next,
        'form': form,
        'avoid': True
    })

def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse('home_page'))

def download_gen(request, _id):
    return HttpResponseRedirect(reverse('download', args=(_id,)))

class UploadForm(forms.Form):
    package_home = forms.CharField(widget=forms.TextInput(attrs=\
                {'class':'text'}), max_length=20)
#    repo = forms.ChoiceField(choices=('same', 'remote'))
    package  = forms.FileField(widget=forms.FileInput(attrs=\
                {'class':'text'}))
@login_required
def upload_gen(request):
    if request.method == 'POST': 
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            package_home = form.cleaned_data['package_home']
            package = request.FILES['package']
            upload(request, package.read(), package_home, package.size)

            return HttpResponseRedirect(reverse('home_page')) # Redirect after POST
        else:
                return render_response(request, 'ui/upload.html', {
                'error': 'File Not Uploaded, Please verify the details',
                'form': form,
                })
    else:
        form = UploadForm() # An unbound form

    return render_response(request, 'ui/upload.html', {
        'form': form,
    })

@login_required
def tag_view(request, generator_id=None):
    tags = request.POST
    try:
        query.update_tag(tags, request.user, generator_id)
    except:
        pass
    
    return HttpResponseRedirect('/generator/%s' % generator_id)