import unittest

import numpy as np

from skactiveml.utils import mesh, check_bound


class TestAuxiliaryFunctions(unittest.TestCase):

    def test_check_mesh(self):
        bound = np.array([[0, 0], [1, 1]])
        res = 10
        X_mesh, Y_mesh, mesh_instances = mesh(bound, res)

        self.assertEqual(X_mesh.shape, (10, 10))
        self.assertEqual(Y_mesh.shape, (10, 10))
        self.assertEqual(mesh_instances.shape, (100, 2))
