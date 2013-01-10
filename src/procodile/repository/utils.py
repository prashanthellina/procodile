'''
Utilities for repository management.

G{importgraph}
'''

import re
import os
import glob
import string
import random
import zipfile
import logging

import xml.etree.ElementTree as etree
from procodile.utils import get_tmp_dir, get_random_name

log = logging.getLogger()

repos_cache = None

def set_repos_cache(loc):
    global repos_cache
    repos_cache = loc

def get_repos_cache():
    if not repos_cache:
        env_repos_cache = os.environ.get('BW_REPOS_CACHE')
        return env_repos_cache

    return repos_cache

class RepositoryException:
    def __init__(self, message=''):
        self.message = message

    def __repr__(self):
        return '%s' % self.message

def parse_version(v):
    return [int(x) for x in v.split('.')]

def unparse_version(v):
    return '.'.join([str(x) for x in v])

def get_package_versions(package_dir, parse=False):
    pattern = os.path.join(package_dir, '*')
    matches = glob.glob(pattern)
    version_dirs = [os.path.basename(f) for f in matches if os.path.isdir(f)]

    version_dirs = [parse_version(v) for v in version_dirs]
    version_dirs.sort()

    identity = lambda v: v
    unparse = identity if parse else unparse_version
    version_dirs = [unparse(v) for v in version_dirs]

    return version_dirs

def get_latest_package_version(package_dir):
    version_dirs = get_package_versions(package_dir)

    if not version_dirs:
        return None

    return version_dirs[-1]

def zip_dir(dir_path, zip_fpath, rename_dir=None):
    '''
    Create a zip file at I{zip_fpath} placing directory
    at I{dir_path} in the zip file. If I{rename_dir} is
    specified, rename the directory when placing in the
    zip file.

    @type dir_path: str
    @param dir_path: path of directory to place in zip file

    @type zip_fpath: str
    @param zip_fpath: path of the zip file to be created

    @type rename_dir: None/str
    @param rename_dir: name to give the directory when
        placing inside the zip file

    @rtype: None
    '''
    dir_path = dir_path.rstrip(os.path.sep)
    dir_name = os.path.basename(dir_path)

    if rename_dir:
        dir_name = rename_dir

    def collect_files(data, _dir, files):
        data.extend([os.path.join(_dir, f) for f in files])

    all_files = []
    os.path.walk(dir_path, collect_files, all_files)

    zfile = zipfile.ZipFile(zip_fpath, 'w')

    for src_path in all_files:
        dst_path = src_path.split(dir_path, 1)[-1]
        dst_path = '%s%s' % (dir_name, dst_path)

        zfile.write(src_path, dst_path)

    zfile.close()

class Dependency(object):
    def __init__(self, repo_uri, class_id, version, _type):
        self.repo_uri = repo_uri
        self.class_id = class_id
        self.version = version
        self.type = _type

    def _get_key(self):
        return (self.repo_uri,
                self.class_id,
                self.version)

    def __eq__(self, other):
        if other is None:
            return False

        eq = self._get_key() == other._get_key()
        return eq

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        return cmp(self._get_key(), other._get_key())

    def __hash__(self):
        return hash(self._get_key())

    def __str__(self):
        return 'Dependency: repo=%s, id=%s, version=%s, type=%s' % \
            self.repo_uri, self.id, self.version, self.type

    def __repr__(self):
        return str(self)

def _get_dependency(_type, node):
    repo_uri = node.get('repo')
    if not repo_uri:
        return None

    _id = node.get('id')
    version = node.get('version')

    return Dependency(repo_uri, _id, version, _type)

def get_dependencies(package_xml):

    dependencies = set()
    xml = package_xml
    doc = etree.fromstring(xml)

    sub_generators = doc.findall('.//sub_generator')
    parents = doc.findall('.//parent')

    for _type, nodes in [('sub_generator', sub_generators),
                         ('parent', parents)]:
        for node in nodes:
            d = _get_dependency(_type, node)
            if d:
                dependencies.add(d)

    return dependencies

def extract_zip(zip_fpath, dir_path=None):

    if not dir_path:
        dirname = get_random_name()
        dir_path = os.path.join(get_tmp_dir(), dirname)

    unzip_file_into_dir(open(zip_fpath, 'rb'), dir_path)

    return dir_path

def ensure_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def unzip_file_into_dir(zfile, dir_path):
    zfobj = zipfile.ZipFile(zfile)

    for name in zfobj.namelist():
        full_path = os.path.join(dir_path, name)

        if name.endswith('/'):
            ensure_dir(full_path)
        else:
            ensure_dir(os.path.dirname(full_path))
            outfile = open(full_path, 'wb')
            outfile.write(zfobj.read(name))
            outfile.close()

def get_package_xml(xml, _dir, zip):
    if xml:
        xml = open(xml).read()

    elif zip:
        try:
            tmp_dirpath = extract_zip(zip)
            xml = os.path.join(tmp_dirpath, 'package.xml')
            xml = open(xml).read()
        finally:
            if os.path.exists(tmp_dirpath):
                shutil.rmtree(tmp_dirpath)

    else:
        xml = os.path.join(_dir, 'package.xml')
        xml = open(xml).read()

    return xml
