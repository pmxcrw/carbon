from abc import abstractmethod
from collections import namedtuple

import numpy as np


Factor = namedtuple('Factor', 'sigma alpha')


class VolCorrCalibrationError(Exception):
    """raised when a vol_corr calibration doesn't have required information, or is badly specified"""


class AbstractVolCorrCalibration(object):

    def __init__(self):
        self.cache = {}  # TODO - should these live on the calibration object?
        self.hits = 0 # TODO - should these live on the calibration object?
        self.fails = 0 # TODO - should these live on the calibration object?
        if self.factor_count:
            self.cholesky_decomposition = np.linalg.cholesky(self.rho_matrix)

class SingleAssetVolCorrCalibration(AbstractVolCorrCalibration):

    """
    Class which holds the vol_corr calibration data for a single underlying asset and an ability to transform the
    calibration data when changing numeraire
    """

    def __init__(self, factors, factor_correlations):
        self.factors = factors
        self.factor_count = len(factors)
        self.rho_matrix = self._correlation_matrix(factor_correlations)
        super().__init__()

    def _correlation_matrix(self, factor_correlations):
        expected_corrs = self.factor_count * (self.factor_count - 1) / 2
        if len(factor_correlations) != expected_corrs:
            raise VolCorrCalibrationError("wrong number of rho_matrix, expected {} factors, given {} in :{}"
                                          .format(expected_corrs, len(factor_correlations), factor_correlations))
        matrix = np.zeros((self.factor_count, self.factor_count))
        for x in range(self.factor_count):
            matrix[x, x] = 1
            for y in range(x + 1, self.factor_count):
                try:
                    matrix[x, y] = factor_correlations[(x, y)]
                except KeyError:
                    raise VolCorrCalibrationError("missing factor correlation, couldn't find {} in {}"
                                                  .format((x, y), factor_correlations))
                matrix[y, x] = matrix[x, y]
        return matrix

    def sigma(self, factor):
        return self.factors[factor].sigma

    def alpha(self, factor):
        return self.factors[factor].alpha

    def rho(self, factor1, factor2):
        """Convenience interface for retreiving correlations"""
        return self.rho_matrix[factor1, factor2]


class MultiAssetVolCorrCalibration(AbstractVolCorrCalibration):

    """
    Class which holds vol_corr calibration data and provides an ability to transform the calibration data when
    changing numeraire
    """

    def __init__(self, single_asset_calibrations, inter_asset_correlations):
        self.factors, self.asset_factor_map = self._compose_factors(single_asset_calibrations)
        self.factor_count = len(self.factors)
        inter_asset_correlations = self._parse(inter_asset_correlations)
        self.rho_matrix = self._correlation_matrix(single_asset_calibrations, inter_asset_correlations)
        super().__init__()

    @staticmethod
    def _compose_factors(single_asset_calibrations):
        factors = []
        asset_factor_map = {}
        for asset in sorted(single_asset_calibrations.keys()):
            start = len(factors)
            factors.extend(single_asset_calibrations[asset].factors)
            end = len(factors)
            asset_factor_map[asset] = (start, end)
        return factors, asset_factor_map

    def _parse(self, inter_asset_correlations):
        num_assets = len(self.asset_factor_map.keys())
        num_correlations = num_assets * (num_assets - 1) / 2
        correlation_dict = {}
        for asset_pair in inter_asset_correlations.keys():
            asset_pair_set = frozenset(asset_pair)
            if len(asset_pair_set) != 2 or not asset_pair_set.issubset(self.asset_factor_map.keys()):
                raise VolCorrCalibrationError("inter_asset_correlations with unknown key {}".format(asset_pair))
            value = np.array(inter_asset_correlations[asset_pair])
            if value.ndim != 2:
                raise VolCorrCalibrationError("inter-asset correlation matrix is not 2 dimensional: {}"
                                              .format(inter_asset_correlations[asset_pair]))
            correlation_dict[asset_pair] = value
        if len(correlation_dict.keys()) != num_correlations:
            raise VolCorrCalibrationError("not enough inter-asset correlations provided: given {}, expected {}"
                                          .format(len(correlation_dict.keys()), num_correlations))
        return correlation_dict

    def _correlation_matrix(self, single_asset_calibrations, inter_asset_correlations):
        matrix = np.zeros((self.factor_count, self.factor_count))
        assets = sorted(single_asset_calibrations.keys())
        for x, asset1 in enumerate(assets):
            x_map = self.asset_factor_map[asset1]
            matrix[x_map[0]:x_map[1], x_map[0]:x_map[1]] = single_asset_calibrations[asset1].rho_matrix
            for asset2 in assets[x+1:]:
                y_map = self.asset_factor_map[asset2]
                if (asset1, asset2) in inter_asset_correlations.keys():
                    key = (asset1, asset2)
                    matrix[x_map[0]:x_map[1], y_map[0]:y_map[1]] = inter_asset_correlations[key]
                    matrix[y_map[0]:y_map[1], x_map[0]:x_map[1]] = inter_asset_correlations[key].transpose()
                elif (asset2, asset1) in inter_asset_correlations.keys():
                    key = (asset2, asset1)
                    matrix[x_map[0]:x_map[1], y_map[0]:y_map[1]] = inter_asset_correlations[key].transpose()
                    matrix[y_map[0]:y_map[1], x_map[0]:x_map[1]] = inter_asset_correlations[key]
                else:
                    raise VolCorrCalibrationError("could not find inter_asset_correlation between {} and {}"
                                                  .format(asset1, asset2))
        return matrix

    def sigma(self, asset, factor):
        return self.factors[self.asset_factor_map[asset][0] + factor].sigma

    def alpha(self, asset, factor):
        return self.factors[self.asset_factor_map[asset][0] + factor].alpha

    def rho(self, asset1, factor1, asset2, factor2):
        asset1_loc = self.asset_factor_map[asset1][0] + factor1
        asset2_loc = self.asset_factor_map[asset2][0] + factor2
        return self.rho_matrix[asset1_loc, asset2_loc]