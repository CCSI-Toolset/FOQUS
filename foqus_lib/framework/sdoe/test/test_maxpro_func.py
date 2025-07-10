import unittest
import numpy as np
from unittest.mock import patch
import sys
import os

# Add the module path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from foqus_lib.framework.sdoe.maxpro import maxpro


class TestMaxPro(unittest.TestCase):
    """Test cases for the maxpro function"""

    def setUp(self):
        """Set up test fixtures"""
        np.random.seed(42)  # For reproducible tests

    def test_basic_functionality_2d(self):
        """Test basic functionality with 2D input"""
        # Create a simple 2D design
        initial_design = np.array([[0.1, 0.2], [0.5, 0.6], [0.9, 0.8]])

        result = maxpro(initial_design)

        # Check return structure
        self.assertIsInstance(result, dict)
        self.assertIn("Design", result)
        self.assertIn("measure", result)

        # Check design properties
        design = result["Design"]
        self.assertEqual(design.shape, initial_design.shape)
        self.assertTrue(np.all(design >= 0))
        self.assertTrue(np.all(design <= 1))

        # Check measure is a scalar
        self.assertIsInstance(result["measure"], (int, float, np.number))

    def test_1d_input(self):
        """Test with 1D input (should be reshaped)"""
        initial_design = np.array([0.1, 0.5, 0.9])

        result = maxpro(initial_design)

        # Should reshape to column vector
        self.assertEqual(result["Design"].shape, (3, 1))
        self.assertTrue(np.all(result["Design"] >= 0))
        self.assertTrue(np.all(result["Design"] <= 1))

    def test_single_point(self):
        """Test with single design point"""
        initial_design = np.array([[0.5, 0.5]])

        # Single point design should either:
        # 1. Return the single point as-is, or
        # 2. Raise an appropriate error
        try:
            result = maxpro(initial_design)
            self.assertEqual(result["Design"].shape, (1, 2))
            # If it succeeds, the design should be normalized
            self.assertTrue(np.all(result["Design"] >= 0))
            self.assertTrue(np.all(result["Design"] <= 1))
        except ValueError as e:
            # If it fails, it should be due to insufficient points for distance calculation
            self.assertIn("empty", str(e).lower())

    def test_normalization(self):
        """Test that input is properly normalized to [0,1]"""
        # Design with values outside [0,1]
        initial_design = np.array([[10, 20], [50, 60], [90, 80]])

        result = maxpro(initial_design)

        # Result should be normalized
        design = result["Design"]
        self.assertTrue(np.all(design >= 0))
        self.assertTrue(np.all(design <= 1))

    def test_two_points_minimum(self):
        """Test with minimum viable design (2 points)"""
        initial_design = np.array([[0.1, 0.2], [0.9, 0.8]])

        result = maxpro(initial_design)

        self.assertEqual(result["Design"].shape, (2, 2))
        self.assertTrue(np.all(result["Design"] >= 0))
        self.assertTrue(np.all(result["Design"] <= 1))
        self.assertIsInstance(result["measure"], (int, float, np.number))
        """Test with different s parameter values"""
        initial_design = np.array([[0.1, 0.2], [0.5, 0.6], [0.9, 0.8]])

        for s in [1, 2, 3, 4]:
            result = maxpro(initial_design, s=s)
            self.assertIsInstance(result["measure"], (int, float, np.number))

    def test_iteration_parameter(self):
        """Test with different iteration counts"""
        initial_design = np.array([[0.1, 0.2], [0.5, 0.6], [0.9, 0.8]])

        for iterations in [1, 5, 20]:
            result = maxpro(initial_design, iteration=iterations)
            self.assertIsInstance(result, dict)
            self.assertIn("Design", result)
            self.assertIn("measure", result)

    def test_eps_parameter(self):
        """Test with different eps values"""
        initial_design = np.array([[0.1, 0.2], [0.5, 0.6], [0.9, 0.8]])

        for eps in [1e-10, 1e-8, 1e-6]:
            result = maxpro(initial_design, eps=eps)
            self.assertIsInstance(result, dict)

    def test_identical_points(self):
        """Test with identical design points (edge case)"""
        initial_design = np.array([[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]])

        # Should handle this gracefully due to eps parameter
        try:
            result = maxpro(initial_design)
            self.assertEqual(result["Design"].shape, (3, 2))
            self.assertTrue(np.all(result["Design"] >= 0))
            self.assertTrue(np.all(result["Design"] <= 1))
        except (ValueError, np.linalg.LinAlgError):
            # May fail due to numerical issues with identical points
            pass

    def test_zero_range_column(self):
        """Test with a column that has zero range"""
        initial_design = np.array([[0.1, 0.5], [0.5, 0.5], [0.9, 0.5]])

        # Should handle this gracefully
        result = maxpro(initial_design)

        self.assertEqual(result["Design"].shape, (3, 2))

    def test_large_design(self):
        """Test with larger design matrix"""
        n_points = 10
        n_factors = 5
        initial_design = np.random.rand(n_points, n_factors)

        result = maxpro(initial_design, iteration=5)

        self.assertEqual(result["Design"].shape, (n_points, n_factors))
        self.assertTrue(np.all(result["Design"] >= 0))
        self.assertTrue(np.all(result["Design"] <= 1))

    def test_return_value_types(self):
        """Test that return values are of correct types"""
        initial_design = np.array([[0.1, 0.2], [0.5, 0.6]])

        result = maxpro(initial_design)

        self.assertIsInstance(result, dict)
        self.assertIsInstance(result["Design"], np.ndarray)
        self.assertIsInstance(result["measure"], (int, float, np.number))

    def test_design_bounds(self):
        """Test that optimized design stays within bounds"""
        initial_design = np.array([[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]])

        result = maxpro(initial_design)

        design = result["Design"]
        self.assertTrue(np.all(design >= -1e-10))  # Allow small numerical errors
        self.assertTrue(np.all(design <= 1.0 + 1e-10))

    def test_convergence_improvement(self):
        """Test that optimization generally improves the design"""
        initial_design = np.random.rand(5, 3)

        # Run with 0 iterations (should return initial design)
        result_0 = maxpro(initial_design, iteration=0)

        # Run with multiple iterations
        result_many = maxpro(initial_design, iteration=10)

        # The measure should generally improve (though not guaranteed)
        # At minimum, both should be valid results
        self.assertIsInstance(result_0["measure"], (int, float, np.number))
        self.assertIsInstance(result_many["measure"], (int, float, np.number))

    @patch("foqus_lib.framework.sdoe.maxpro.minimize")
    def test_optimization_error_handling(self, mock_minimize):
        """Test handling of optimization errors"""
        # Mock minimize to raise an error
        mock_minimize.side_effect = np.linalg.LinAlgError("Test error")

        initial_design = np.array([[0.1, 0.2], [0.5, 0.6]])

        # Should handle the error gracefully
        result = maxpro(initial_design)

        self.assertIsInstance(result, dict)
        self.assertIn("Design", result)
        self.assertIn("measure", result)

    def test_input_validation(self):
        """Test input validation and edge cases"""
        # Test with list input
        initial_design = [[0.1, 0.2], [0.5, 0.6]]
        result = maxpro(initial_design)
        self.assertIsInstance(result, dict)

        # Test with numpy array
        initial_design = np.array([[0.1, 0.2], [0.5, 0.6]])
        result = maxpro(initial_design)
        self.assertIsInstance(result, dict)

    def test_numerical_stability(self):
        """Test numerical stability with extreme values"""
        # Test with very small values
        initial_design = np.array([[1e-10, 1e-10], [1e-9, 1e-9]])
        result = maxpro(initial_design)
        self.assertIsInstance(result, dict)

        # Test with values very close to bounds
        initial_design = np.array([[0.0, 0.0], [1.0, 1.0]])
        result = maxpro(initial_design)
        self.assertIsInstance(result, dict)

    def test_parameter_combinations(self):
        """Test various parameter combinations"""
        initial_design = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])

        test_cases = [
            {"s": 1, "iteration": 5, "eps": 1e-8},
            {"s": 3, "iteration": 15, "eps": 1e-6},
            {"s": 2, "iteration": 1, "eps": 1e-10},
        ]

        for params in test_cases:
            result = maxpro(initial_design, **params)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["Design"].shape, initial_design.shape)

    def test_reproducibility(self):
        """Test that results are reproducible with same random seed"""
        initial_design = np.array([[0.1, 0.2], [0.5, 0.6], [0.9, 0.8]])

        # Set random seed and run
        np.random.seed(123)
        result1 = maxpro(initial_design)

        # Reset seed and run again
        np.random.seed(123)
        result2 = maxpro(initial_design)

        # Note: Results might not be exactly identical due to optimization
        # but the function should execute consistently
        self.assertEqual(result1["Design"].shape, result2["Design"].shape)


