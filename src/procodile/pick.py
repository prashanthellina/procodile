'''
Utilities for picking random values deterministically.
(Pseudo Random Number Generation)

G{importgraph}
'''

import random
import hashlib

from procodile.utils import DotAccessDict

class Picker:
    '''
    Randomization utility
    '''

    def __init__(self, seed=None):
        self._seed = None
        self.seed(seed)

    def seed(self, seed):

        self.seed = seed

        if seed is not None:
            self._random = random.Random(seed)
        else:
            self._random = random.Random()

    def pick(self, *args):

        if len(args) == 0:
            data = [True, False]

        elif len(args) == 1:
            data = args[0]

        elif len(args) == 2:
            data = tuple(args)

        else:
            data = args

        if not data:
            return data

        elif isinstance(data, tuple):
            data = Range(*data)
            return self.pick(data)

        elif isinstance(data, Range):
            if isinstance(data.min, int) and isinstance(data.max, int):
                return self._random.randint(data.min, data.max)
            else:
                return self._random.uniform(data.min, data.max)

        elif isinstance(data, (list, xrange)):
            return self._random.choice(data)

        elif isinstance(data, (dict, DotAccessDict)):
            return self.configure(data)

        elif hasattr(data, '__pick__'):
            return data.__pick__(self)

        else:
            return data

    def configure(self, config):
        _config = {}

        for key, value in config.iteritems():
            value = self.pick(value)
            _config[key] = value

        config = DotAccessDict(_config)
        return config

    def random(self):
        return self._random.random()

    def randint(self, *args, **kwargs):
        return self._random.randint(*args, **kwargs)

    def choice(self, seq):
        return self._random.choice(seq)

    def shuffle(self, seq):
        return self._random.shuffle(seq)

class Range:
    def __init__(self, _min, _max):
        self.min = _min
        self.max = _max

    def __repr__(self):
        return 'Range(%s, %s)' % (self.min, self.max)

def make_seed(*seeds):
    composite = '.'.join([str(s) for s in seeds])
    digest = hashlib.md5(composite).hexdigest()
    value = eval('0x' + digest)
    return value % 65535
