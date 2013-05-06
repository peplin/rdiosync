import os
import mutagen

from .config import PersistentDict


class Collection(PersistentDict):
    # collection = {
    #   'Artist': {
    #       'key': 'asdf',
    #       'albums': {
        #       'Album': {
        #           'tracks': [...],
        #           'synced': false,
        #       },
        #       'Album 2': {
        #           'tracks': [...],
        #           'synced': true,
        #       }
            #}
    #   }
    # }

    def __init__(self, config):
        super(Collection, self).__init__("collection")
        self.config = config

    def get_artist(self, artist):
        return self.setdefault(artist, {})

    def add_album(self, artist, album):
        artist = self.get_artist(artist)
        albums = artist.setdefault('albums', {})
        albums.setdefault(album, {'synced': False})

    def load_albums(self):
        count = 0
        for root, directories, files in os.walk(self.config['music_path']):
            for name in files:
                count += 1
                full_path = os.path.join(root, name)
                if name.endswith("flac") or name.endswith("mp3"):
                    try:
                        audio = mutagen.File(full_path, easy=True)
                    except Exception as e:
                        print "Couldn't open %s: %s" % (full_path, e)
                    else:
                        if 'artist' not in audio or 'album' not in audio:
                            print ("Skipping %s, it's missing something" %
                                    full_path)
                            continue
                        self.add_album(audio['artist'][0],
                                audio['album'][0])
                if count % 1000 == 0:
                    print "Processed %s so far..." % count
                    self.save()
        self.save()
