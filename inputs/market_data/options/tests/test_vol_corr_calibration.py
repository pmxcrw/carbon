from inputs.market_data.options.vol_corr_calibration import Factor, SingleAssetVolCorrCalibration, \
                                                            MultiAssetVolCorrCalibration, VolCorrCalibrationError

import unittest
import numpy as np
from numpy.linalg import LinAlgError

UKPOWER_PEAK = SingleAssetVolCorrCalibration(factors=[Factor(0.2, 0.1), Factor(0.2, 20)],
                                             factor_correlations={(0, 1): 0.3})

NBP = SingleAssetVolCorrCalibration(factors=[Factor(0.1, 0.5), Factor(0.15, 10), Factor(0.3, 20)],
                                    factor_correlations={(0, 1): 0.8,
                                                         (0, 2): 0.7,
                                                         (1, 2): 0.9})

inter_asset_correlation = {("UKPOWER_PEAK", "NBP"): [[0.4, 0.5, 0.7], [0.6, 0.7, 0.8]]}

SPARK = MultiAssetVolCorrCalibration({"UKPOWER_PEAK": UKPOWER_PEAK, "NBP": NBP}, inter_asset_correlation)


class SingleAssetVolCorrTestCase(unittest.TestCase):

    def test_empty_vol_corr(self):
        """Test whether we can build an empty object"""
        vol_corr = SingleAssetVolCorrCalibration([],{})
        self.assertEqual([], vol_corr.factors)

    def test_factor_correlation(self):
        self.assertEqual(0.8, NBP.rho(0, 1))
        self.assertEqual(0.7, NBP.rho(0, 2))
        self.assertEqual(0.9, NBP.rho(1, 2))
        self.assertEqual(0.8, NBP.rho(1, 0))
        self.assertEqual(0.7, NBP.rho(2, 0))
        self.assertEqual(0.9, NBP.rho(2, 1))

    def test_factors(self):
        self.assertEqual(0.1, NBP.sigma(0))
        self.assertEqual(0.5, NBP.alpha(0))
        self.assertEqual(0.15, NBP.sigma(1))
        self.assertEqual(10, NBP.alpha(1))
        self.assertEqual(0.3, NBP.sigma(2))
        self.assertEqual(20, NBP.alpha(2))

class MultiAssetVolCorrTestCase(unittest.TestCase):

    def test_PSD_error(self):
        """Check whether the constructor throws an exception if the correlations form a non PSD matrix"""
        with self.assertRaises(LinAlgError):
            bad_NBP = SingleAssetVolCorrCalibration(factors=[Factor(0.1, 0.5), Factor(0.15, 10)],
                                                    factor_correlations={(0, 1): 0.9})
            bad_inter_asset_correlation = {("UKPOWER_PEAK", "NBP"): [[0.4, 0.5], [0.6, 0.9]]}
            MultiAssetVolCorrCalibration({"UKPOWER_PEAK": UKPOWER_PEAK, "NBP": bad_NBP}, bad_inter_asset_correlation)

    def test_factor_correlation(self):
        self.assertEqual(0.3, SPARK.rho("UKPOWER_PEAK", 0, "UKPOWER_PEAK", 1))
        self.assertEqual(0.4, SPARK.rho("UKPOWER_PEAK", 0, "NBP", 0))
        self.assertEqual(0.5, SPARK.rho("UKPOWER_PEAK", 0, "NBP", 1))
        self.assertEqual(0.7, SPARK.rho("UKPOWER_PEAK", 0, "NBP", 2))
        self.assertEqual(0.6, SPARK.rho("UKPOWER_PEAK", 1, "NBP", 0))
        self.assertEqual(0.7, SPARK.rho("UKPOWER_PEAK", 1, "NBP", 1))
        self.assertEqual(0.8, SPARK.rho("UKPOWER_PEAK", 1, "NBP", 2))
        self.assertEqual(1, SPARK.rho("UKPOWER_PEAK", 0, "UKPOWER_PEAK", 0))

    def test_factors(self):
        self.assertEqual(0.1, SPARK.sigma("NBP", 0))
        self.assertEqual(0.5, SPARK.alpha("NBP", 0))
        self.assertEqual(0.15, SPARK.sigma("NBP", 1))
        self.assertEqual(10, SPARK.alpha("NBP", 1))
        self.assertEqual(0.3, SPARK.sigma("NBP", 2))
        self.assertEqual(20, SPARK.alpha("NBP", 2))

    def test_missing_asset(self):
        """Check whether an error is thrown if the correlations don't have the correct assets"""
        with self.assertRaises(VolCorrCalibrationError):
            bad_inter_asset_correlation = {("UKPOWER_BASE", "NBP"): [[0.4, 0.5], [0.6, 0.9]]}
            MultiAssetVolCorrCalibration({"UKPOWER_PEAK": UKPOWER_PEAK, "NBP": NBP}, bad_inter_asset_correlation)
