'''
Repository client utilities.

G{importgraph}
'''

import os
import urllib2
import xml.etree.ElementTree as etree
import xmlrpclib

from procodile.utils import get_tmp_dir, get_random_name
from procodile.repository.utils import zip_dir

class Response:

    def __init__(self, xml):
        self.xml = xml

        xml = xml.strip()
        lines = xml.split('\n')[1:] #ignoring xml header

        if '<data>' in xml:
            response = lines[0] + '</response>'
            xml = ''.join(lines[1:-1])
            xml = xml.split('<data>', 1)[-1]
            xml = xml.rsplit('</data>', 1)[0]

        else:
            response = ''.join(lines)
            xml = ''

        data = None
        if xml:
            data = xmlrpclib.loads(xml)[0]

        response = etree.fromstring(response)
        self.code = int(response.get('code'))
        self.message = response.get('message')
        self.success = (self.code == 0)
        self.data = data

class Client:
    '''
    Repository client abstraction for
    interacting with a repository server.
    '''

    class Exception:
        def __init__(self, code, message):
            self.code = code
            self.message = message
            self.args = (code, message)

        def __repr__(self):
            return 'Client.Exception(%s, %s)' % (self.code, self.message)

        __str__  = __repr__

    CHUNK_SIZE = 4096
    NUM_PER_PAGE = 50

    def __init__(self, repo_uri=None, debug=False):
        self.repo_uri = repo_uri.rstrip(os.path.sep) if repo_uri else None
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        self.debug = debug

    def _handle_response(self, response):
        response_data = response.read()
        response.close()
        r = Response(response_data)

        if self.debug:
            print 'response: %s' % r.xml

        if not r.success:
            raise Client.Exception(r.code, r.message)

        return r.data or r.message

    def get(self, url, data=None):
        if self.debug:
            print 'request: %s, %s' % (url, data)

        r = self.opener.open(url, data=data)
        return self._handle_response(r)

    def login(self, username, password):
        data = 'username=%s&password=%s' % (username, password)
        url = self.repo_uri + '/login'
        return self.get(url, data)

    def logout(self):
        return self.get(self.repo_uri + '/logout')

    def register(self, username, email, password):
        data = 'username=%s&email=%s&password=%s' % (username, email, password)
        url = self.repo_uri + '/register'
        return self.get(url, data)

    def _get_item_info(self, item_type, _id):
        url = '%s/%s/%s' % (self.repo_uri, item_type, _id)
        return self.get(url)[0]

    def user(self, username):
        return self._get_item_info('user', username)

    def generator(self, _id):
        return self._get_item_info('generator', _id)

    def package(self, _id):
        return self._get_item_info('package', _id)

    def _get_listing(self, list_type,
                           ordering='recent',
                           search_term=None,
                           page_num=1,
                           num_per_page=None):

        num_per_page = num_per_page or self.NUM_PER_PAGE

        repo_uri = self.repo_uri
        url = '%(repo_uri)s/%(list_type)s/%(ordering)s' % locals()

        if search_term:
            search = '/search/%(search_term)s' % locals()
            url += search

        pagination = '%(page_num)s/%(num_per_page)s' % locals()
        url = '%(url)s/%(pagination)s' %  locals()

        return self.get(url)

    def users(self, *args, **kwargs):
        return self._get_listing('users', *args, **kwargs)

    def generators(self, *args, **kwargs):
        return self._get_listing('generators', *args, **kwargs)

    def packages(self, *args, **kwargs):
        return self._get_listing('packages', *args, **kwargs)

    def categories(self, *args, **kwargs):
        return self._get_listing('categories', *args, **kwargs)

    def tag_generator(self, gen_id, tag):
        url = self.repo_uri + '/generator/%(gen_id)s/tag' % locals()
        data = '%(tag)s=add' % locals()
        return self.get(url, data)

    def untag_generator(self, gen_id, tag):
        url = self.repo_uri + '/generator/%(gen_id)s/tag' % locals()
        data = '%(tag)s=remove' % locals()
        return self.get(url, data)

    def favorite_generator(self, gen_id):
        return self.tag_generator(gen_id, '.fav')

    def unfavorite_generator(self, gen_id):
        return self.untag_generator(gen_id, '.fav')

    def upload(self, path, package_home):
        '''
        Upload package to repository.

        @param path: path to package zip file / directory.
        @type path: str

        @param package_home: destination location of package in repo
        @type package_home: str
        '''

        fn = self._upload_package_dir if os.path.isdir(path) \
                                      else self._upload_package_zip
        response = fn(path, package_home)
        return self._handle_response(response)

    def bug_report(self, bug_type, description, attachment_path):
        headers = {'Content-type': 'application/zip'}

        data = []
        data.append(str(bug_type))
        data.append(str(description))
        
        if attachment_path:
            zdata = open(attachment_path, 'rb').read()
            data.append(attachment_path.rsplit(os.path.sep, 1)[-1])
            data.append(zdata)
        
        data = '\n'.join(data)

        bugreport_uri = self.repo_uri + '/bugreport'
        request = urllib2.Request(bugreport_uri, data, headers)
        response = self.opener.open(request)

        return self._handle_response(response)


    def _upload_package_zip(self, package_zip_fpath, package_home):

        zdata = open(package_zip_fpath, 'rb').read()
        headers = {'Content-type': 'application/zip'}

        data = []
        data.append(str(package_home))
        data.append(str(len(zdata)))
        data.append(zdata)
        data = '\n'.join(data)

        upload_uri = self.repo_uri + '/upload'
        request = urllib2.Request(upload_uri, data, headers)
        response = self.opener.open(request)

        return response

    def _upload_package_dir(self, package_dir_path, package_home):
        tmp_fname = get_random_name()
        tmp_fpath = os.path.join(get_tmp_dir(), tmp_fname)

        try:
            zip_dir(package_dir_path, tmp_fpath)
            response = self._upload_package_zip(tmp_fpath, package_home)
            return response
        finally:
            if os.path.exists(tmp_fpath):
                os.remove(tmp_fpath)

    def download(self, to_location, _id, version=None):
        close_file = False

        if isinstance(to_location, (str, unicode)):
            to_location = open(to_location, 'wb')
            close_file = True

        try:
            return self._download_package(to_location, _id, version)
        finally:
            if close_file:
                to_location.close()

    def _download_package(self, stream, _id, version=None):

        _id = '%s-%s' % (_id, version) if version else _id

        download_uri = self.repo_uri + '/download/%s' % _id

        request = urllib2.Request(download_uri)
        response = self.opener.open(request)

        if response.headers['Content-Type'] == 'text/xml':
            # some error occured
            return self._handle_response(response)

        while 1:
            data = response.read(self.CHUNK_SIZE)
            if not data:
                break
            stream.write(data)

    def reset(self):
        return self.get(self.repo_uri + '/reset')

#: Default CLIENT object to be used only for stateless operations.
CLIENT = Client()
