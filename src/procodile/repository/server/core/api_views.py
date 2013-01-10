import os
import sys
import shutil
import traceback
import xml.etree.ElementTree as etree
from cStringIO import StringIO

import Image

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse

from procodile.utils import get_random_name
from procodile.repository.utils import RepositoryException

from procodile.repository.server.utils import add_packages_from_zip, store_file
from procodile.repository.server.config import Config as config

from procodile.repository.server.core.utils import apiresponse
from procodile.repository.server.core.utils import api_login_required
from procodile.repository.server.core.utils import compute_cache_path
from procodile.repository.server.core.utils import get_package_path
from procodile.repository.server.core import query

ITEMS_PER_PAGE = 100

def register(request):
    username = request.POST['username']
    email = request.POST['email']
    password = request.POST['password']

    try:
        User.objects.create_user(username=username,
                                 email=email,
                                 password=password)
    except:
        return apiresponse("Username already exists", code='err_record')

    return apiresponse()

def login_user(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(username=username, password=password)

    if user is not None:
        if user.is_active:
            login(request, user)
            return apiresponse()
        else:
            return apiresponse(code='inactive_usr')

    else:
        return apiresponse(code='invalid_usrpwd')

def logout_user(request):
    logout(request)
    return apiresponse()

def make_parse_fn(request, err):
    def parse_meta(package_xml, package_id, images):
        doc = etree.parse(package_xml)
        pack_id = package_id.split('.', 1)[-1] # remove username
        pack_entry, ver = query.update_package_table(doc, request.user,
                                                     pack_id, err)

        if err: return err

        gnodes = doc.findall('//generator')
        for gnode in gnodes:
            gen = query.update_generator(gnode, request.user, pack_entry,
                                         pack_id, ver)
            query.update_relations(gnode, request.user, gen,
                                   request.get_host(), pack_id)
            query.update_thumbnails(images, gen, gnode.get('id'))

    return parse_meta

def bug_report(request):
    content = None
    user = None
    if request.user.is_authenticated():
        user = request.user

    data = StringIO(request.raw_post_data)
    type = data.readline().strip()
    desc = data.readline().strip()
    file_name = data.readline()

    if file_name:
        file_name = file_name.strip()
        content = ContentFile(data.read())

    query.update_bug(user, type, desc, file_name, content)

    return apiresponse()


@api_login_required
def upload(request, data=None, phome=None, con_len=None):
    try:
        err = {}
        tmp_fname = get_random_name()

        if not os.path.exists(config.tmp_dir):
            os.makedirs(config.tmp_dir)

        tmp_fpath = os.path.join(config.tmp_dir, tmp_fname)
        tmp_dirpath = tmp_fpath + '_dir'

        package_data = StringIO(data) if data \
                       else StringIO(request.raw_post_data)
        username = request.user.username

        package_home = phome or package_data.readline().strip()
        package_home = '.'.join([username, package_home]).strip('.')

        content_length = con_len or int(package_data.readline().strip())
        store_file(tmp_fpath, package_data, content_length, config.chunk_size)

        callback_fn = make_parse_fn(request, err)
        num_package_dirs = add_packages_from_zip(tmp_fpath, tmp_dirpath,
                              package_home, config.repo_dir, callback_fn)
                              
    except RepositoryException, e:
        return apiresponse(e.message, 'err')
    except:
        print ''.join(traceback.format_exception(*sys.exc_info()[:3]))

    finally:
        if os.path.exists(tmp_fpath):
            os.remove(tmp_fpath)

        if os.path.exists(tmp_dirpath):
            shutil.rmtree(tmp_dirpath)

    response = apiresponse(err['message'], err['code']) if err else\
               apiresponse("%s Packages added" % num_package_dirs)

    return response

def download(request, _id):
    gen = query.get_generator(_id)
    if not gen:
        return apiresponse(code='err_record')

    pack_path = get_package_path(gen)
    zip_file = '.'.join([pack_path, 'zip'])

    if not os.path.exists(zip_file):
        return apiresponse(code='err_record')

    data = open(zip_file, 'rb').read()

    resp = HttpResponse(mimetype='application/zip')
    resp['Content-Disposition'] = 'attachment; filename=%s.zip' % _id
    resp.write(data)

    pack = gen.package
    num_downloaded = pack.num_downloaded+1 if pack.num_downloaded else 1
    pack.num_downloaded = num_downloaded
    pack.save()

    return resp

def list_view(request, list_type, ordering='popular', search_term=None,
              page_no=1, num=ITEMS_PER_PAGE):
    num = num or ITEMS_PER_PAGE

    type = 'get_%s_list' %list_type
    fn = getattr(query, type)

    ordering = 'views' if ordering == 'popular' else 'views'
    entries = fn(ordering, search_term)

    paginator = Paginator(entries, int(num))
    try:
        page = paginator.page(int(page_no))
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages)

    return apiresponse(data=page.object_list)

def item_view(request, item_type, item_name, ordering='relevance',
              search_term=None, page_no=1, num=ITEMS_PER_PAGE):

    type = 'get_%s_info' %item_type
    fn = getattr(query, type)
    values = fn(item_name)

    if item_type == 'generator':
        gen = query.get_generator(item_name)
        if gen:
            views = gen.views+1 if gen.views else 1
            values['views'] = views
            gen.views = views
            gen.save()
    
    code = 'success' if values else 'err_record'

    return apiresponse(code=code, data=values)

def item_list_view(request, item_type, item_name, item_list_type,
              ordering='relevance', search_term=None,
              page_no=1, num=ITEMS_PER_PAGE):

    type = 'get_%s_list' %item_list_type
    fn = getattr(query, type)

    item_name = query.get_user(item_name) if item_type == 'user' else item_name
    keywords = {str(item_type): item_name}
    values = fn(ordering, search_term, **keywords)

    code = 'success' if values else 'err_record'

    return apiresponse(code=code, data=values)

@api_login_required
def tag_view(request, generator_id):
    tags = request.POST
    query.update_tag(tags, request.user, generator_id)

    return apiresponse()

def get_image_path(generator_id, fname, size=None):
    gen = query.get_generator(generator_id)
    pack_path = get_package_path(gen)

    pack_id = gen.package.pack_id
    gen_id = gen.gen_id.split(pack_id, 1)[-1].lstrip('.')

    image_path = os.path.sep.join([pack_path, 'screenshots', gen_id, fname])

    if size:
        id = '+'.join([generator_id, fname, size])
        fsize = [int(s) for s in size.split('x', 1)]
        thumb_path = compute_cache_path(config.cache_dir, id)
        if not os.path.exists(thumb_path):
            im = Image.open(image_path)
            im.thumbnail(fsize, Image.ANTIALIAS)
            im.save(thumb_path, "JPEG")
        image_path = thumb_path

    return image_path

def image_view(request, generator_id, fname, size=''):
    image_path = get_thumb_path(generator_id, fname, size)

    if not os.path.exists(image_path):
        return apiresponse(code='err_record')

    data = open(image_path, 'rb').read()

    resp = HttpResponse(mimetype='image/%s' % image_path.rsplit('.', 1)[-1])
    resp['Content-Disposition'] = 'attachment; filename=%s%s' % (size, fname)
    resp.write(data)

    return resp

def reset_view(request, reset_type=None):
    query.reset(reset_type)
    return apiresponse()
