import unittest
import warnings
from copy import deepcopy
import inspect

import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler

from skactiveml.classifier import SklearnClassifier
from skactiveml.regressor import SklearnRegressor
from skactiveml.pool import (
    SubSamplingWrapper,
    ParallelUtilityEstimationWrapper,
    QueryByCommittee,
    UncertaintySampling,
)
from skactiveml.pool.multiannotator import IntervalEstimationThreshold
from skactiveml.tests.template_query_strategy import (
    TemplateSingleAnnotatorPoolQueryStrategy,
)
from skactiveml.utils import MISSING_LABEL
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


class TestSubSamplingWrapper(
    TemplateSingleAnnotatorPoolQueryStrategy, unittest.TestCase
):
    def setUp(self):
        # Create dataset.
        X, y = load_breast_cancer(return_X_y=True)
        self.X = StandardScaler().fit_transform(X)
        y = y.astype(float)
        y[:50] = MISSING_LABEL
        y[350:] = MISSING_LABEL

        # Create test setting for classification.
        clf = SklearnClassifier(
            RandomForestClassifier(random_state=0),
            classes=[0, 1],
            missing_label=MISSING_LABEL,
            random_state=0,
        )
        query_default_params_clf = {
            "X": X,
            "y": y,
            "ensemble": clf,
            "fit_ensemble": True,
        }

        # Create test setting for regression.
        reg = SklearnRegressor(
            RandomForestRegressor(random_state=0),
            missing_label=MISSING_LABEL,
            random_state=0,
        )
        query_default_params_reg = {
            "X": X,
            "y": y,
            "ensemble": reg,
            "fit_ensemble": True,
        }

        # Setup initial parameters, where `QueryByCommittee` is used because
        # it can handle classification and regression models.
        init_default_params = {
            "query_strategy": QueryByCommittee(random_state=0),
            "max_candidates": 10,
            "random_state": 0,
            "missing_label": MISSING_LABEL,
        }

        super().setUp(
            qs_class=SubSamplingWrapper,
            init_default_params=init_default_params,
            query_default_params_clf=query_default_params_clf,
            query_default_params_reg=query_default_params_reg,
        )

    def test_init_param_max_candidates(self, test_cases=None):
        test_cases = [] if test_cases is None else test_cases
        test_cases += [
            (0, ValueError),
            (1.9, ValueError),
            ("", TypeError),
            (10, None),
            (0.9, None),
        ]
        self._test_param("init", "max_candidates", test_cases)

    def test_init_param_query_strategy(self, test_cases=None):
        test_cases = [] if test_cases is None else test_cases
        test_cases += [
            (0, AttributeError),
            ("1.2", AttributeError),
            (QueryByCommittee(), None),
            (IntervalEstimationThreshold(), TypeError),
        ]
        self._test_param("init", "query_strategy", test_cases)

    def test_query_param_query_kwargs(self, test_cases=None):
        test_cases = [] if test_cases is None else test_cases
        test_cases += [(2, TypeError), (True, None), ("Hello", TypeError)]
        # Check is adjusted for ensemble since it is exemplary used
        # as parameters to the default query strategy of this test.
        self._test_param("query", "fit_ensemble", test_cases)

    def test_query(self):
        qs = deepcopy(self.init_default_params["query_strategy"])
        qs_sub = self.qs_class(**deepcopy(self.init_default_params))

        for query_params in [
            self.query_default_params_clf,
            self.query_default_params_reg,
        ]:
            query_params = deepcopy(query_params)
            query_params["return_utilities"] = True
            query_params["batch_size"] = 1
            query_params["candidates"] = query_params["X"]
            (
                q,
                u,
            ) = qs.query(**query_params)
            u = u.ravel()
            q_sub, u_sub = qs_sub.query(**query_params)
            u_sub = u_sub.ravel()
            mask = ~np.isnan(u_sub)
            np.testing.assert_array_equal(u[mask], u_sub[mask])
            query_params["return_utilities"] = False
            q_sub = qs_sub.query(**query_params)
            self.assertEqual(len(q_sub), 1)

        us = UncertaintySampling()
        qs_us = SubSamplingWrapper(us)
        sig_qs_us = inspect.signature(qs_us.query).parameters
        sig_us = inspect.signature(us.query).parameters
        self.assertEqual(sig_qs_us, sig_us)

    def test_query_batch_variation(self):
        init_params = deepcopy(self.init_default_params)
        qs = self.qs_class(**init_params)

        for query_params in [
            self.query_default_params_clf,
            self.query_default_params_reg,
        ]:
            if query_params is not None:
                query_params = deepcopy(query_params)
                max_batch_size = qs.max_candidates
                batch_size = min(5, max_batch_size)
                self.assertTrue(batch_size > 1, msg="Too few unlabeled")

                query_params["batch_size"] = batch_size
                query_params["return_utilities"] = True
                query_ids, utils = qs.query(**query_params)

                self.assertEqual(len(query_ids), batch_size)
                self.assertEqual(len(utils), batch_size)
                self.assertEqual(len(utils[0]), len(query_params["X"]))
                self.assertEqual(sum(~np.isnan(utils[0])), qs.max_candidates)

                query_params["batch_size"] = max_batch_size + 1
                query_params["return_utilities"] = False
                self.assertWarns(Warning, qs.query, **query_params)

                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore")
                    ids = qs.query(**query_params)
                    self.assertEqual(len(ids), max_batch_size)


