#
#    Copyright (C) 2024-2025 sys4 AG
#    Author Boris Lohner bl@sys4.de
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#

import random


class RandPool:
    """
    A pooled random generator that returns values form a pool until the pool is empty, then the pool gets refilled.
    Counts over the returned values are flat after each multiple of the pool size and differ at most by one otherwise.
    """
    def __init__(self, poolsize):
        """
        Initializes a random pool of size poolsize.
        The pool will return values from zero inclusive up to poolsize exclusive in random order.
        :param poolsize: The size of the pool
        """
        self.size = poolsize
        self.pool = []

    def get(self):
        """
        Returns a random value from the pool of remaining values.
        If no values are left to choose from, the pool is filled with a new set of possible return values.
        :return: One random value out of the pool of possible values
        """
        if len(self.pool) == 0:  # refill the empty pool
            self.pool = [i for i in range(self.size)]
            random.shuffle(self.pool)
        return self.pool.pop()  # return a random value from the pool
