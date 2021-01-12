#!/bin/bash
#wget --timeout=8 --waitretry=0 --tries=1 -O photo1.jpg http://192.168.1.75:8080/photo.jpg
ffmpeg -timeout 1000000 -y -i http://192.168.1.37:8080/video -codec:v mjpeg -frames:v 1 photo2.jpg < /dev/null &
ffmpeg -timeout 1000000 -y -i http://192.168.1.75:8080/video -codec:v mjpeg -frames:v 1 photo1.jpg < /dev/null &
ffmpeg -timeout 1000000 -y -i http://192.168.1.159:8080/video -codec:v mjpeg -frames:v 1 photo3.jpg < /dev/null &
#wget --timeout=8 --waitretry=0 --tries=1 -O photo2nr.jpg http://192.168.1.37:8080/photo.jpg
#jpegtran -rotate 180 photo2nr.jpg > photo2.jpg
fswebcam -d v4l2:/dev/video2 -r 320x240 --jpeg 90 -D 2 --rotate 180 --no-banner --scale 1280x720 backlight_compensation 5 -F 5 -S 2 photo4.jpg
montage  photo?.jpg  -tile 2x2  -geometry +0+0  photo_combined.jpg
mv -f photo_combined.jpg photo.jpg
