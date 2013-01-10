'''
Need the following installed:
    # Subversion Windows Command Line client
    ## http://www.open.collab.net/downloads/subversion/

    # NSIS
'''

import os
import sys
import shutil
import optparse
import compileall

def handle_rm_error(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
        func(path)
    else:
        raise

def load_config(config):
    config = __import__(config, fromlist=['*'])
    config = config.Config
    return config

def get_tmp_dir():
    return os.path.join(os.getcwd(), os.getpid())

def do_checkout(code_dir, username, password, tag=None):
    print 'Checking out source (%s) ...' % tag
    c = 'svn checkout -q --username %s --password %s '\
        '"svn://ellina.homeip.net:3690/media/data/code/blockworld'
    c = c % (username, password)
    c += ('/tags/%s"' % tag if tag else '/trunk"')
    c += ' "%s"' % code_dir

    if os.path.exists(code_dir):
        shutil.rmtree(code_dir, onerror=handle_rm_error)

    error = os.system(c)
    if error:
        raise Exception('checkout failed')

def _ignore_files(path, fnames):
    if path.endswith('.svn'):
        return fnames

    return [f for f in fnames if f.endswith('.pyc') or f.endswith('.pyo')]

def remove_source(path):
    def del_fn(arg, dirname, fnames):
        for f in fnames:
            if f.endswith('.py'):
                os.remove(os.path.join(path, dirname, f))

    os.path.walk(path, del_fn, None)

def update_installer_dir(code_dir, installer_dir, keep_source=True):
    print 'Updating code ...'
    
    procodile_src = os.path.join(code_dir, r'src\procodile')
    procodile_dst = os.path.join(installer_dir,
                        r'python\Lib\site-packages\procodile')
    scripts_src = os.path.join(code_dir, r'src\scripts')
    scripts_dst = os.path.join(installer_dir, 'scripts')
    samples_src = os.path.join(code_dir, r'misc\karthik\samples')
    samples_dst = os.path.join(installer_dir, 'samples')

    # remove old data in destination dir locations
    for path in (procodile_dst, scripts_dst, samples_dst):
        if os.path.exists(path):
            print ' Removing old code ...'
            shutil.rmtree(path, onerror=handle_rm_error)

    # copy from code dir to installer dir
    print 'Copying new code ...'
    igfn = _ignore_files
    shutil.copytree(procodile_src, procodile_dst, ignore=igfn)
    shutil.copytree(scripts_src, scripts_dst, ignore=igfn)
    shutil.copytree(samples_src, samples_dst, ignore=igfn)

    # regenerate .pyc files
    print 'Compiling source ...'
    for path in (procodile_dst, scripts_dst, samples_dst):
        compileall.compile_dir(path, quiet=True)

    if not keep_source:
        print 'Removing raw source ...'
        remove_source(procodile_dst)
        remove_source(scripts_dst)

def make_installer(script_path, installer_dest_dir, out_path):
    print 'Making installer (%s) ...' % out_path
    c = 'makensis.exe /V2 /DInstallerOutput="%s" /DInstallerFiles="%s" "%s"' %\
            (out_path, installer_dest_dir, script_path)
    error = os.system(c)
    if error:
        raise Exception('making installer failed')

def main(options, args):
    config = load_config(args[0])

    wdir = options.working_dir or config.working_dir or get_tmp_dir()
    dir_exists = os.path.exists(wdir)
    if not dir_exists:
        os.makedirs(wdir)

    # get procodile code
    code_dest_dir = os.path.join(wdir, 'code')
    if config.should_checkout:
        do_checkout(code_dest_dir, config.svn_username,
                    config.svn_password, config.tag)
    else:
        code_dest_dir = config.code_dir

    # get installer dir
    print 'Copying installer dependencies ...'
    installer_dest_dir = os.path.join(wdir, 'installer')
    if not os.path.exists(installer_dest_dir):
        shutil.copytree(config.installer_dir, installer_dest_dir)

    update_installer_dir(code_dest_dir, installer_dest_dir, config.keep_source)

    script_path = os.path.join(code_dest_dir, 'procodile.nsi')
    outpath = config.outpath
    make_installer(script_path, installer_dest_dir, outpath)

    if not dir_exists:
        shutil.rmtree(wdir, onerror=handle_rm_error)

if __name__ == '__main__':
    parser = optparse.OptionParser(usage='%prog [options] <config>')
    parser.add_option('-w', '--working-dir', default=None,
            metavar='PATH', help='temporary directory for working')
    (options, args) = parser.parse_args()

    main(options, args)
