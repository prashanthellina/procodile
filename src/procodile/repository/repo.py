#!/usr/bin/env python
'''
Repository client console user interface.

G{importgraph}
'''

import os
import sys
import traceback
import optparse
from pprint import pprint
from cmd import Cmd
from getpass import getpass
import cStringIO

from procodile.repository.client import Client
from procodile.repository.utils import set_repos_cache
from procodile.repository.utils import get_repos_cache
from procodile.loader import get_loader, cache_package_metadata

def parse_args(args, num):
    args = args.strip().split(' ')

    if len(args) < num:
        args = args + [''] * (num - len(args))

    elif len(args) > num:
        extra_args = args[num:]
        args = args[:num]

        args[-1] += ' '.join(extra_args)

    return args

def get_args(args, names):
    names = [n.strip() for n in names.split(',') if n.strip()]

    num = len(names)
    args = parse_args(args, num)

    for index, arg in enumerate(args):
        name = names[index]

        if not arg and not name.startswith('#'):
            get_data = getpass if name == 'password' else raw_input
            arg = get_data('%s: '% name)
            args[index] = arg

    if len(args) == 1:
        args = args[0]

    return args

class RepoConsole(Cmd):

    def __init__(self, options):

        Cmd.__init__(self)
        self.options = options
        self.username = None
        self.repo_uri = None
        self.repos_cache = None
        self.client = None
        self.exception = None
        self.debug = options.debug

        self.do_set_repository(options.repo_uri)

        if options.repos_cache:
            self.do_repos_cache(options.repos_cache)

        if options.username:
            self.do_login(options.username)

    def do_repos_cache(self, args):
        if self.repos_cache and not args:
            print self.repos_cache
            return

        self.repos_cache = args if args else get_repos_cache()
        set_repos_cache(self.repos_cache)

    def do_exception(self, args):
        print ''.join(traceback.format_exception(*self.exception))

    def do_set_repository(self, args):
        if self.username:
            self.do_logout('')

        self.repo_uri = get_args(args, 'repo-uri')
        self.client = Client(self.repo_uri, self.debug)

    def do_who(self, args):
        print 'repo: %s, username: %s' % (self.repo_uri, self.username)

    def do_login(self, args):
        username, password = get_args(args, 'username, password')
        self.client.login(username, password)
        self.username = username
        self.prompt = '%s >>> ' % self.username

    def do_logout(self, args):
        self.client.logout()
        self.prompt = '>>> '
        self.username = None

    def do_register(self, args):
        username, email, password = get_args(args, 'username, email, password')
        self.client.register(username, email, password)

    def do_user(self, args):
        username = get_args(args, 'username')
        pprint(self.client.user(username))

    def do_generator(self, args):
        _id = get_args(args, 'id')
        pprint(self.client.generator(_id))

    def do_package(self, args):
        _id = get_args(args, 'id')
        pprint(self.client.package(_id))

    def _parse_list_args(self, args):
        args = args.split(' ')

        int_args = []
        for a in reversed(args):
            if a.isdigit():
                int_args.insert(0, a)
            else:
                break

        if int_args:
            args = args[:-len(int_args)]

        args = ' '.join(args)
        int_args = ' '.join(int_args)

        ordering, search_term = get_args(args, '#ordering,#search-term')
        page_num, num_per_page = get_args(int_args, '#page_num,#num_per_page')

        page_num = int(page_num) if page_num else 1
        num_per_page = int(num_per_page) if num_per_page \
                                         else self.client.NUM_PER_PAGE

        ordering = ordering if ordering else 'recent'

        return ordering, search_term, page_num, num_per_page

    def do_users(self, args):
        users = self.client.users(*self._parse_list_args(args))
        if users and isinstance(users, tuple):
            pprint (users[0])

    def do_generators(self, args):
        generators = self.client.generators(*self._parse_list_args(args))
        if generators and isinstance(generators, tuple):
            pprint (generators[0])

    def do_packages(self, args):
        packages = self.client.packages(*self._parse_list_args(args))
        if packages and isinstance(packages, tuple):
            pprint (packages[0])

    def do_categories(self, args):
        pass

    def do_tag(self, args):
        gen_id, tag = get_args(args, 'generator-id,tag')
        self.client.tag_generator(gen_id, tag)

    def do_untag(self, args):
        gen_id, tag = get_args(args, 'generator-id,tag')
        self.client.untag_generator(gen_id, tag)

    def do_favorite(self, args):
        gen_id = get_args(args, 'generator-id')
        self.client.favorite_generator(gen_id)

    def do_unfavorite(self, args):
        gen_id = get_args(args, 'generator-id')
        self.client.unfavorite_generator(gen_id)

    def do_reset(self, args):
        self.client.reset()

    def _get_package_meta(self, stream, path, version, description):

        package = get_loader().get_package(path)
        meta = package.meta
        meta.version = version
        meta.description = description

        xml_doc = meta.xmlize()
        stream.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        xml_doc.serialize(stream)

        cache_package_metadata(meta, path)

    def _ensure_package_xml(self, path):
        pxml_fpath = os.path.join(path, 'package.xml')
        if os.path.exists(pxml_fpath):
            return

        version, description = get_args('', 'version, description')

        f = open(pxml_fpath, 'w')
        self._get_package_meta(f, path, version, description)
        f.close()

    def do_upload(self, args):
        path, package_home = get_args(args, 'path,package-home')

        if os.path.isdir(path):
            self._ensure_package_xml(path)

        response = self.client.upload(path, package_home)
        print response

    def do_download(self, args):
        to_location, _id, version = get_args(args, 'path,id,#version')
        self.client.download(to_location, _id, version)

    def do_generatemeta(self, args):
        package_dir, version, description, outfile = get_args(args,
                                'package-dir,version,#description,out-file')
        if outfile == os.path.join(package_dir, 'package.xml'):
            f = cStringIO.StringIO()
        else:
            f = open(outfile, 'w') if outfile else sys.stdout

        self._get_package_meta(f, package_dir, version, description)
        
        if outfile:
            f.close()

    def do_debug(self, args):
        self.debug = not self.debug
        print 'debug = %s' % self.debug
        if self.client:
            self.client.debug = self.debug

    def do_EOF(self, args):
        self.do_quit(args)

    def do_quit(self, args):
        print '\n'
        sys.exit(0)

    def do_help(self, args):

        if args == '':
            Cmd.do_help(self, args)

        else:
            if 'do_%s' % args in dir(self):
                code = 'doc_string = self.do_%s.__doc__' % args
                exec(code)
                print doc_string

