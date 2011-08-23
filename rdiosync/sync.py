#!/usr/bin/env python
import argparse

import rdio

from .collection import Collection
from .config import Configuration


def get_api(config):
    if config['token'] is None:
        api = rdio.Api(config['api_key'], config['api_secret'])
        token_dict = api.get_token_and_login_url()
        print 'Authorize this application at: %s?oauth_token=%s' % (
            token_dict['login_url'], token_dict['oauth_token'])
        oauth_verifier = raw_input('Enter the PIN / oAuth verifier: ').strip()
        auth_dict = api.authorize_with_verifier(oauth_verifier)
        print auth_dict
    else:
        api = rdio.Api(config['api_key'], config['api_secret'],
                config['token'], config['token_key'])
    return api


def update_artist_key(api, artist_name, artist_info):
    if 'key' not in artist_info and not artist_info.get('missing', False):
        results = api.search(artist_name.encode("utf-8"), "Artist").results
        if len(results) > 0 and isinstance(results[0], rdio.rdio.RdioArtist):
            artist_info['key'] = results[0].key
        else:
            artist_info['missing'] = True


# Recurse over all files
# Build dict of artists/albums, pickle it

# For each artist, get_albums_for_artist(artist.key)
# Find matches between albums in local database and list returned from rdio
# For each track key in the album, add to collection
# Mark in database that it was synced

def sync(config):
    collection = Collection()
    api = get_api(config)

    collection.load_albums()

    for artist_name, artist_info in collection.items():
        update_artist_key(api, artist_name, artist_info)
        if 'key' not in artist_info:
            print "Skipping artist %s, couldn't get key" % artist_name
            continue

        albums = None
        for local_album_name, local_album in artist_info['albums'].items():
            if 'key' in local_album:
                print "Already matched %s - %s" % (
                        artist_name, local_album_name)
                continue
            if local_album.get('missing', False):
                print "Missing key for %s - %s" % (artist_name, local_album_name)
                continue
            albums = (albums or api.get_albums_for_artist(artist_info['key'])
                    or [])
            matched = False
            for album in albums:
                if (album.name.lower() == local_album_name.lower() or
                        album.name.lower().startswith(local_album_name.lower())):
                    local_album['key'] = album.key
                    local_album['tracks'] = album.track_keys
                    matched = True
                    break
            if not matched:
                print "Couldn't match album %s for artist %s" % (
                        local_album_name, artist_name)
                local_album['missing'] = True
    collection.save()

    for artist_name, artist_info in collection.items():
        if artist_info.get('missing', False):
            print "Skipping loading albums for %s, key is missing" % artist_name
            continue
        for local_album_name, local_album in artist_info['albums'].items():
            if local_album.get('synced', False):
                print "Already synced %s - %s" % (
                        artist_name, local_album_name)
                continue
            if 'tracks' not in local_album:
                continue
            api.add_to_collection(local_album['tracks'])
            print "Synced tracks for %s - %s" % (
                    artist_name, local_album_name)
            local_album['synced'] = True

    collection.save()

def run():

    parser = argparse.ArgumentParser(
            description="Sync directories of music to an Rdio collection")
    parser.add_argument('--api-key', dest='api_key',
            type=unicode, help="Your API key from Rdio")
    parser.add_argument('--api-secret', dest='api_secret',
            type=unicode, help="Your API secret from Rdio")
    parser.add_argument('--music-path', dest='music_path',
            type=unicode, help="The path to your music")
    parser.add_argument('-p', '--print-config', action='store_true',
            help="Print the current configuration")
    args = parser.parse_args()

    config = Configuration()
    config['api_key'] = args.api_key or config['api_key']
    config['api_secret'] = args.api_secret or config['api_secret']
    config['music_path'] = args.music_path or config['music_path']

    if args.print_config:
        print "Current configuration:"
        print config.dict
        return

    if not config['api_key'] or not config['api_secret']:
        print "You must set your API key and secret"
        parser.print_help()
    elif not config['music-path']:
        print "You must set the path to your music"
        parser.print_help()
    else:
        sync(config)

if __name__ == '__main__':
    run()
