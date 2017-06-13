# Cooperative Lane Management and Traffic flow Optimisation (CoLMTO)

[![CircleCI](https://circleci.com/gh/SocialCars/colmto.svg?style=shield)](https://circleci.com/gh/SocialCars/colmto)
[![codecov](https://codecov.io/gh/SocialCars/colmto/branch/master/graph/badge.svg)](https://codecov.io/gh/SocialCars/colmto)

  * [Source Code Documentation (HTML)](http://socialcars.github.io/colmto/docs/sources/index.html)
  * [Source Code Documentation (PDF)](http://socialcars.github.io/colmto/docs/CoLMTO-doc.pdf)

## Build Instructions

### Prerequisites

* Python 2.7
* libhdf5
* libyaml
* SUMO build dependencies (see build instructions for [MacOS](http://sumo.dlr.de/wiki/Installing/MacOS_Build_w_Homebrew), [Linux](http://sumo.dlr.de/wiki/Installing/Linux_Build), [Windows](http://sumo.dlr.de/wiki/Installing/Windows_Build) to requirements.)

### Checkout Code

```zsh
git clone --recursive https://github.com/SocialCars/colmto.git
cd colmto
```

### Build SUMO

#### MacOS

```zsh
export CPPFLAGS="$CPPFLAGS -I/opt/X11/include/"
export LDFLAGS="-L/opt/X11/lib"
cd sumo/sumo
make -f Makefile.cvs
./configure --with-xerces=/usr/local --with-proj-gdal=/usr/local
make -jN
```

### Linux/FreeBSD

### Windows


### Install CoLMTO (including dependencies)

```zsh
python setup.py install --user
```

## Copyright & License

  * Copyright 2017, Malte Aschermann
  * [License: LGPL](http://socialcars.github.io/colmto/LICENSE.md)
