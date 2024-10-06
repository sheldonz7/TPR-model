# clone git repo

git submodule init
git submodule update

# make sure current user have ownership of the directory /opt
# recommend installing the tool under root then add it to the non-root user's PATH


make -f Makefile.init

mkdir build
cd build


../configure --enable-all --disable-release --enable-debug --prefix=/opt/panda
make -j16
make install

# uninstall
make uninstall
make clean

# and then you can rebuild
