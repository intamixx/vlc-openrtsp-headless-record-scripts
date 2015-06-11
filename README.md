# vlc-openrtsp-headless-record-scripts

These scripts are run from my VYOS firewall which also acts as a headless video recorder for my surveillance cameras (no audio).
The script vlc1-rec.sh uses cvlc with the libavcodec library file copied from the vlc 2.0.5-1~bp package.  It transcodes the stream in h264 avi format and also allows to change bitrate quality of recorded output.  I didn't want to install this package as it would install a huge amount of other dependant packages.
Also installed package vlc-nox (without X support).

Version of vlc used from debian squeeze and deb-multimedia repos;
vlc-nox 2.0.5-1~bp
VLC media player 2.0.3 Twoflower (revision 2.0.2-93-g77aa89e)
