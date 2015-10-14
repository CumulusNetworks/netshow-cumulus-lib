#!/bin/bash

set -e

echo "starting up"

git clean -xdf

PATH=$WORKSPACE/venv/bin:/usr/local/bin:$PATH
if [ ! -d "venv" ]; then
        virtualenv venv
fi
. venv/bin/activate

GIT_BRANCH=test
# install test requirements like tox
pip install --upgrade -r requirements_develop.txt

## All of this will go away when netshow-core is in PyPI
GIT_BRANCH=master

# Delete working directories
# TODO: make it an array and iterate over that
if [ -d .tox ]; then
  echo "Delete tox directories"
  rm -rf .tox
fi

if [ -d dist ]; then
  echo "delete dist directory"
  rm -rf .dist
fi

if [ -d wheel_dir ]; then
  echo "Delete wheel directory"
  rm -rf wheel_dir
fi
if [ -d .temp ]; then
  echo "Delete temp install directory"
  rm -rf .temp
fi

# Make working directories
echo "Create wheel directory"
mkdir wheel_dir
echo "Create temp install directory"
mkdir .temp

# Go into the temp directory and install netshow-lib
echo "Go into temp install directory"
cd .temp

echo "Install netshow-core repo"
git clone -b $GIT_BRANCH ssh://git@github.com/CumulusNetworks/netshow-core.git netshow-core
echo " Install netshow-core-lib"
cd netshow-core/netshow-lib

echo "Create wheel for netshow-core-lib"
python setup.py bdist_wheel
echo "Install wheel in wheel directory"
cp dist/* ../../../wheel_dir/

echo " Install netshow-core"
cd ../netshow
python setup.py bdist_wheel
echo "Install wheel in wheel directory"
cp dist/* ../../../wheel_dir/

echo "clone cumulus-platform-info and create wheel"
cd  ../../
git clone -b $GIT_BRANCH ssh://git@github.com/CumulusNetworks/cumulus-platform-info
cd cumulus-platform-info
python setup.py bdist_wheel
cp dist/* ../../wheel_dir/

echo "clone netshow-linux-lib and create wheel"
cd ../
git clone -b $GIT_BRANCH ssh://git@github.com/CumulusNetworks/netshow-linux-lib
cd netshow-linux-lib
python setup.py bdist_wheel
cp dist/* ../../wheel_dir/

echo "Return back to the directory with test.sh"
cd ../../

echo "Run Tox"
tox
