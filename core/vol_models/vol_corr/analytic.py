from core.vol_models.vol_corr.factor import Factor

import numpy as np


class SingleAssetAnalytics(object):

    """
    This class provides analytic vols and intra asset correlations from a SingleAssetVolCorrCalibration
    """

    def __init__(self, single_asset_vol_corr_calibration):
        """
        :param single_asset_vol_corr_calibration: SingleAssetVolCorrCalibraiton object
        """
        alphas, sigmas = [], []
        for factor in single_asset_vol_corr_calibration.factors:
            alphas.append(factor.alpha)
            sigmas.append(factor.sigma)
        self.alphas = np.array(alphas)
        self.sigmas = np.array(sigmas)
        self.rho_matrix = single_asset_vol_corr_calibration.rho_matrix
        self._sigma_array = self.sigmas[:, np.newaxis] * self.sigmas  # matrix who's i,j element is sigma[i] * sigma[j]
        self._alpha_array = self.alphas[:, np.newaxis] + self.alphas  # matrix who's i,j element is alpha[i] + alpha[j]

    def _scaled_correlations(self, t=None):
        if not t:
            # return the array needed to calculate instantaneous correlations
            return self.rho_matrix * self._sigma_array
        return self.rho_matrix * self._sigma_array / self._alpha_array * (1 - np.exp(-self._alpha_array * t))

    def decay_corrections(self, t, T):
        return np.exp(-self.alphas * (T - t))

    def duration_corrections(self, D):
        if D == 0:
            return np.ones_like(self.alphas)
        return (1 - np.exp(-self.alphas * D)) / (self.alphas * D)

    def _vol(self, t, T, D):
        """Calculates either the terminal vol (if t  > 0) or instantaneous vol (if t == 0)"""
        vector = self.decay_corrections(t, T) * self.duration_corrections(D)
        total_variance = vector @ self._scaled_correlations(t) @ vector
        if t:
            return np.sqrt(total_variance / t)
        else:
            return np.sqrt(total_variance)

    def vol(self, t, T, D):
        return self._vol(t, T, D)

    def inst_vol(self, T, D):
        return self._vol(0, T, D)

    def _covariance(self, t, T1, D1, T2, D2):
        """common calculations for correlation and instantaneous correlation (instantaneous correlation calculations
        correspond to setting t == 0"""
        lhs_vector = self.decay_corrections(t, T1) * self.duration_corrections(D1)
        rhs_vector = self.decay_corrections(t, T2) * self.duration_corrections(D2)
        scaled_correlations = self._scaled_correlations(t)

        # this bit is ugly but performance enhancing, avoids doing the same matrix multuplication twice
        cached = lhs_vector @ scaled_correlations  # this multiplication appears in lhs_vol and covariance
        lhs_variance= cached @ lhs_vector
        covariance = cached @ rhs_vector

        rhs_variance = rhs_vector @ scaled_correlations @ rhs_vector
        return lhs_variance, covariance, rhs_variance

    def correlation(self, t, T1, D1, T2, D2):
        lhs_variance, covariance, rhs_variance = self._covariance(t, T1, D1, T2, D2)
        return covariance * t / np.sqrt(lhs_variance * rhs_variance)

    def inst_correlation(self, T1, D1, T2, D2):
        lhs_variance, covariance, rhs_variance = self._covariance(0, T1, D1, T2, D2)
        return covariance / np.sqrt(lhs_variance * rhs_variance)


