#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Helper functions taken from aima-python."""
import math
import random

# ______________________________________________________________________________
# argmin and argmax

argmin = min
argmax = max


def _identity(x):
    return x


def argmin_random_tie(seq, key=_identity):
    """
    Return an element with lowest fn(seq[i]) score.

    Break ties randomly.
    """
    return argmin(shuffled(seq), key=key)


def argmax_random_tie(seq, key=_identity):
    """
    Return an element with highest fn(seq[i]) score.

    Break ties randomly.
    """
    return argmax(shuffled(seq), key=key)


def shuffled(iterable):
    """Randomly shuffle a copy of iterable."""
    items = list(iterable)
    random.shuffle(items)
    return items

# ______________________________________________________________________________
# argmin and argmax


def exp_schedule(k=20, lam=0.005, limit=100):
    """One possible schedule function for simulated annealing."""
    return lambda t: (k * math.exp(-lam * t) if t < limit else 0)

# ______________________________________________________________________________


def probability(p):
    """Return true with probability p."""
    return p > random.uniform(0.0, 1.0)
