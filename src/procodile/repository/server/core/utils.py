__author__="karthik"
__date__ ="$Sep 30, 2009 10:26:40 AM$"

import os
import hashlib
import xmlrpclib

from django.http import HttpResponse

from procodile.xmlwriter import XMLNode
from procodile.repository.server.config import Config as config

resp_codes = {'success'       : (0, 'Success'),
              'login_required': (1, 'Login Required'),
              'invalid_usrpwd': (2, 'Enter username and password correctly'),
              'inactive_usr'  : (3, 'Your account is de-activated'),
              'err_record'    : (4, 'No matching records found'),
              'err'           : (5, 'some error')
              }

def apiresponse(message=None, code='success', data=None):
    message = message or resp_codes[code][1]
    code_no = resp_codes[code][0]

    response = HttpResponse(mimetype='text/xml')
    root = XMLNode('response')
    root.attrs = {'code': code_no, 'message': message}

    if data:
        data = xmlrpclib.dumps((data,), allow_none=True) if data else data
        root.data = data
    
    response.write('<?xml version="1.0"?>\n')
    root.serialize(response)

    return response

def api_login_required(fn):
    def login_req(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return apiresponse(code='login_required')
        return fn(request, *args, **kwargs)
    return login_req

def getvalues(record, fields=None):
    fields = fields or record.__dict__
    values = dict([(field, getattr(record, field)) for field in fields])

    return values

def format_id(_id):
    username = None
    version = None

    splits = _id.split('.', 1)
    username = splits[0] if len(splits)==2 else None # get username
    _id = splits[-1]

    splits = _id.rsplit('-', 1)
    version =  splits[-1] if len(splits)==2 else None # get version
    _id = splits[0]
        
    return (username, _id, version)

def get_package_path(arg):
    if isinstance(arg, unicode):
        username, fid, ver = format_id(arg)

        if not username or not fid or not ver:
            return

        fid = fid.replace('.', os.path.sep)
        pack_path = os.path.sep.join([username, fid, ver])
        
    else:
        gen = arg
        pack_id = gen.package.pack_id.replace('.', os.path.sep)
        pack_path = os.path.sep.join([gen.user.username, pack_id, gen.version])

    pack_path = os.path.join(config.repo_dir, pack_path)

    return pack_path

def compute_cache_path(path, id):
    hash = hashlib.md5(id).hexdigest()
    dir_one = hash[:2]
    dir_two = hash[2:4]

    path = os.path.join(path, dir_one, dir_two)
    if not os.path.exists(path):
        os.makedirs(path)

    fpath = os.path.join(path, hash+'.jpg')
    
    return fpath

