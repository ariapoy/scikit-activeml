"""
The :mod:`skactiveml.pool` module implements query strategies for pool-based
active learning.
"""

from ._probal import McPAL, XPAL
from ._random import RandomSampler
from ._uncertainty import UncertaintySampling, expected_average_precision
from ._qbc import QBC, average_KL_divergence, vote_entropy
from ._expected_error import ExpectedErrorReduction
from ._four_ds import FourDS
from ._alce import ALCE

__all__ = ['RandomSampler', 'McPAL', 'XPAL', 'UncertaintySampling',
           'ExpectedErrorReduction', 'QBC', 'FourDS', 'ALCE']
