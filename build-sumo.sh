#!/bin/sh

OS=$(uname)
cd sumo && \
make -f Makefile.cvs && \
if [[ $OS = "Darwin" ]]; then
	export CPPFLAGS="$CPPFLAGS -I/opt/X11/include/" && \
	export LDFLAGS="-L/opt/X11/lib" && \
	./configure --with-xerces=/usr/local --with-proj-gdal=/usr/local
elif [[ $OS = "FreeBSD" ]]; then
	./configure CXX=clang++ --with-xerces-libraries=/usr/local/lib --with-proj-libraries=/usr/local/lib --with-fox-config=/usr/local/bin/fox-config
elif [[ $OS = "Linux" ]]; then
	./configure
fi && \
make clean && \
make -j && \
cd ../..