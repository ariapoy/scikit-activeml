import inspect
import warnings

import numpy as np
from sklearn.base import clone
from sklearn.utils.validation import check_array, check_is_fitted, \
    NotFittedError

from ._selection import rand_argmax
from ._validation import check_scalar


def call_func(f_callable, only_mandatory=False, **kwargs):
    """ Calls a function with the given parameters given in kwargs if they
    exist as parameters in f_callable.

    Parameters
    ----------
    f_callable : callable
        The function or object that is to be called
    only_mandatory : boolean
        If True only mandatory parameters are set.
    kwargs : kwargs
        All parameters that could be used for calling f_callable.

    Returns
    -------
    called object
    """
    params = inspect.signature(f_callable).parameters
    param_keys = params.keys()
    if only_mandatory:
        param_keys = list(filter(lambda k: params[k].default == inspect._empty,
                                 param_keys))

    vars = dict(filter(lambda e: e[0] in param_keys, kwargs.items()))

    return f_callable(**vars)


def simple_batch(utilities, random_state=None, batch_size=1, return_utilities=False):
    """Generates a batch by selecting the highest values in the 'utilities'.
    If utilities is an ND-array, the returned utilities will be an (N+1)D-array,
    with the shape batch_size x utilities.shape, filled the given utilities but
    set the n-th highest values in the n-th row to np.nan.

    Parameters
    ----------
    utilities : np.ndarray
        The utilities to be used to create the batch.
    random_state : numeric | np.random.RandomState (default=None)
        The random state to use. If `random_state is None` random `random_state`
        is used.
    batch_size : int, optional (default=1)
        The number of samples to be selected in one AL cycle.
    return_utilities : bool (default=False)
        If True, the utilities are returned.

    Returns
    -------
    best_indices : np.ndarray, shape (batch_size) if ndim == 1
    (batch_size, ndim) else
        The index of the batch instance.
    batch_utilities : np.ndarray,  shape (batch_size, len(utilities))
        The utilities of the batch (if return_utilities=True).

    """
    # validation
    utilities = check_array(utilities, ensure_2d=False, dtype=float,
                            force_all_finite='allow-nan', allow_nd=True)
    check_scalar(batch_size, target_type=int, name='batch_size', min_val=1)
    max_batch_size = np.sum(~np.isnan(utilities), dtype=int)
    if max_batch_size < batch_size:
        warnings.warn(
            "'batch_size={}' is larger than number of candidate samples "
            "in 'utilities'. Instead, 'batch_size={}' was set.".format(
                batch_size, max_batch_size))
        batch_size = max_batch_size
    # generate batch

    batch_utilities = np.empty((batch_size,) + utilities.shape)
    best_indices = np.empty((batch_size,  utilities.ndim), dtype=int)

    for i in range(batch_size):
        best_indices[i] = rand_argmax(utilities, random_state=random_state)
        batch_utilities[i] = utilities
        utilities[tuple(best_indices[i])] = np.nan
    # Check whether utilities are to be returned.
    if utilities.ndim == 1:
        best_indices = best_indices.flatten()

    if return_utilities:
        return best_indices, batch_utilities
    else:
        return best_indices