class MultiAssetAnalytics(object):

    """
    This class provides inter-asset correlations from a MultiAssetVolCorrCalibration
    """

    def __init__(self, multi_asset_vol_corr_calibration):
        """
        :param multi_asset_vol_corr_calibration: a MultiAssetVolCorrCalibration object
        """
        self.rho_matrix = multi_asset_vol_corr_calibration.rho_matrix
        self.asset_factor_map = multi_asset_vol_corr_calibration.asset_factor_map
        alphas, sigmas = [], []
        for factor in multi_asset_vol_corr_calibration.factors:
            alphas.append(factor.alpha)
            sigmas.append(factor.sigma)
        self.alphas = np.array(alphas)
        self.sigmas = np.array(sigmas)

    def _sigma_by_asset(self, asset):
        asset = self.asset_factor_map[asset]
        return self.sigmas[asset[0]:asset[1]]

    def _alpha_by_asset(self, asset):
        asset = self.asset_factor_map[asset]
        return self.alphas[asset[0]:asset[1]]

    def _rho_by_assets(self, asset1, asset2):
        asset1 = self.asset_factor_map[asset1]
        asset2 = self.asset_factor_map[asset2]
        return self.rho_matrix[asset1[0]:asset1[1], asset2[0]:asset2[1]]

    def _sigma_array(self, asset1, asset2):
        """
        Builds a matrix who's (i, j)th element is the i-th sigma in asset1 multiplied by the j-th sigma in asset2

        :param asset1: str name of asset1
        :param asset2: str name of asset2
        :return: array
        """
        return self._sigma_by_asset(asset1)[:, np.newaxis] * self._sigma_by_asset(asset2)

    def _alpha_array(self, asset1, asset2):
        """
        Builds a matrix who's (i, j)th element is the i-th alpha in asset1 plus the j-th alpha in asset2

        :param asset1: str name of asset1
        :param asset2: str name of asset2
        :return: array
        """
        return self._alpha_by_asset(asset1)[:, np.newaxis] + self._alpha_by_asset(asset2)

    def _scaled_correlations(self, asset1, asset2, t=None):
        rho = self._rho_by_assets(asset1, asset2)
        sigma_array = self._sigma_array(asset1, asset2)
        if not t:
            return rho * sigma_array
        alpha_array = self._alpha_array(asset1, asset2)
        return rho * sigma_array / alpha_array * (1 - np.exp(-alpha_array * t))

    def decay_corrections(self, t, T, asset):
        return np.exp(-self._alpha_by_asset(asset) * (T - t))

    def duration_corrections(self, D, asset):
        if D == 0:
            return np.ones_like(self._alpha_by_asset(asset))
        alphas = self._alpha_by_asset(asset)
        return (1 - np.exp(-alphas * D)) / (alphas * D)

    def _vol(self, t, asset, T, D):
        """Calculates either the terminal vol (if t  > 0) or instantaneous vol (if t == 0)"""
        vector = self.decay_corrections(t, T, asset) * self.duration_corrections(D, asset)
        array = self._scaled_correlations(asset, asset, t)
        total_variance = vector @ array @ vector[:, np.newaxis]
        if t:
            return np.sqrt(total_variance / t)
        else:
            return np.sqrt(total_variance)

    def vol(self, t, asset, T, D):
        return self._vol(t, asset, T, D)

    def inst_vol(self, asset, T, D):
        return self._vol(0, asset, T, D)

    def _covariance(self, t, asset1, T1, D1, asset2, T2, D2):
        """common calculations for correlation and instantaneous correlation (instantaneous correlation calculations
        correspond to setting t == 0"""
        asset2 = asset2 if asset2 else asset1
        T2 = T2 if T2 else T1
        D2 = D2 if D2 else D1

        vector1 = self.decay_corrections(t, T1, asset1) * self.duration_corrections(D1, asset1)
        vector1_T = vector1[:, np.newaxis]
        vector2 = self.decay_corrections(t, T2, asset2) * self.duration_corrections(D2, asset2)
        vector2_T = vector2[:, np.newaxis]

        array1 = self._scaled_correlations(asset1, asset1, t)
        array2 = self._scaled_correlations(asset2, asset2, t)
        array12 = self._scaled_correlations(asset1, asset2, t)

        covariance = vector1 @ array12 @ vector2_T
        variance1 = vector1 @ array1 @ vector1_T
        variance2 = vector2 @ array2 @ vector2_T

        return variance1, covariance, variance2

    def correlation(self, t, asset1, T1, D1, asset2, T2, D2):
        lhs_variance, covariance, rhs_variance = self._covariance(t, asset1, T1, D1, asset2, T2, D2)
        return covariance * t / np.sqrt(lhs_variance * rhs_variance)

    def inst_correlation(self, asset1, T1, D1, asset2, T2, D2):
        lhs_variance, covariance, rhs_variance = self._covariance(0, asset1, T1, D1, asset2, T2, D2)
        return covariance / np.sqrt(lhs_variance * rhs_variance)
