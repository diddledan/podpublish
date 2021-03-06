#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) Ubuntu Podcast
# http://www.ubuntupodcast.org
# See the file "LICENSE" for the full license governing this code.

import argparse
import glob
import os
import podpublish
import re
import sys
from mutagen.easyid3 import EasyID3, EasyID3KeyError
from mutagen.oggvorbis import OggVorbis
from podpublish import configuration
from podpublish import encoder
from podpublish import uploader

def get_files(audio_in, audio_format):
    files = [os.path.join(dirpath, f)
        for dirpath, dirnames, files in os.walk(audio_in)
        for f in files if f.endswith(audio_format)]
    return files

def get_tags(audio_file, audio_format):
    print("Getting tags from " + audio_file)
    if audio_format is 'mp3':
        return EasyID3(audio_file)
    elif audio_format is 'ogg':
        return OggVorbis(audio_file)
    else:
        print("ERROR! Unknown audio format. Abort.")
        sys.exit(1)

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def main():
    parser = argparse.ArgumentParser(description='Encode a season of existing podcasts to mkv and upload them to YouTube.')
    parser.add_argument('--version', action='version', version=podpublish.__version__)
    parser.add_argument('filename', type=argparse.FileType('r'), help="Podcast configuration file.")
    args = parser.parse_args()

    AUDIO_FORMAT='mp3'

    config = configuration.Configuration(args.filename)
    audio_files = get_files(config.audio_in, AUDIO_FORMAT)

    comment_suffix = config.tags['comments']

    for audio_file in audio_files:
        # Ignore the low bitrate files
        if '_low' in audio_file:
            continue

        # Pull in the episode from the audio filename.
        config.episode = re.findall(r"(?:e|x|episode|\n)(\d{2})", audio_file, re.I)[0]
        config.update_filename()

        # Update the configuration to point at the current audio file.
        config.audio_in = audio_file
        tags = get_tags(audio_file, AUDIO_FORMAT)

        # Pull in the title from the audio tags.
        config.tags['title'] = tags['title'][0]
        config.tags['comments'] = tags['title'][0] + comment_suffix
        config.youtube['description'] = tags['title'][0] + comment_suffix

        if not os.path.isfile(config.mkv_file):
            encoder.png_poster(config)
            encoder.mkv_encode(config)
            os.remove(config.png_poster_file)

        if not os.path.isfile(config.mkv_file + '.upload'):
            uploader.youtube_upload(config)
            touch(config.mkv_file + '.upload')

if __name__ == '__main__':
    main()
