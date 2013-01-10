#!/usr/bin/env python
'''
Create a new repository.
'''

import os
import sys
import optparse

import procodile
from procodile.xmlwriter import XMLNode

APACHE_CONFIG = '''\
   SetEnv PYTHONPATH "%(pythonpath)s"
'''

def get_installation_dir():
    bdir = os.path.dirname(procodile.__file__)
    return bdir

def main(options):

    repo_xml = os.path.join(options.repo_dir, 'repository.xml')

    if os.path.exists(repo_xml):
        print 'repository already exists at "%s"' % options.repo_dir
        sys.exit(1)

    # create repo dir
    if not os.path.exists(options.repo_dir):
        os.makedirs(options.repo_dir)

    # create repo data dir
    repo_data_dir = os.path.join(options.repo_dir, 'data')
    if not os.path.exists(repo_data_dir):
        os.makedirs(repo_data_dir)

    # create symlink to cgi scripts
    actions_dir = os.path.join(options.repo_dir, 'actions')
    cgi_scripts_dir = os.path.join(options.installation_dir, \
                            'repository/server/cgi/')
    os.symlink(cgi_scripts_dir, actions_dir)

    # create 'repository.xml'
    ostream = open(repo_xml, 'w')

    repo = XMLNode('repository')
    repo.attrs = {'title': options.title}

    if options.description:
        repo.description = options.description

    ostream.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    repo.serialize(ostream)

    ostream.close()

    # inform user of installation dir being used
    print 'using: installation_dir = "%s"' % (options.installation_dir)

    # write .htaccess for apache config
    htaccess_fpath = os.path.join(options.repo_dir, '.htaccess')
    f = open(htaccess_fpath, 'w')
    conf = APACHE_CONFIG % {'pythonpath': options.installation_dir}
    f.write(conf)
    f.close()

if __name__ == '__main__':
    parser = optparse.OptionParser()

    parser.add_option('-r', '--repo-dir', metavar='PATH',
                      help='will be created if not present already. ')

    parser.add_option('-t', '--title', metavar='TEXT', default=None,
                      help='repository title to be stored in metadata')

    parser.add_option('-d', '--description', metavar='TEXT', default='',
                      help='repository description to be stored in metadata')

    parser.add_option('-c', '--installation-dir', metavar='PATH', default='',
                      help='Location of procodile installation' + \
                           'If provided will override environment var - ' + \
                           'BW_LOC. If these options and env var are not' + \
                           'defined, then discovery is attempted.')

    options, args = parser.parse_args()

    if None in (options.repo_dir, options.title):
        print 'please specify --repo-dir, --title'
        sys.exit(1)

    bdir = options.installation_dir

    if not bdir:
        bdir = os.environ.get('BW_LOC')

        if not bdir:
            bdir = get_installation_dir()

    options.installation_dir = bdir

    main(options)
