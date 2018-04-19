# -*- coding: utf-8 -*-
# @package tests.common
# @cond LICENSE
# #############################################################################
# # LGPL License                                                              #
# #                                                                           #
# # This file is part of the Cooperative Lane Management and Traffic flow     #
# # Optimisation project.                                                     #
# # Copyright (c) 2018, Malte Aschermann (malte.aschermann@tu-clausthal.de)   #
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
'''
colmto: Test module for common.model.
'''

import pandas
import numpy

from nose.tools import assert_equal
from nose.tools import assert_almost_equal
from nose.tools import assert_true

import colmto.common.model


def test_unfairness():
    '''
    Test unfairness, i.e. H-Spread function.

    note: Example data taken from http://mathworld.wolfram.com/Hinge.html
    '''

    assert_equal(
        colmto.common.model.unfairness(
            pandas.Series(
                (150, 250, 688, 795, 795, 795, 895, 895, 895, 1099, 1166, 1333, 1499, 1693, 1699, 1775, 1895)
            )
        ),
        704
    )

    assert_equal(
        colmto.common.model.unfairness(pandas.Series(range(10**6))),
        499999.5
    )

    assert_equal(
        colmto.common.model.unfairness(
            pandas.Series()
        ),
        0
    )

    assert_equal(
        colmto.common.model.unfairness(
            pandas.Series((0,))
        ),
        0
    )

    assert_equal(
        colmto.common.model.unfairness(
            pandas.Series((1, 2, numpy.nan, 3, 4, 5))
        ),
        2
    )

    assert_true(
        isinstance(
            colmto.common.model.unfairness(pandas.Series()),
            numpy.float64                                       # pylint: disable=no-member
        )
    )


def test_dissatisfaction():
    '''
    Test dissatisfaction model
    '''

    assert_equal(
        colmto.common.model.dissatisfaction(2, 10, 0.2),
        0.5
    )

    assert_almost_equal(
        colmto.common.model.dissatisfaction(6, 10, 0.5),
        0.51249739
    )


def test_inefficiency():
    '''
    Test inefficiency model
    '''

    assert_true(
        isinstance(
            colmto.common.model.inefficiency(pandas.Series((1, 2, 3, 4))),
            numpy.int64
        )
    )


    assert_true(
        isinstance(
            colmto.common.model.inefficiency(pandas.Series((1.1, 2, 3, 4))),
            numpy.float64                                                   # pylint: disable=no-member
        )
    )

    assert_equal(
        colmto.common.model.inefficiency(pandas.Series((1, 2, 3, 4))),
        10
    )

    assert_equal(
        colmto.common.model.inefficiency(pandas.Series((11, -2, 43.5, 114))),
        166.5
    )
