"""
The :mod:`skactiveml.utils` module includes various utilities.
"""
from ._aggregation import compute_vote_vectors
from ._functions import call_func, simple_batch
from ._label import is_unlabeled, is_labeled, ExtLabelEncoder
from ._multi_annot import ext_confusion_matrix
from ._selection import rand_argmax, rand_argmin
from ._validation import check_classes, check_missing_label, check_scalar, \
    check_cost_matrix, check_classifier_params, check_X_y, MISSING_LABEL, \
    check_random_state, check_class_prior

from ._visualization import plot_2d_dataset  # TODO remove after merging 'docs_getting_started' branch

__all__ = ['rand_argmax', 'rand_argmin', 'compute_vote_vectors',
           'is_unlabeled', 'is_labeled', 'ExtLabelEncoder', 'check_classes',
           'check_missing_label', 'check_cost_matrix', 'check_scalar',
           'check_classifier_params', 'check_X_y', 'check_random_state',
           'MISSING_LABEL', 'call_func', 'simple_batch', 'check_class_prior',
           'ext_confusion_matrix']
