#!/bin/sh

OS=$(uname)
cd sumo && \
make -f Makefile.cvs && \
[ $OS = "Darwin" ] &&
    export CPPFLAGS="$CPPFLAGS -I/opt/X11/include/" && \
    export LDFLAGS="-L/opt/X11/lib" && \
    ./configure --with-xerces=/usr/local --with-proj-gdal=/usr/local --enable-pic
[ $OS = "FreeBSD" ] && \
    ./configure CXX=clang++ --with-xerces-libraries=/usr/local/lib --with-proj-libraries=/usr/local/lib --with-proj-includes=/usr/local/include --with-fox-config=/usr/local/bin/fox-config --enable-pic
[ $OS = "Linux" ] && \
    ./configure --enable-pic
make clean && \
make -j $(getconf NPROCESSORS_CONF)