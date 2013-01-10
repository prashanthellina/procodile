import re

from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

RE_LIST = '(?P<list_type>users|generators|packages|categories)'
RE_ITEM = '(?P<item_type>user|generator|package|category)/\
(?P<item_name>[\._\-A-Za-z0-9]+)'
RE_GEN = 'generator/(?P<generator_id>[\._\-A-Za-z0-9]+)'
RE_ITEM_LIST = '(?P<item_list_type>generators|packages|parents|sub_generators)'

RE_ORDERING = '(?P<ordering>relevance|popularity|recent)'
RE_SEARCH ='search/(?P<search_term>[^/]+)'
RE_PAGINATION = '(?P<page_no>\d+)(?:/(?P<num>\d+)){0,1}'

def make_regex(text):
    parts = re.findall('<[A-Z_]+>', text)
    for p in parts:
        re_name = p.strip('<>')
        re_name = 'RE_%s' % re_name
        text = text.replace(p, globals()[re_name])
    return text
P = make_regex

api_urls = patterns('procodile.repository.server.core.api_views',

    (r'^login$', 'login_user'),
    (r'^logout$', 'logout_user'),
    (r'^register$', 'register'),

    (r'^upload$', 'upload'),
    url(r'^download/(?P<_id>[\._\-A-Za-z0-9]+)$', 'download', name="download"),

    (r'^bugreport$', 'bug_report'),

    url(P('^<GEN>/tag$'), 'tag_view'),
    url(P('^<GEN>/image/(?P<size>.*?)/(?P<fname>.*)$'), 'image_view'),
    url(P('^<GEN>/image/(?P<fname>.*)$'), 'image_view'),

    url(P('^<LIST>$'), 'list_view'),
    url(P('^<LIST>/<SEARCH>$'), 'list_view'),
    url(P('^<LIST>/<ORDERING>$'), 'list_view'),
    url(P('^<LIST>/<ORDERING>/<SEARCH>$'), 'list_view'),

    url(P('^<LIST>/<PAGINATION>$'), 'list_view'),
    url(P('^<LIST>/<SEARCH>/<PAGINATION>$'), 'list_view'),
    url(P('^<LIST>/<ORDERING>/<PAGINATION>$'), 'list_view'),
    url(P('^<LIST>/<ORDERING>/<SEARCH>/<PAGINATION>$'), 'list_view'),

    url(P('^<ITEM>$'), 'item_view'),
    url(P('^<ITEM>/<ITEM_LIST>$'), 'item_list_view'),
    url(P('^<ITEM>/<ITEM_LIST>/<SEARCH>$'), 'item_list_view'),
    url(P('^<ITEM>/<ITEM_LIST>/<ORDERING>$'), 'item_list_view'),
    url(P('^<ITEM>/<ITEM_LIST>/<ORDERING>/<SEARCH>$'), 'item_list_view'),

    url(P('^<ITEM>/<ITEM_LIST>/<PAGINATION>$'), 'item_list_view'),
    url(P('^<ITEM>/<ITEM_LIST>/<SEARCH>/<PAGINATION>$'), 'item_list_view'),
    url(P('^<ITEM>/<ITEM_LIST>/<ORDERING>/<PAGINATION>$'), 'item_list_view'),
    url(P('^<ITEM>/<ITEM_LIST>/<ORDERING>/<SEARCH>/<PAGINATION>$'),\
                                                            'item_list_view'),

    url('^reset$', 'reset_view'),
    url('^reset/(?P<reset_type>[_\-A-Za-z0-9]+)$', 'reset_view'),
    )

html_urls = patterns('procodile.repository.server.core.html_views',

    url(r'^$', 'gens_view', name="home_page"),

    (r'^login$', 'login_user'),
    (r'^logout$', 'logout_user'),
    (r'^register$', 'register'),

    (r'^upload$', 'upload_gen'),
    (r'^download/(?P<_id>[\._\-A-Za-z0-9]+)$', 'download_gen'),

    url('^user/(?P<username>[_\-A-Za-z0-9]+)$', 'user_view'),

    url(P('^<GEN>/tag$'), 'tag_view'),

    url(P('^generators$'), 'gens_view'),
    url(P('^generators/<SEARCH>$'), 'gens_view'),
    url(P('^generators/<ORDERING>$'), 'gens_view'),
    url(P('^generators/<ORDERING>/<SEARCH>$'), 'gens_view'),

    url(P('^generators/<PAGINATION>$'), 'gens_view'),
    url(P('^generators/<SEARCH>/<PAGINATION>$'), 'gens_view'),
    url(P('^generators/<ORDERING>/<PAGINATION>$'), 'gens_view'),
    url(P('^generators/<ORDERING>/<SEARCH>/<PAGINATION>$'), 'gens_view'),

    url(P('^<ITEM>/generators$'), 'gens_view'),
    url(P('^<ITEM>/generators/<SEARCH>$'), 'gens_view'),
    url(P('^<ITEM>/generators/<ORDERING>$'), 'gens_view'),
    url(P('^<ITEM>/generators/<ORDERING>/<SEARCH>$'), 'gens_view'),

    url(P('^<ITEM>/generators/<PAGINATION>$'), 'gens_view'),
    url(P('^<ITEM>/generators/<SEARCH>/<PAGINATION>$'), 'gens_view'),
    url(P('^<ITEM>/generators/<ORDERING>/<PAGINATION>$'), 'gens_view'),
    url(P('^<ITEM>/generators/<ORDERING>/<SEARCH>/<PAGINATION>$'),\
                                                            'gens_view'),

    url(P('^generator/(?P<item_name>[\._\-A-Za-z0-9]+)$'), 'gen_view'),

    url(P('^package/(?P<item_name>[\._\-A-Za-z0-9]+)$'), 'pack_view'),
    )

urlpatterns = html_urls + patterns('',
    (r'^admin/(.*)', admin.site.root),

    (r'^api/', include(api_urls)),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
                 {'document_root': settings.MEDIA_ROOT}),
)