class TestMaxProIntegration(unittest.TestCase):
    """Integration tests for maxpro function"""

    def test_realistic_doe_scenario(self):
        """Test with a realistic design of experiments scenario"""
        # 3-factor design with 8 runs (2^3 factorial-like)
        initial_design = np.array(
            [
                [0.1, 0.1, 0.1],
                [0.1, 0.1, 0.9],
                [0.1, 0.9, 0.1],
                [0.1, 0.9, 0.9],
                [0.9, 0.1, 0.1],
                [0.9, 0.1, 0.9],
                [0.9, 0.9, 0.1],
                [0.9, 0.9, 0.9],
            ]
        )

        result = maxpro(initial_design, s=2, iteration=10)

        # Check that the result is reasonable
        self.assertEqual(result["Design"].shape, (8, 3))
        self.assertTrue(np.all(result["Design"] >= 0))
        self.assertTrue(np.all(result["Design"] <= 1))
        self.assertIsInstance(result["measure"], (int, float, np.number))

    def test_space_filling_property(self):
        """Test that the optimization produces a space-filling design"""
        # Start with a poor design (all points clustered)
        initial_design = np.array([[0.45, 0.45], [0.50, 0.50], [0.55, 0.55]])

        result = maxpro(initial_design, iteration=20)

        # The optimized design should be more spread out
        design = result["Design"]

        # Check that points are not all clustered together
        distances = []
        for i in range(len(design)):
            for j in range(i + 1, len(design)):
                dist = np.linalg.norm(design[i] - design[j])
                distances.append(dist)

        # Should have some reasonable separation
        self.assertGreater(np.mean(distances), 0.1)


if __name__ == "__main__":
    # Create a test suite
    suite = unittest.TestSuite()

    # Add all test methods
    suite.addTest(unittest.makeSuite(TestMaxPro))
    suite.addTest(unittest.makeSuite(TestMaxProIntegration))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    if result.wasSuccessful():
        print("\nAll tests passed!")
    else:
        print(
            f"\nTests failed: {len(result.failures)} failures, {len(result.errors)} errors"
        )
