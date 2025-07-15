import numpy as np
import pytest
from unittest.mock import patch
from foqus_lib.framework.sdoe.maxpro import maxpro_augment


class TestMaxProAugment:
    """Test suite for maxpro_augment function"""

    def setup_method(self):
        """Set up test fixtures"""
        # Basic continuous design
        self.exist_design_2d = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
        self.cand_design_2d = np.array([[0.7, 0.8], [0.9, 1.0], [0.0, 0.1], [0.2, 0.3]])

        # 1D design for edge cases
        self.exist_design_1d = np.array([0.1, 0.3, 0.5])
        self.cand_design_1d = np.array([0.7, 0.9, 0.0])

        # Mixed variable design (continuous + discrete numeric)
        self.exist_mixed = np.array([[0.1, 0.2, 1], [0.3, 0.4, 2], [0.5, 0.6, 1]])
        self.cand_mixed = np.array([[0.7, 0.8, 3], [0.9, 1.0, 2], [0.0, 0.1, 1]])

        # Nominal variables design
        self.exist_nominal = np.array([[0.1, 0.2, 0], [0.3, 0.4, 1], [0.5, 0.6, 2]])
        self.cand_nominal = np.array([[0.7, 0.8, 1], [0.9, 1.0, 2], [0.0, 0.1, 0]])

    @pytest.mark.skip()
    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_basic_continuous_augmentation(self, mock_core):
        """Test basic continuous variable augmentation"""
        mock_core.return_value = (
            np.vstack([self.exist_design_2d, self.cand_design_2d[:2]]),
            0.5,
            1,
        )

        result = maxpro_augment(self.exist_design_2d, self.cand_design_2d, n_new=2)

        assert isinstance(result, dict)
        assert "Design" in result
        assert "measure" in result
        assert "time_rec" in result
        assert result["Design"].shape == (5, 2)  # 3 existing + 2 new
        assert result["measure"] == 0.25  # 0.5^2
        assert isinstance(result["time_rec"], float)

        # Check that core function was called with correct parameters
        mock_core.assert_called_once()
        args = mock_core.call_args[0]
        assert np.array_equal(args[0], np.zeros(2))  # lambda_vals for continuous
        assert np.array_equal(args[1], self.exist_design_2d)
        assert np.array_equal(args[2], self.cand_design_2d)
        assert args[3] == 2  # n_new
        assert args[4] == 0  # p_nom
        assert args[5] == 2  # s

    @pytest.mark.skip()
    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_1d_design_reshaping(self, mock_core):
        """Test that 1D existing design is properly reshaped"""
        mock_core.return_value = (np.array([[0.1], [0.3], [0.5], [0.7]]), 0.3, 1)

        result = maxpro_augment(
            self.exist_design_1d, self.cand_design_1d.reshape(-1, 1), n_new=1
        )

        assert result["Design"].shape == (4, 1)
        mock_core.assert_called_once()

    def test_dimension_mismatch_error(self):
        """Test error when candidate and existing designs have different dimensions"""
        with pytest.raises(ValueError, match="different dimensions"):
            maxpro_augment(
                self.exist_design_2d, self.cand_design_1d.reshape(-1, 1), n_new=1
            )

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_discrete_numeric_variables(self, mock_core):
        """Test handling of discrete numeric variables"""
        mock_core.return_value = (
            np.vstack([self.exist_mixed, self.cand_mixed[:1]]),
            0.4,
            1,
        )

        result = maxpro_augment(
            self.exist_mixed, self.cand_mixed, n_new=1, p_disnum=1, l_disnum=[3]
        )

        assert result["Design"].shape == (4, 3)

        # Check lambda values calculation
        args = mock_core.call_args[0]
        expected_lambda = np.array(
            [0.0, 0.0, 1.0 / 3]
        )  # 2 continuous + 1 discrete with 3 levels
        np.testing.assert_array_almost_equal(args[0], expected_lambda)

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_discrete_numeric_auto_levels(self, mock_core):
        """Test automatic level detection for discrete numeric variables"""
        mock_core.return_value = (
            np.vstack([self.exist_mixed, self.cand_mixed[:1]]),
            0.4,
            1,
        )

        result = maxpro_augment(self.exist_mixed, self.cand_mixed, n_new=1, p_disnum=1)

        # Should automatically detect 3 levels (1, 2, 3)
        args = mock_core.call_args[0]
        expected_lambda = np.array([0.0, 0.0, 1.0 / 3])
        np.testing.assert_array_almost_equal(args[0], expected_lambda)

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_nominal_variables(self, mock_core):
        """Test handling of nominal variables"""
        mock_core.return_value = (
            np.vstack([self.exist_nominal, self.cand_nominal[:1]]),
            0.6,
            1,
        )

        result = maxpro_augment(
            self.exist_nominal, self.cand_nominal, n_new=1, p_nom=1, l_nom=[3]
        )

        assert result["Design"].shape == (4, 3)

        # Check lambda values calculation
        args = mock_core.call_args[0]
        expected_lambda = np.array(
            [0.0, 0.0, 1.0 / 3]
        )  # 2 continuous + 1 nominal with 3 levels
        np.testing.assert_array_almost_equal(args[0], expected_lambda)

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_nominal_variables_auto_levels(self, mock_core):
        """Test automatic level detection for nominal variables"""
        mock_core.return_value = (
            np.vstack([self.exist_nominal, self.cand_nominal[:1]]),
            0.6,
            1,
        )

        result = maxpro_augment(self.exist_nominal, self.cand_nominal, n_new=1, p_nom=1)

        # Should automatically detect 3 levels (0, 1, 2)
        args = mock_core.call_args[0]
        expected_lambda = np.array([0.0, 0.0, 1.0 / 3])
        np.testing.assert_array_almost_equal(args[0], expected_lambda)

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_mixed_discrete_and_nominal(self, mock_core):
        """Test handling of both discrete numeric and nominal variables"""
        # Design with 1 continuous, 1 discrete numeric, 1 nominal
        exist_design = np.array([[0.1, 1, 0], [0.3, 2, 1], [0.5, 1, 2]])
        cand_design = np.array([[0.7, 3, 1], [0.9, 2, 0]])

        mock_core.return_value = (np.vstack([exist_design, cand_design[:1]]), 0.7, 1)

        result = maxpro_augment(
            exist_design,
            cand_design,
            n_new=1,
            p_disnum=1,
            l_disnum=[3],
            p_nom=1,
            l_nom=[3],
        )

        # Check lambda values: 1 continuous (0), 1 discrete (1/3), 1 nominal (1/3)
        args = mock_core.call_args[0]
        expected_lambda = np.array([0.0, 1.0 / 3, 1.0 / 3])
        np.testing.assert_array_almost_equal(args[0], expected_lambda)

    def test_invalid_p_disnum_p_nom_sum(self):
        """Test error when p_disnum + p_nom exceeds total columns"""
        with pytest.raises(ValueError, match="exceeds the total number of columns"):
            maxpro_augment(
                self.exist_design_2d, self.cand_design_2d, n_new=1, p_disnum=2, p_nom=1
            )

    def test_invalid_l_disnum_length(self):
        """Test error when l_disnum length doesn't match p_disnum"""
        with pytest.raises(
            ValueError, match="Length of l_disnum does not match p_disnum"
        ):
            maxpro_augment(
                self.exist_mixed,
                self.cand_mixed,
                n_new=1,
                p_disnum=1,
                l_disnum=[2, 3],  # Length 2 but p_disnum=1
            )

    def test_invalid_l_nom_length(self):
        """Test error when l_nom length doesn't match p_nom"""
        with pytest.raises(ValueError, match="Length of l_nom does not match p_nom"):
            maxpro_augment(
                self.exist_nominal,
                self.cand_nominal,
                n_new=1,
                p_nom=1,
                l_nom=[2, 3],  # Length 2 but p_nom=1
            )

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_success_flag_zero_warning(self, mock_core, capsys):
        """Test warning message when success_flag is 0"""
        mock_core.return_value = (self.exist_design_2d, 0.5, 0)  # success_flag = 0

        result = maxpro_augment(self.exist_design_2d, self.cand_design_2d, n_new=1)

        captured = capsys.readouterr()
        assert "Note: Not enough candidate rows" in captured.out
        assert "continuous factor" in captured.out

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_timing_measurement(self, mock_core):
        """Test that timing is properly measured"""
        # Mock time.time() to return predictable values
        with patch("time.time", side_effect=[100.0, 101.5]):
            mock_core.return_value = (self.exist_design_2d, 0.5, 1)

            result = maxpro_augment(self.exist_design_2d, self.cand_design_2d, n_new=1)

            assert result["time_rec"] == 1.5

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_measure_squaring(self, mock_core):
        """Test that the measure is squared in the result"""
        mock_core.return_value = (self.exist_design_2d, 0.6, 1)

        result = maxpro_augment(self.exist_design_2d, self.cand_design_2d, n_new=1)

        assert result["measure"] == 0.36  # 0.6^2

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_numpy_array_conversion(self, mock_core):
        """Test that inputs are properly converted to numpy arrays"""
        mock_core.return_value = (self.exist_design_2d, 0.5, 1)

        # Test with Python lists
        exist_list = [[0.1, 0.2], [0.3, 0.4]]
        cand_list = [[0.7, 0.8], [0.9, 1.0]]

        result = maxpro_augment(exist_list, cand_list, n_new=1)

        # Should work without errors
        assert "Design" in result

        # Check that arrays were passed to core function
        args = mock_core.call_args[0]
        assert isinstance(args[1], np.ndarray)
        assert isinstance(args[2], np.ndarray)

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_zero_new_points(self, mock_core):
        """Test behavior when n_new=0"""
        mock_core.return_value = (self.exist_design_2d, 0.5, 1)

        result = maxpro_augment(self.exist_design_2d, self.cand_design_2d, n_new=0)

        mock_core.assert_called_once()
        args = mock_core.call_args[0]
        assert args[3] == 0  # n_new should be 0

    @patch("foqus_lib.framework.sdoe.maxpro.maxpro_augment_core")
    def test_large_n_new(self, mock_core):
        """Test behavior when n_new is larger than candidate set"""
        mock_core.return_value = (self.exist_design_2d, 0.5, 1)

        result = maxpro_augment(self.exist_design_2d, self.cand_design_2d, n_new=10)

        mock_core.assert_called_once()
        args = mock_core.call_args[0]
        assert args[3] == 10  # n_new should be passed as-is

    def test_empty_designs(self):
        """Test behavior with empty designs"""
        empty_design = np.array([]).reshape(0, 2)

        with pytest.raises((ValueError, IndexError)):
            maxpro_augment(empty_design, self.cand_design_2d, n_new=1)