class TestParallelUtilityEstimationWrapper(
    TemplateSingleAnnotatorPoolQueryStrategy, unittest.TestCase
):
    def setUp(self):
        X, y = load_breast_cancer(return_X_y=True)
        X = StandardScaler().fit_transform(X)
        y = y.astype(float)
        y[:50] = MISSING_LABEL
        y[350:] = MISSING_LABEL
        clf = SklearnClassifier(
            RandomForestClassifier(random_state=0),
            classes=[0, 1],
            missing_label=MISSING_LABEL,
        )
        query_default_params_clf = {
            "X": X,
            "y": y,
            "ensemble": clf,
            "fit_ensemble": True,
        }

        # Create test setting for regression.
        reg = SklearnRegressor(
            RandomForestRegressor(random_state=0),
            missing_label=MISSING_LABEL,
            random_state=0,
        )
        query_default_params_reg = {
            "X": X,
            "y": y,
            "ensemble": reg,
            "fit_ensemble": True,
        }

        # Setup initial parameters, where `QueryByCommittee` is used because
        # it can handle classification and regression models.
        super().setUp(
            qs_class=ParallelUtilityEstimationWrapper,
            init_default_params={
                "query_strategy": QueryByCommittee(random_state=0),
                "n_jobs": 2,
            },
            query_default_params_clf=query_default_params_clf,
            query_default_params_reg=query_default_params_reg,
        )

    def test_init_param_query_strategy(self):
        test_cases = [
            (QueryByCommittee(), None),
            (np.nan, TypeError),
            ("state", TypeError),
            (1.1, TypeError),
        ]
        self._test_param("init", "query_strategy", test_cases)

    def test_init_param_n_jobs(self):
        test_cases = [
            (2, None),
            (-1, None),
            (0, ValueError),
            ("multi", TypeError),
            ([0], TypeError),
        ]
        self._test_param("init", "n_jobs", test_cases)

    def test_init_param_parallel_dict(self):
        test_cases = [
            ({"backend": "threading"}, None),
            ({"backend": "loky", "batch_size": 2}, None),
            ({"abcdefg": "test"}, TypeError),
            (0, TypeError),
            ("multi", TypeError),
            ([0], TypeError),
        ]
        self._test_param("init", "parallel_dict", test_cases)

    def test_query_param_query_kwargs(self, test_cases=None):
        test_cases = [] if test_cases is None else test_cases
        test_cases += [(2, TypeError), (True, None), ("Hello", TypeError)]
        # Check is adjusted for clf since it is exemplary used
        # as parameters to the default query strategy of this test.
        self._test_param("query", "fit_ensemble", test_cases)

    def test_query(self):
        qs = deepcopy(self.init_default_params["query_strategy"])
        qs_sub = self.qs_class(**deepcopy(self.init_default_params))

        for query_params in [
            self.query_default_params_clf,
            self.query_default_params_reg,
        ]:
            query_params = deepcopy(query_params)
            query_params["return_utilities"] = True
            query_params["batch_size"] = 1
            query_params["candidates"] = query_params["X"]
            (
                q,
                u,
            ) = qs.query(**query_params)
            u = u.ravel()
            q_sub, u_sub = qs_sub.query(**query_params)
            u_sub = u_sub.ravel()
            mask = ~np.isnan(u_sub)
            np.testing.assert_array_equal(u[mask], u_sub[mask])
            query_params["return_utilities"] = False
            q_sub = qs_sub.query(**query_params)
            self.assertEqual(len(q_sub), 1)
