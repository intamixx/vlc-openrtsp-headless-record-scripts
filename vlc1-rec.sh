#!/bin/bash

# Msingh 28/01/15
# Records videos from RTSP cameras

# Approx 1.8mb / minute at 640x352
# Approx 9mb / 5 minute at 640x352
# Approx 120mb / hour at 640x352

# /usr/lib/vlc/plugins/codec/libavcodec_plugin.so (required)
# from vlc 2.0.5-1~bp

# package vlc-nox (without X support)
# vlc-nox 2.0.5-1~bp
# VLC media player 2.0.3 Twoflower (revision 2.0.2-93-g77aa89e)

IFS=!

hostname=`hostname | cut -d. -f1`
programs=( "echo" "hostname" "logger" "id" "grep" "pidof" "rm" "awk" "pkill" "cvlc" )
basedirectory="/mnt/videos"
prog="cvlc"
user="user"
password="password"

function usage()
{
        cat <<END
$0 (C) Copyright 2015 cvlc Video Recorder

Usage: $0 [options]

-c Camera to record from (options: front, back, tree, study, kitchen) 
-q Quality (options: high, med, low) 
-d Debug Mode

END
}

if [[ -z "$1" ]]; then
        # Run in summary mode by default
        usage
        exit
fi

trap 'pkill $prog;sleep 1; echo -e "\e[0mExiting $$...";exit' SIGINT SIGTERM

while getopts "c:q:dh" OPT; do
        case "$OPT" in
        c)
                camera=$OPTARG
                ;;
        q)
                quality=$OPTARG
                ;;
        d)
                debug=true
                ;;
        h)
                usage
                exit 0
                ;;
        ?)
                usage
                exit 1
        esac
done
shift $((OPTIND - 1))

        case $quality in
                *high*)
                        bitrate=230
                ;;
                *med*)
                        bitrate=150
                ;;
                *low*)
                        bitrate=50
                ;;
                *)
                        bitrate=230
                ;;
        esac

# Check if required progs are on system
        for prog in "${programs[@]}"
                do
                        if type "$prog" >/dev/null 2>&1; then
                                echo -n "";
                        else
                                echo "Executable $prog missing"; exit 1; fi
                done

echo "----------------------------------" && echo " $hostname - cvlc Video Recorder       " && echo "----------------------------------"

if [[ -d "$basedirectory" ]]; then

        echo "Using $basedirectory for recordings"
        date=`date "+%Y%m%d%H%M%S"`
        filename="$basedirectory/$camera-$date-$quality.mp4"

                case $camera in
                        *front*)
                        echo "Writing to ${filename}";echo
                        ${prog} rtsp://${user}:${password}@192.168.0.91:2091/12  --noaudio --sout-transcode-vb=$bitrate --sout "#transcode{venc=x264,vcodec=h264}:std{access=file,mux=mp4,dst=${filename}"
                        ;;

                        *tree*)
                        echo "Writing to ${filename}";echo
                        ${prog} rtsp://${user}:${password}@192.168.0.92:2092/12  --noaudio --sout-transcode-vb=$bitrate --sout "#transcode{venc=x264,vcodec=h264}:std{access=file,mux=mp4,dst=${filename}"
                        ;;

                        *back*)
                        echo "Writing to ${filename}";echo
                        ${prog} rtsp://${user}:${password}@192.168.0.93:2093/12  --noaudio --sout-transcode-vb=$bitrate --sout "#transcode{venc=x264,vcodec=h264}:std{access=file,mux=mp4,dst=${filename}"
                        ;;

                        *study*)
                        echo "Writing to ${filename}";echo
                        ${prog} http://admin:numark@192.168.0.81:81/videostream.asf  --noaudio --sout-transcode-vb=$bitrate --sout "#transcode{venc=x264,vcodec=h264}:std{access=file,mux=mp4,dst=${filename}"
                        ;;

                        *kitchen*)
                        echo "Writing to ${filename}";echo
                        ${prog} http://admin:numark@192.168.0.82:82/videostream.asf  --noaudio --sout-transcode-vb=$bitrate --sout "#transcode{venc=x264,vcodec=h264}:std{access=file,mux=mp4,dst=${filename}"
                        ;;

                        *)
                        echo "Camera not listed"
                        usage
                        exit 1
                        ;;
                esac
else

        echo "$basedirectory does not exist"
fi

exit 0