# Integration test (requires actual maxpro_augment_core function)
class TestMaxProAugmentIntegration:
    """Integration tests that would require the actual maxpro_augment_core function"""

    @pytest.mark.skip(reason="Requires actual maxpro_augment_core implementation")
    def test_full_integration_continuous(self):
        """Test full integration with continuous variables"""
        exist_design = np.array([[0.1, 0.2], [0.3, 0.4]])
        cand_design = np.array([[0.7, 0.8], [0.9, 1.0], [0.0, 0.1]])

        result = maxpro_augment(exist_design, cand_design, n_new=2)

        assert result["Design"].shape == (4, 2)
        assert result["measure"] > 0
        assert result["time_rec"] >= 0

    @pytest.mark.skip(reason="Requires actual maxpro_augment_core implementation")
    def test_full_integration_mixed_variables(self):
        """Test full integration with mixed variable types"""
        exist_design = np.array([[0.1, 0.2, 1, 0], [0.3, 0.4, 2, 1]])
        cand_design = np.array([[0.7, 0.8, 1, 2], [0.9, 1.0, 3, 0]])

        result = maxpro_augment(
            exist_design,
            cand_design,
            n_new=1,
            p_disnum=1,
            l_disnum=[3],
            p_nom=1,
            l_nom=[3],
        )

        assert result["Design"].shape == (3, 4)
        assert result["measure"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