def command_loop(console):
    try:
        console.cmdloop()
    except SystemExit:
        pass
    except Client.Exception, e:
        print 'server error: %s, %s' % (e.code, e.message)
        command_loop(console)
    except:
        console.exception = sys.exc_info()[:3]
        exception = traceback.format_exception(*console.exception)[-1]
        print 'Fatal Error: %s' % exception
        command_loop(console)

def main(options, args):
    c = RepoConsole(options)

    if args:
        args = ' '.join(args)
        c.onecmd(args)
    else:
        if '>>>' not in c.prompt:
            c.prompt = '>>> '
        command_loop(c)

if __name__ == '__main__':
    parser = optparse.OptionParser(usage='%prog [options] [<command>]')

    parser.add_option('-r', '--repo-uri', default='', metavar='URI',
                help='repository url eg: http://example.com/api/')

    parser.add_option('-u', '--username', default='', metavar='STRING')

    parser.add_option('-c', '--repos-cache', metavar='PATH',
                      help='location of repositories storage. ' + \
                           'can be omitted if BW_REPOS_CACHE is defined' + \
                           'in the environment.')

    parser.add_option('-d', '--debug', metavar='BOOL',
                        help='enable debugging', action='store_true')

    (options, args) = parser.parse_args()

    main(options, args)
