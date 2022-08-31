#! /bin/bash

set -x
set -e


music_list=https://www.youtube.com/playlist?list=PLOPongunjVMV9KhWBq1ByXVyGIXh41uz5

wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -O ./youtube-dl
chmod a+rx ./youtube-dl
./youtube-dl -x --yes-playlist --audio-format mp3  -o 'mp3s/%(title)s.%(ext)s' $music_list
