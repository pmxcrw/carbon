from inputs.market_data.options.vol_corr_calibration import Factor, SingleAssetVolCorrCalibration, \
                                                            MultiAssetVolCorrCalibration
from core.vol_models.vol_corr.analytic import SingleAssetAnalytics, MultiAssetAnalytics

import unittest

UKPOWER_PEAK_CALIBRATION = SingleAssetVolCorrCalibration(factors=[Factor(0.2, 0.1), Factor(0.2, 20)],
                                             factor_correlations={(0, 1): 0.3})
UKPOWER_PEAK = SingleAssetAnalytics(UKPOWER_PEAK_CALIBRATION)

NBP_CALIBRATION = SingleAssetVolCorrCalibration(factors=[Factor(0.1, 0.5), Factor(0.15, 10), Factor(0.3, 20)],
                                    factor_correlations={(0, 1): 0.8,
                                                         (0, 2): 0.7,
                                                         (1, 2): 0.9})

NBP = SingleAssetAnalytics(NBP_CALIBRATION)

inter_asset_correlation = {("UKPOWER_PEAK", "NBP"): [[0.4, 0.5, 0.7], [0.6, 0.7, 0.8]]}

SPARK = MultiAssetAnalytics(MultiAssetVolCorrCalibration({"UKPOWER_PEAK": UKPOWER_PEAK_CALIBRATION,
                                                          "NBP": NBP_CALIBRATION},
                                                         inter_asset_correlation))


class SingleAssetAnalyticsTest(unittest.TestCase):

    def test_instantaneous_vol(self):
        T = 0.2
        D = 0.1
        self.assertTrue(abs(0.195543737743486 - UKPOWER_PEAK.inst_vol(T, D)) < 1e-15)
        self.assertTrue(abs(0.100600348590755 - NBP.inst_vol(T, D)) < 1e-15)

    def test_vol(self):
        t = 0.1
        T = 0.2
        D = 0.3
        self.assertTrue(abs(0.194694447675990 - UKPOWER_PEAK.vol(t, T, D)) < 1e-15)
        self.assertTrue(abs(0.097569447353218 - NBP.vol(t, T, D)) < 1e-15)

    def test_inst_corr(self):
        T1 = 0.2
        D1 = 0.1
        T2 = 0.5
        D2 = 0.2
        self.assertTrue(abs(0.999970242260919 - UKPOWER_PEAK.inst_correlation(T1, D1, T2, D2)) < 1e-10)
        self.assertTrue(abs(0.996209363421824 - NBP.inst_correlation(T1, D1, T2, D2)) < 1e-15)

    def test_correlation(self):
        t = 0.1
        T1 = 0.2
        D1 = 0.1
        T2 = 0.5
        D2 = 0.2
        self.assertTrue(abs(0.099960050053073 - UKPOWER_PEAK.correlation(t, T1, D1, T2, D2)) < 1e-15)
        self.assertTrue(abs(0.098527495979982 - NBP.correlation(t, T1, D1, T2, D2)) < 1e-15)


class MultiAssetAnalyticsTest(unittest.TestCase):

    def test_instantaneous_vol(self):
        T = 0.2
        D = 0.1
        self.assertTrue(abs(0.195543737743486 - SPARK.inst_vol("UKPOWER_PEAK", T, D)) < 1e-15)
        self.assertTrue(abs(0.100600348590755 - SPARK.inst_vol("NBP", T, D)) < 1e-15)

    def test_vol(self):
        t = 0.1
        T = 0.2
        D = 0.3
        self.assertTrue(abs(0.194694447675990 - SPARK.vol(t, "UKPOWER_PEAK", T, D)) < 1e-10)
        self.assertTrue(abs(0.097569447353218 - SPARK.vol(t, "NBP", T, D)) < 1e-15)

    def test_inst_corr(self):
        T1 = 0.2
        D1 = 0.1
        T2 = 0.5
        D2 = 0.2
        self.assertTrue(abs(0.999970242260919 -
                            SPARK.inst_correlation("UKPOWER_PEAK", T1, D1, "UKPOWER_PEAK", T2, D2)) < 1e-10)
        self.assertTrue(abs(0.996209363421824 - SPARK.inst_correlation("NBP", T1, D1, "NBP", T2, D2)) < 1e-15)

    def test_multiasset_inst_corr(self):
        T1 = 0.2
        D1 = 0.1
        T2 = 0.5
        D2 = 0.2
        self.assertTrue(abs(0.431242479767532 -
                            SPARK.inst_correlation("NBP", T1, D1, "UKPOWER_PEAK", T2, D2)) < 1e-15)

    def test_correlation(self):
        t = 0.1
        T1 = 0.2
        D1 = 0.1
        T2 = 0.5
        D2 = 0.2
        self.assertTrue(abs(0.099960050053073 -
                            SPARK.correlation(t, "UKPOWER_PEAK", T1, D1, "UKPOWER_PEAK", T2, D2)) < 1e-15)
        self.assertTrue(abs(0.098527495979982 - SPARK.correlation(t, "NBP", T1, D1, "NBP", T2, D2)) < 1e-15)

    def test_multiasset_correlation(self):
        t = 0.1
        T1 = 0.2
        D1 = 0.1
        T2 = 0.5
        D2 = 0.2
        print(SPARK.correlation(t, "NBP", T1, D1, "UKPOWER_PEAK", T2, D2))
        self.assertTrue(abs(0.045543304817166 -
                            SPARK.correlation(t, "NBP", T1, D1, "UKPOWER_PEAK", T2, D2)) < 1e-15)