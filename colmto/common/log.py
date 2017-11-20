# -*- coding: utf-8 -*-
# @package colmto.common
# @cond LICENSE
# #############################################################################
# # LGPL License                                                              #
# #                                                                           #
# # This file is part of the Cooperative Lane Management and Traffic flow     #
# # Optimisation project.                                                     #
# # Copyright (c) 2017, Malte Aschermann (malte.aschermann@tu-clausthal.de)   #
# # This program is free software: you can redistribute it and/or modify      #
# # it under the terms of the GNU Lesser General Public License as            #
# # published by the Free Software Foundation, either version 3 of the        #
# # License, or (at your option) any later version.                           #
# #                                                                           #
# # This program is distributed in the hope that it will be useful,           #
# # but WITHOUT ANY WARRANTY; without even the implied warranty of            #
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
# # GNU Lesser General Public License for more details.                       #
# #                                                                           #
# # You should have received a copy of the GNU Lesser General Public License  #
# # along with this program. If not, see http://www.gnu.org/licenses/         #
# #############################################################################
# @endcond
'''Logging module'''
import logging
import logging.handlers
from pathlib import Path
import sys
import warnings


def logger(name: str, loglevel=logging.NOTSET, quiet=False,
           logfile=Path('~/.colmto/colmto.log').expanduser()) -> logging.Logger:
    '''Create a logger instance.'''

    if not isinstance(loglevel, (int, str)):
        raise TypeError('Unknown log level type %s' % type(loglevel))

    # create logfile dir if not exist
    Path(logfile).expanduser().parent.mkdir(parents=True, exist_ok=True)

    l_log = logging.getLogger(name)

    l_log.setLevel(loglevel.upper() if isinstance(loglevel, str) else loglevel)

    # create a logging format
    l_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # create a file/stream handler if not already done
    l_add_fhandler = True
    l_add_qhandler = True
    for i_handler in l_log.handlers:
        if isinstance(i_handler, logging.handlers.RotatingFileHandler):
            l_add_fhandler = False
        elif isinstance(i_handler, logging.StreamHandler):
            l_add_qhandler = False

    if l_add_fhandler:
        l_fhandler = logging.handlers.RotatingFileHandler(
            logfile, maxBytes=100 * 1024 * 1024, backupCount=16
        )
        l_fhandler.setLevel(l_log.getEffectiveLevel())
        l_fhandler.setFormatter(l_formatter)

        # add the handlers to the logger
        l_log.addHandler(l_fhandler)

    if l_add_qhandler:
        # create a stdout handler if not set to quiet
        if not isinstance(quiet, bool):
            raise TypeError(f'quiet ({quiet}) is {type(quiet)}, but bool expected.')

        if not quiet:
            l_shandler = logging.StreamHandler(sys.stdout)
            l_shandler.setLevel(l_log.getEffectiveLevel())
            l_shandler.setFormatter(l_formatter)
            l_log.addHandler(l_shandler)

    return l_log

def deprecated(func):
    '''
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.

    @see https://wiki.python.org/moin/PythonDecoratorLibrary#Generating_Deprecation_Warnings
    '''

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        '''wrapper function'''
        warnings.warn_explicit(
            'Call to deprecated function {}.'.format(func.__name__),
            category=DeprecationWarning,
            filename=func.func_code.co_filename,
            lineno=func.func_code.co_firstlineno + 1
        )
        return func(*args, **kwargs)
    return new_func
