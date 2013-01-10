'''
Repository Configuration
'''

import os
import logging

class Config:
    #: repository directory
    repo_dir = 'c:/repo'
    #: directory to store temporary-transient files
    tmp_dir = 'c:/tmp/'
    #: directory to store cache files
    cache_dir = 'c:/cache'

    #: read files in chunks of this size when
    # serving out.
    chunk_size = 4096

    #: log file
    log_fpath = os.path.join(repo_dir, 'log')

    #: log level
    log_level = logging.DEBUG
