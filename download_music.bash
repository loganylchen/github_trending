#! /bin/bash

set -x
set -e


music_list=https://www.youtube.com/playlist?list=PL6rKmks47C2vRvYpBy51BQV2oHwFpljql

wget https://yt-dl.org/downloads/latest/youtube-dl -O ./youtube-dl
chmod a+rx ./youtube-dl
./youtube-dl -x --yes-playlist --audio-format mp3  -o 'mp3s/%(title)s.%(ext)s' $music_list