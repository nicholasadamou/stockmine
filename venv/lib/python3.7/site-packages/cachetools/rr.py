from __future__ import absolute_import

import random

from .cache import Cache


# random.choice cannot be pickled in Python 2.7
def _choice(seq):
    return random.choice(seq)


class RRCache(Cache):
    """Random Replacement (RR) cache implementation."""

    def __init__(self, maxsize, choice=random.choice, getsizeof=None):
        Cache.__init__(self, maxsize, getsizeof)
        # TODO: use None as default, assing to self.choice directly?
        self.__choice = _choice if choice is random.choice else choice

    @property
    def choice(self):
        """The `choice` function used by the cache."""
        return self.__choice

    def popitem(self):
        """Remove and return a random `(key, value)` pair."""
        try:
            key = self.__choice(list(self))
        except IndexError:
            raise KeyError(f'{self.__class__.__name__} is empty')
        else:
            return (key, self.pop(key))
