import math

class Factor(object):

    """
    This class represents a Factor - a shift to the forward curve driven by a Brownian motion. The shift decays
    exponentially with time to delivery. Such a factor can be associated with an Ornstein-Uhlenbeck process.
    """

    def __init__(self, sigma, alpha):
        assert sigma > 0
        assert alpha >= 0
        self.sigma = sigma
        self.alpha = alpha

    # TODO - cleanup
    # def decay_correction(self, t, T):
    #     alpha = self.alpha
    #     if alpha > 0:
    #         return math.exp(-alpha * (T - t))
    #     return 1
    #
    # def duration_correction(self, D):
    #     if D > 0:
    #         return (1 - math.exp(-self.alpha * D)) / (self.alpha * D)
    #     return 1

    # TODO - cleanup
    # @staticmethod
    # def _OU_covariance(factor1, factor2, rho, t):
    #     """
    #     Helper function that calculates the covariance between the underlying OU processes associated with two Factor's
    #
    #     :param factor1: a Factor object
    #     :param factor2: another Factor object
    #     :param rho: correlation betweent the two Brownians embedded in the OU process / Factor
    #     :param t: the time the Factor's are being observed
    #     :return: the covariance between the two underlying OU processes.
    #     """
    #     total_sigma = rho * factor1.sigma * factor2.sigma
    #     total_alpha = factor1.alpha + factor2.alpha
    #     try:
    #         return total_sigma / total_alpha * (1 - math.exp(-total_alpha * t))
    #     except ZeroDivisionError:
    #         # alpha is zero for both factors
    #         return total_sigma
    #
    # @staticmethod
    # def _OU_instant_covariance(factor1, factor2, rho):
    #     """
    #     Helper function that calculates the instantaneous covariance between the OU processes associated with two
    #     Factor's.
    #
    #     :param factor1: a Factor object
    #     :param factor2: another Factor object
    #     :param rho: correlation betweent the two Brownians embedded in the OU process / Factor
    #     :return: the instantaneous covariance between the two underlying OU processes.
    #     """
    #     return rho * factor1.sigma * factor2.sigma
    #
    # @staticmethod
    # def covariance(t, rho, factor1, T1, D1=None, factor2=None, T2=None, D2=None):
    #     """
    #     Calculates the covariance between Factors
    #
    #     :param t: the observation date
    #     :param rho: the correlation between the factors
    #     :param factor1: a Factor object
    #     :param T1: the point on the forward curve being observed
    #     :param D1: optional; the duration of the delivery period being observed on the first factor
    #     :param factor2: optional; a second Factor object
    #     :param T2: optional; the point on the forward curve being observed
    #     :param D2: optional; the duration of the delivery period being observed on the first factor
    #     :return: the covariance
    #     """
    #     factor2 = factor2 if factor2 else factor1
    #     OU_covariance = Factor._OU_covariance(factor1, factor2, rho, t)
    #     return Factor._convert_OU_covariance_to_factor(OU_covariance, t, factor1, T1, D1, factor2, T2, D2)
    #
    # @staticmethod
    # def instantaneous_covariance(t, rho, factor1, T1, D1=None, factor2=None, T2=None, D2=None):
    #     """
    #     Calculates the instantaneous covariance between Factors
    #
    #     :param t: the observation date
    #     :param rho: the correlation between the factors
    #     :param factor1: a Factor object
    #     :param T1: the point on the forward curve being observed
    #     :param D1: optional; the duration of the delivery period being observed on the first factor
    #     :param factor2: optional; a second Factor object
    #     :param T2: optional; the point on the forward curve being observed
    #     :param D2: optional; the duration of the delivery period being observed on the first factor
    #     :return: the covariance
    #     """
    #     factor2 = factor2 if factor2 else factor1
    #     OU_instant_covariance = Factor._OU_instant_covariance(factor1, factor2, rho)
    #     return Factor._convert_OU_covariance_to_factor(OU_instant_covariance, t, factor1, T1, D1, factor2, T2, D2)
    #
    # @staticmethod
    # def _convert_OU_covariance_to_factor(OU_covariance, t, factor1, T1, D1=None, factor2=None, T2=None, D2=None):
    #     if T2:
    #         covariance = OU_covariance * factor1.decay_correction(t, T1) * factor2.decay_correction(t, T2)
    #     else:
    #         covariance = OU_covariance * factor1.decay_correction(t, T1) ** 2
    #     if not D1 and not D2:
    #         return covariance
    #     if D1 and not D2:
    #         return covariance * factor1.duration_correction(D1) ** 2
    #     if D2 and not D1:
    #         return covariance * factor1.duration_correction(D2) ** 2
    #     return covariance * factor1.duration_correction(D1) * factor2.duration_correction(D2)