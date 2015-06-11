#!/bin/bash

# Msingh 28/01/15
# Records videos RTSP cameras
# Approx 6mb per minute at 640x352

IFS=!

hostname=`hostname | cut -d. -f1`
programs=( "echo" "hostname" "logger" "id" "grep" "pidof" "rm" "awk" "pkill" "openRTSP" )
basedirectory="/mnt/videos"
prog="openRTSP"
user="user"
password="password"

function usage()
{
        cat <<END
$0 (C) Copyright 2015 openRTSP Video Recorder

Usage: $0 [options]

-c Camera to record from (options: front, back, tree) 
-d Debug Mode

END
}

if [[ -z "$1" ]]; then
        # Run in summary mode by default
        usage
        exit
fi

trap 'pkill $prog;sleep 1;mv ${filename}video-H264-1{,.avi}; echo -e "\e[0mExiting $$...";exit' SIGINT SIGTERM

while getopts "c:dh" OPT; do
        case "$OPT" in
        c)
                camera=$OPTARG
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

# Check if required progs are on system
        for prog in "${programs[@]}"
                do
                        if type "$prog" >/dev/null 2>&1; then
                                echo -n "";
                        else
                                echo "Executable $prog missing"; exit 1; fi
                done

echo "----------------------------------" && echo " $hostname - openRTSP Video Recorder       " && echo "----------------------------------"

if [[ -d "$basedirectory" ]]; then

        echo "Using $basedirectory for recordings"
        date=`date "+%Y%m%d%H%M%S"`
        filename="$basedirectory/$camera-$date-"

                case $camera in
                        *front*)
                        echo "Writing to ${filename}";echo
                        ${prog} -b 200000 -V -F "$filename" rtsp://${user}:${password}@192.168.0.91:2091/12
                        ;;

                        *tree*)
                        echo "Writing to ${filename}";echo
                        ${prog} -b 200000 -V -F "$filename" rtsp://${user}:${password}@192.168.0.92:2092/12
                        ;;

                        *back*)
                        echo "Writing to ${filename}";echo
                        ${prog} -b 200000 -V -F "$filename" rtsp://${user}:${password}@192.168.0.93:2093/12
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
