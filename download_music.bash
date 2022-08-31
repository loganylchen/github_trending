#! /bin/bash

set -x
set -e


music_list=https://www.youtube.com/playlist?list=PL6rKmks47C2vRvYpBy51BQV2oHwFpljql

wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -O ./youtube-dl
chmod a+rx ./youtube-dl
./youtube-dl -x --yes-playlist --audio-format mp3  -o 'mp3s/%(title)s.%(ext)s' $music_list
