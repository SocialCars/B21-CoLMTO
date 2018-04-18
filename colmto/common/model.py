# -*- coding: utf-8 -*-
# @package colmto.common.model
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
'''Classes and functions to realise models regarding dissatisfaction, inefficiency and unfairness.'''

import typing
import numpy
import pandas


# pylint: disable=no-member
def unfairness(data: pandas.Series) -> numpy.float64:
    r'''
    Calculate the unfairness by means of the H-Spread of Hinges for given data points.

    note: Using `pandas.Series.quantile([.75, .25])` with linear (=default) interpolation.

    .. math::
        :nowrap:

        \begin{eqnarray*}
        \text{Hinge} &=& H_2 - H_1 \text{with} \\
        H_1 &=& a_{n+2} = a_{(N+3)/4} \\
        H_2 &=& a_{3n+4} = a_{(3N+1)/4}.
        \end{eqnarray*}

    For example

    .. math::
        :nowrap:

        \begin{align*}
        \begin{array}{l}
        \text{relative time-}\\
        \text{losses of vehicles}
        \end{array}
        \Rightarrow
        \begin{array}{c}IQR\\\text{(H-Spread)}\end{array}
        \Rightarrow
        \begin{array}{ccccccccc}
        26&  &  &  &40&  &  &  &54\\
        &34&&36&  &41&&46\\
        &&36&&&&42
		\end{array}\\
		\Rightarrow \text{unfairness} =|36-42|=6
		\end{align*}

    :see: Weisstein, Eric W. H-Spread. From MathWorld--A Wolfram Web Resource. http://mathworld.wolfram.com/H-Spread.html
    :see: Weisstein, Eric W. Hinge. From MathWorld--A Wolfram Web Resource. http://mathworld.wolfram.com/Hinge.html
    :param data: pandas.Series of data elements (preferably) :math:`4n+5` for :math:`n=0,1,...,N`, i.e. minimum length is :math:`5`.
    :return: Hinge of type numpy.float64

    '''

    return numpy.subtract(*data.quantile([.75, .25])) if not data.empty else numpy.float64(0)


def dissatisfaction(
        time_loss: float,
        optimal_travel_time: float,
        time_loss_threshold=0.2) -> numpy.float64:
    r'''
    Calculate driver's dissatisfaction.

    .. math::
        :nowrap:

        \begin{eqnarray*}
        TT &:=& \text{travel time}, \\
        TT^{*} &:=& \text{optimal travel time}, \\
        TL &:=& \text{time loss}, \\
        TLT &:=& \text{time loss threshold}, \\
        \text{dissatisfaction} &:=& dsat(TL, TT^{*}, TLT) \\
        &=&\frac{1}{1+e^{(-TL + TLT \cdot TT^{*}) \cdot \rho}}.\\
        &&\text{Note: Using a smoothening factor of $\rho = 0{.}05$}\\
        &&\text{to make the transition not that sharp}
        \end{eqnarray*}

    :param time_loss: time loss
    :param time_loss_threshold: cut-off point of acceptable time loss
        relative to optimal travel time in [0,1]
    :param optimal_travel_time: optimal travel time
    :return: dissatisfaction ([0,1] normalised)

    '''

    # pylint: disable=no-member
    return numpy.divide(
        1.,
        1 + numpy.exp((-time_loss + time_loss_threshold * optimal_travel_time) * .05)
    )
    # pylint: enable=no-member

def inefficiency(data: pandas.Series) -> typing.Union[numpy.int64, numpy.float64]:  # pylint: disable=no-member
    '''
    Inefficiency model, i.e. sum of data

    :param data: pandas.Series
    :return: sum of data points
    '''

    return data.sum()
