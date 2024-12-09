import numpy as np
import matplotlib.pyplot as plt
from jinja2.optimizer import optimize
from scipy.stats import norm, uniform
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from bayes_opt import BayesianOptimization


def f_gp(mu_st, sigma_st):
    s_t = np.random.normal(mu_st, sigma_st)
    # transform s_t to a_t using the cdf of Gaussian Process
    a_t = norm.cdf(s_t, loc=mu_st, scale=sigma_st)
    return a_t


def l2NormObjective(mu_st, sigma_st):
    a_t = f_gp(mu_st, sigma_st)
    # discretize a_t using histograms
    hist_a_t, bin_edges = np.histogram(a_t, bins=32, density=True)
    # the Uniform is spread of the entirety of p_a_t
    uniform_hist = np.ones(hist_a_t) / len(hist_a_t)
    distance = np.linalg.norm(hist_a_t - uniform_hist)
    # minimizing distance is the same as maximizing the negative of distance
    return -distance


kernel = C(constant_value=1.0, constant_value_bounds=(1e-4, 1e1)) * RBF(length_scale=1.0,
                                                                        length_scale_bounds=(1e-4, 1e1))
GP = GaussianProcessRegressor(kernel=kernel, random_state=0, n_restarts_optimizer=10)

# first you need to define the bounds for which the mu_st and sigma_st can take
bounds = {'mu_st': (-5.0, 5.0), 'sigma_st': (0.1, 3.0)}
# set up the optimiser
optimiser = BayesianOptimization(
    f=l2NormObjective,
    pbounds=bounds,
    random_state=64
)

optimiser.maximize(init_points=5, n_iter=20)
