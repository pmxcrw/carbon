from inputs.static_data.time_constants import DAYS_PER_YEAR

from copy import deepcopy
import numpy as np
import math

class SimulationContext(object):

    """Contains the context for simulations"""

    def __init__(self, vol_corr_calibration, path_count, seed):
        self.vol_corr_calibration = vol_corr_calibration
        self.path_count = int(path_count)
        self.seed = seed
        self.random_state = np.random.RandomState(seed)
        self.simulated_factors = [self.vol_corr.factors(underlying)
                                  for underlying in self.vol_corr.simulated_underlyings]
