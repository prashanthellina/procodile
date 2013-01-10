#!/usr/bin/env python
'''
Add a new package or a new version of existing package
to the repository.
'''

import os
import sys
import glob
import shutil
import logging
import optparse
import xml.etree.ElementTree as etree

from procodile.xmlwriter import XMLNode
from procodile.repository.utils import RepositoryException, \
                                        get_package_versions, \
                                        get_latest_package_version, \
                                        extract_zip

log = logging.getLogger()

def get_package_version(package_dir):
    package_xml = os.path.join(package_dir, 'package.xml')

    if not os.path.exists(package_xml):
        msg = 'package.xml missing in package = "%s"' % package_dir
        raise RepositoryException(msg)

    doc = etree.parse(package_xml)
    version = doc.getroot().get('version')
    return version

def prepare_home(repo_dir, package_home, package_name):
    phome = os.path.join(repo_dir, package_home, package_name)
    if not os.path.exists(phome):
        os.makedirs(phome)
        pindic_fname = os.path.join(phome, '__package__')
        open(pindic_fname, 'w').close()

    return phome

def add_package_dir(package_dir, package_home, repo_dir):
    version = get_package_version(package_dir)

    if not version:
        raise RepositoryException, 'version not specified in package.xml'

    package_name = os.path.basename(package_dir.rstrip(os.path.sep))

    phome = package_home.replace('.', os.path.sep)
    phome = prepare_home(repo_dir, phome, package_name)

    versions = get_package_versions(phome)
    if version in versions:
        raise RepositoryException, 'version %s already exists' % version

    version_dir = os.path.join(phome, version)

    shutil.copytree(package_dir, version_dir)

    return version

def add_package(package, package_home, repo_dir):
    tmp_dirpath = None

    try:
        if os.path.isfile(package):
            # is a zip file
            tmp_dirpath = extract_zip(package)
            package = glob.glob(tmp_dirpath + '/*')[0]

        version = add_package_dir(package, package_home, repo_dir)
        return version

    finally:
        if tmp_dirpath and os.path.exists(tmp_dirpath):
            shutil.rmtree(tmp_dirpath)

def main(options):

    tmp_dirpath = None

    package = options.package_dir or options.package_zip

    add_package(package,
                options.package_home,
                options.repo_dir)

if __name__ == '__main__':
    parser = optparse.OptionParser()

    parser.add_option('-r', '--repo-dir', metavar='PATH',
                      help='location of repository.')

    parser.add_option('-m', '--package-home', metavar='PATH',
                      help='relative path in repository directory ' + \
                           'where the package has to be placed\n' + \
                           'eg: core/trees or core.trees')

    parser.add_option('-p', '--package-dir', metavar='PATH',
                      help='location of package that needs to be ' + \
                           'added to the repository')

    parser.add_option('-z', '--package-zip', metavar='PATH',
                      help='location of package zip to be added' + \
                           'to the repository')

    options, args = parser.parse_args()

    if None in (options.repo_dir, options.package_home):
        print 'please specify --repo-dir, --package-home'
        sys.exit(1)

    if bool(options.package_dir) ^ bool(options.package_zip):
        print 'please specify --package-zip or --package-dir'
        sys.exit(1)

    main(options)
