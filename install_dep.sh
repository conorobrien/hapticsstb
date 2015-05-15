
sudo apt-get update && apt-get upgrade

sudo apt-get install -y exfat-fuse # fuse for EXFAT file system, used for backup
sudo apt-get install -y build-essential vlc v4l-utils p7zip-full yasm # general utilities for viewing and compiling
sudo apt-get install -y python-dev python-numpy python-matplotlib python-opencv python-pip # necessary python modules

sudo pip install --upgrade pip
sudo pip install pyserial cython

# Optional, download OpenCV
# wget http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.9/opencv-2.4.9.zip
# unzip opencv-2.4.9.zip
# rm opencv-2.4.9.zip

echo -n "Username for serial and video access: "
read username

sudo adduser $username dialout
sudo adduser $username video

echo "Log in and out for changes to take effect"