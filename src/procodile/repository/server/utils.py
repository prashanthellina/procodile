'''
Server side utilities for repository maintenance.

G{importgraph}
'''

import os
import sys
import zipfile
import logging
from  glob import glob
import shutil

from procodile.repository.utils import get_latest_package_version
from procodile.repository.utils import RepositoryException
from procodile.xmlwriter import XMLNode
from procodile.repository.add_package import add_package

log = logging.getLogger()

def get_package_id(class_id, repo_dir):
    '''
    Get the package id given the class id and
    the repo directory. The class id has identifiers
    seperated by '.'. The identifier sequence represents
    a hierarchy in the file system under the repo_dir.

    The package dir is the top most sub-directory in that
    hierarchy that contains a '__package__' file.

    @type class_id: str
    @param class_id: eg: core.model.city.Generator

    @type repo_dir: str
    @param repo_dir: path of the repository

    @rtype: str
    @return: package id eg: core.model
    '''

    parts = class_id.split('.')
    pparts = []

    path = repo_dir

    for p in parts:
        path = os.path.join(path, p)
        pindic_fname = os.path.join(path, '__package__')

        pparts.append(p)

        if os.path.exists(pindic_fname):
            return '.'.join(pparts)

    return None

def get_package_dir(package_id, repo_dir):
    package_dir = package_id.replace('.', os.path.sep)
    return os.path.join(repo_dir, package_dir)

def get_package_version_dir(package_id, repo_dir, version=None):

    package_dir = get_package_dir(package_id, repo_dir)

    if not version:
        version = get_latest_package_version(package_dir)

    if not version:
        msg = 'Invalid package dir: %s' % package_dir
        raise RepositoryException, msg

    version_dir = os.path.join(package_dir, version)

    if not os.path.exists(version_dir):
        msg = 'Version="%s" not found for package="%s"' % \
                (version, package_id)
        raise RepositoryException, msg

    return version_dir

def get_package_xml(package_id, repo_dir, version=None):

    version_dir = get_package_version_dir(package_id, repo_dir, version)

    xml_fpath = os.path.join(version_dir, 'package.xml')

    if not os.path.exists(xml_fpath):
        msg = 'package.xml not found for package=%s, version=%s' % \
                (package_id, version)
        raise RepositoryException, msg

    return xml_fpath

def construct_result_xml(code, message):
    result = XMLNode('result')
    result.attrs = {'code': code, 'message': message}
    return result

def construct_failure_response(name, message):
    message = '%s: %s' % (name, message)
    xml = construct_result_xml(1, message)

    print 'Content-Type: text/xml'
    print
    print '<?xml version="1.0" encoding="utf-8"?>'
    xml.serialize(sys.stdout)

def store_file(fpath, stream, num_bytes, chunk_size):

    f = open(fpath, 'wb')

    bytes_read = 0

    while 1:

        to_read = num_bytes - bytes_read
        to_read = min(chunk_size, to_read)
        log.debug('to read = %s' % to_read)

        data = stream.read(to_read)

        f.write(data)

        bytes_read += len(data)
        log.debug('bytes read = %s' % bytes_read)

        if bytes_read >= num_bytes:
            break

    f.close()

def get_package_dirs(dirpath):
    package_dirs = []

    for dpath, subdirs, fnames in os.walk(dirpath):
        rel_dpath = dpath.split(dirpath, 1)[1].lstrip(os.path.sep)

        if 'package.xml' in fnames:
            package_dirs.append(rel_dpath)

            # since we have found a package dir
            # do not recurse inside it.
            del subdirs[:]

    return package_dirs

SCREENSHOT_EXTENSIONS = frozenset(('jpg', 'jpeg', 'JPG', 'JPEG',
                                   'png', 'PNG', 'bmp', 'BMP',
                                   'gif', 'GIF'))

def get_screenshots(package_dir):
    pattern = os.path.join(package_dir, 'screenshots/*')
    screenshot_dirs = [d for d in glob(pattern) if os.path.isdir(d)]

    screenshots = {}

    for _dir in screenshot_dirs:
        pattern = os.path.join(_dir, '*.*')
        fnames = glob(pattern)
        fnames = [os.path.basename(f) for f in fnames \
                    if f.rsplit('.', 1)[-1] in SCREENSHOT_EXTENSIONS]

        _dir = os.path.basename(_dir)
        screenshots[_dir] = fnames

    return screenshots

def add_packages_from_zip(zip_fpath, tmp_dirpath, package_home,
                 repo_dir, package_info_fn = lambda x: False):

    # extract contents of zipfile
    # into a local directory
    z = zipfile.ZipFile(zip_fpath)
    z.extractall(tmp_dirpath)
    z.close()

    # get list of package dirs
    # by examining zip contents
    package_dirs = get_package_dirs(tmp_dirpath)
    log.debug('package_dirs: %s' % (package_dirs,))

    package_home = package_home.replace('.', os.path.sep)

    # add the package to repository
    for pdir in package_dirs:
        full_pdir = os.path.join(package_home, pdir)
        phome = os.path.dirname(full_pdir)
        pdir = os.path.join(tmp_dirpath, pdir)

        pxml_fpath = os.path.join(pdir, 'package.xml')
        package_id = full_pdir.replace(os.path.sep, '.')
        screenshots = get_screenshots(pdir)

        err = package_info_fn(pxml_fpath, package_id, screenshots)
        if err:
            continue

        # add package to repo
        version = add_package(pdir, phome, repo_dir)

        # copy the zip file and store in repo
        pdir = os.path.join(repo_dir, full_pdir)
        pdir = pdir.replace('.', os.path.sep)
        to_zip_fpath = os.path.join(pdir, version + '.zip')
        shutil.copyfile(zip_fpath, to_zip_fpath)

    return len(package_dirs)
