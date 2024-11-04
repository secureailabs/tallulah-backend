#!/bin/bash

pip install yt-dlp

mkdir "Sober Livers"

pushd "Sober Livers"

declare -a list_of_videos=("https://youtu.be/XCAR2-FvosQ?si=0vhpmpdbA9aPKBiJ" "https://youtu.be/gM6p7JMGsh8?si=pmRbad3Y7mhslke6")

# Download the list_of_videos
for video in "${list_of_videos[@]}"
do
    echo $video
done

# Conver the mkv files to mp4
for file in *.mkv; do ffmpeg -i "$file" -c:v copy -c:a aac "${file%.mkv}.mp4"; done

# Convert the webm files to mp4 ffmpeg -i input.webm -c:v libx264 -c:a aac output.mp4
for file in *.webm; do ffmpeg -i "$file" -c:v libx264 -c:a aac "${file%.webm}.mp4"; done

popd
