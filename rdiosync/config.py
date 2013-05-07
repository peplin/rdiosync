import os
try:
    import cPickle as pickle
except ImportError:
    import pickle


class PersistentDict(object):

    def __init__(self, filename="auth"):
        self.filename = filename
        self.dict = self.load(self.filename)

    def __getitem__(self, key):
        try:
            return self.dict.__getitem__(key)
        except KeyError:
            return None

    def __setitem__(self, key, value):
        self.dict.__setitem__(key, value)

    def setdefault(self, key, default=None):
        return self.dict.setdefault(key, default)

    def items(self):
        return self.dict.items()

    def load(self, filename):
        if not os.path.exists(filename):
            self.dict = {}
            self.save()
        with open(filename) as pickle_file:
            return pickle.load(pickle_file)

    def save(self):
        with open(self.filename, "w") as pickle_file:
            pickle.dump(self.dict, pickle_file)


class Configuration(PersistentDict):
    def __init__(self):
        super(Configuration, self).__init__("config")
