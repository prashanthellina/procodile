from urlparse import urlparse
from itertools import chain

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from procodile.repository.server.core.models import *
from procodile.repository.server.core.utils import format_id, getvalues

def get_generator(generator_id, user=None):
    username, gen_id, version = format_id(generator_id)

    try:
        user = user or User.objects.get(username=username)
        ver = version or get_latest_version(gen_id, user)
        gen = Generator.objects.get(gen_id=gen_id, user=user, version=ver)
    except ObjectDoesNotExist:
        return None

    return gen

def get_package(package_id, user=None):
    username, pack_id, version = format_id(package_id)

    try:
        user = user or User.objects.get(username=username)
        package = Package.objects.get(pack_id=pack_id, user=user,
                                      version=version)
    except ObjectDoesNotExist:
        return None

    return package

def get_user(username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return None

    return user

def get_base_categories():
    cat_list = CategoryTree.objects.all()
    cat_gens = [c.category for c in cat_list]

    children = chain(*[get_children(g) for g in cat_gens])

    base_cats = set(cat_gens) - set(children)
    base_cats = ['.'.join([c.user.username, c.gen_id]) for c in base_cats]

    return base_cats

def get_categories_list(ordering=None, search_term=None, **kwargs):
    cat_list = CategoryTree.objects.filter(**kwargs)
    if search_term:
        cat_list = cat_list.category.filter(\
                            category__gen_id__icontains=search_term)

    nesting = [('.'.join([c.category.user.username, c.category.gen_id]), \
                get_tree(c.category)) for c in cat_list]
    
    return nesting

def get_tree(gen):
    tree = []
    children = get_children(gen)

    sub_children = []
    for child in children:
        sub_children = get_tree(child)
        tree.append(('.'.join([child.user.username, child.gen_id]),
                    sub_children))

    return tree

def get_children(gen):
    generator_id = '.'.join([gen.user.username, gen.gen_id])
    relatives = GeneratorRelations.objects.filter(to_gen=generator_id,
                                                  relation='parent')
    children = [r.from_gen for r in relatives]

    return children

def get_users_list(ordering=None, search_term=None, **kwargs):
    user_list = User.objects.filter(**kwargs)
    if search_term:
        user_list = user_list.filter(username__icontains=search_term)

    user_list = [get_user_info(record=u) for u in user_list]

    return user_list

def get_packages_list(ordering=None, search_term=None,
                      limit='all', **kwargs):
    core_user = get_user('core')
    
    if ordering == 'popular':
        ordering = '-num_downloaded'
    else:
        ordering = 'pack_id'

    pack_list = Package.objects.exclude(user=core_user).filter(**kwargs).\
                                                         order_by(ordering)

    if limit !='all':
        pack_list = pack_list[:limit]
    if search_term:
        pack_list = pack_list.filter(pack_id__icontains=search_term)
        
    pack_list = [get_package_info(record=p) for p in pack_list]

    return pack_list

def get_generators_list(ordering=None, search_term=None,
                        limit='all', **kwargs):
    core_user = get_user('core')

    if 'package' in kwargs:
        kwargs['package'] = get_package(kwargs.pop('package'))

    if 'category' in kwargs:
        gens_cat = GeneratorRelations.objects.filter(to_gen=kwargs['category'],
                                                     relation='category')
        
        gen_list = [g.from_gen for g in gens_cat if g.from_gen.user!=core_user]

    else:
        if ordering == 'popular':
            ordering = '-views'
        elif ordering == 'recent':
            ordering = '-package__date_uploaded'
        else:
            ordering = 'gen_id'
            
        gen_list = Generator.objects.exclude(user=core_user).filter(**kwargs).\
                                                             order_by(ordering)

        if limit !='all':
            gen_list = gen_list[:limit]
        if search_term:
            gen_list = gen_list.filter(gen_id__icontains=search_term)

    gen_list = [get_generator_info(record=g) for g in gen_list]

    return gen_list

def get_sub_generators_list(ordering=None, search_term=None, **kwargs):
    gen = get_generator(kwargs.pop('generator'))

    sub_gen_ids = get_relatives(gen, 'sub_gen', search_term=search_term)[0]

    sub_gens = [get_generator(id) for id in sub_gen_ids]
    sub_gens_info = [get_generator_info(record=s) for s in sub_gens]

    return sub_gens_info

def get_parents_list(ordering=None, search_term=None, **kwargs):
    gen = get_generator(kwargs.pop('generator'))

    parent_ids = get_relatives(gen, 'parent', search_term=search_term)[0]

    parents = [get_generator(id) for id in parent_ids]
    parents_info = [get_generator_info(record=p) for p in parents]

    return parents_info

def get_user_info(username=None, record=None):
    user_record = record or User.objects.select_related().get(username=username)

    if not user_record:
        return None

    fields = ['username', 'first_name', 'last_name',
              'date_joined', 'last_login']
    values = getvalues(user_record, fields)

    values['num_generators'] = user_record.generator_set.count()
    values['num_packages'] = user_record.package_set.count()
    favs = Tag.objects.filter(user=user_record, name='.fav')
    values['favs'] = [get_generator_info(record=f.generator) for f in favs]

    return values

def get_package_info(package_id=None, record=None, user=None):
    pack_record = record or get_package(package_id, user)

    if not pack_record:
        return None

    fields = ['version', 'date_uploaded', 'title', 'description']
    values = getvalues(pack_record, fields)

    values['username'] = user.username if user else pack_record.user.username
    values['package_id'] = make_package_id(pack_record, values['username'])

    gens = pack_record.generator_set.all()
    values['num_generators'] = gens.count()
    values['generator_ids'] = [make_generator_id(g, values['username'])
                                              for g in gens[:50]]
    values['gens'] = [get_generator_info(record=g) for g in gens[:50]]

    return values

def get_relatives(gen, type, limit=None, user=None, search_term=None):
    all_relations = gen.generatorrelations_set.filter(relation=type)

    if search_term:
        all_relations = all_relations.filter(gen_id__icontains=search_term)

    total = all_relations.count()
    limit = limit or total
    relations = all_relations[:limit].values('to_gen')

    relations = [str(r['to_gen']) for r in relations]

    for i, generator_id in enumerate(relations):
        username, gen_id, version = format_id(generator_id)

        if not version and type != 'category':
            user = user or get_user(username)
            latest_ver = get_latest_version(gen_id, user)
            relations[i] = '-'.join([generator_id, latest_ver])

    return (relations, total)

def get_latest_version(gen_id, user):
    latest = Generator.objects.filter(gen_id=gen_id, user=user).\
                     order_by('version')
    latest_ver = latest[0].version if latest else ''
    
    return latest_ver

def get_generator_info(generator_id=None, record=None, user=None):
    gen = record or get_generator(generator_id, user)

    if not gen:
        return None

    fields = ['version', 'title', 'description']
    values = getvalues(gen, fields)
    values['username'] = user.username if user else gen.user.username

    values['generator_id'] = make_generator_id(gen, values['username'])
    values['package_id'] = make_package_id(gen.package, values['username'])

    values['num_likes'] = gen.tag_set.filter(name='.fav').count()
    
    sub_gens, num_sub_gens = get_relatives(gen, 'sub_gen', 50, user)
    values['sub_gens'] = sub_gens
    values['num_sub_gens'] = num_sub_gens

    parents, num_parents = get_relatives(gen, 'parent', 50, user)
    values['parents'] = parents
    values['num_parents'] = num_parents

    categories, num_categories = get_relatives(gen, 'category', 50, user)
    values['categories'] = categories
    values['num_categories'] = num_categories

    values['num_downloads'] = gen.package.num_downloaded
    values['date_uploaded'] = gen.package.date_uploaded

    images = gen.thumbnail_set.values('fname')
    values['images'] = [str(i['fname']) for i in images]

    return values

def update_tag(tags, user, generator_id):
    gen = get_generator(generator_id)

    if not gen:
        return None

    for tag, action in tags.iteritems():
        if tag.startswith('.'):
            if action == 'add':
                Tag.objects.create(user=user, generator=gen, name=tag)
            else:
                Tag.objects.get(user=user, generator=gen, name=tag).delete()

def update_package_table(doc, user, pack_id, err):
    package = doc.getroot()
    title = package.get('title')
    desc = package.find('description')
    desc = (desc.text or '').strip() if desc is not None else ''
    version = package.get('version')
    try:
        pack_entry = Package.objects.create(pack_id=pack_id, user=user,
                               title=title, description=desc,
                               version=version)
    except:
        err['message']="Package with same version already exists"
        err['code']='err_record'
        return None, None
                           
    return pack_entry, version

def update_generator(gnode, user, pack_entry, pack_id, version):
    # gen_id in package.xml doesn't include package_home
    gen_id = '.'.join([pack_id, gnode.get('id')])

    title = gnode.find('title')
    title = (title.text or '').strip() if title is not None else ''

    desc = gnode.find('description')
    desc = (desc.text or '').strip() if desc is not None else ''

    config = gnode.find('config')
    params = config.getchildren()
    params = tuple([(param.get('name'), param.get('value'))
                    for param in params])

    fn = Generator.objects.create
    generator = fn(gen_id=gen_id, package=pack_entry, user=user, title=title,
                   version=version, description=desc, config=repr(params))

    return generator

def make_generator_id(gen, username):
    gen_id = '.'.join([username, gen.gen_id])
    gen_id = '-'.join([gen_id, gen.version])
    return gen_id

def make_package_id(pack, username):
    pack_id = '.'.join([username, pack.pack_id])
    pack_id = '-'.join([pack_id, pack.version])
    return pack_id

def make_gen_id(node, user, host, pack_id):
    id = node.get('id')
    version = node.get('version', '')

    repo_uri = node.get('repo', '')
    repo_uri = None if host == urlparse(repo_uri)[1] else repo_uri

    gen_id = '.'.join([user.username, pack_id, id, version]).strip('.')\
             if repo_uri=='' else ':'.join([repo_uri or '', id]).strip(':')

    return gen_id

def update_relations(gnode, user, gen, host, pack_id):
    sub_gens = gnode.findall('sub_generator')
    parents = gnode.findall('parent')
    categories = gnode.findall('category')

    fn = GeneratorRelations.objects.create

    for p in parents:
        fn(from_gen=gen, to_gen=make_gen_id(p, user, host, pack_id),
           relation='parent')

    for s in sub_gens:
        fn(from_gen=gen, to_gen=make_gen_id(s, user, host, pack_id),
           relation='sub_gen')

    for c in categories:
        fn(from_gen=gen, to_gen=make_gen_id(c, user, host, pack_id),
           relation='category')


def update_thumbnails(images, gen, gen_id):
    print 'at updating', images
    for i, fname in enumerate(images.get(gen_id, [])):
        print 'fname updating', fname
        Thumbnail.objects.create(generator=gen, index=i, fname=fname)

def update_bug(user, type, desc, file_name, content):
    print 'here'
    print user, type, desc
    bug = Bugs.objects.create(user=user, type=type, description=desc)
    print file_name, content
    if content:
        bug.file.save(file_name, content, save=True)

def reset(reset_type):
    if reset_type:
        globals()[reset_type].objects.all().delete()
    else:
        Package.objects.all().delete()
        Generator.objects.all().delete()
        GeneratorRelations.objects.all().delete()
        Thumbnail.objects.all().delete()
        Tag.objects.all().delete()
        CategoryTree.objects.all().delete()
