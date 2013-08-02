import numpy as np
import pylab

"""
We use the Mean-reverting jump diffusion model (formula 4 - see comments)

As inputs we use:
- starting S - config value - 120 EUR/MWh
- k -  for now use a uniform value - is a config value and set it to 1
- theta -  config value - 0,3 EUR/h
-  sigma -  for now use a uniform value - is a config value and set it to 0,1
- J use the values in table 2 - see comments
- dq - is a possion process - use lambda from table 2

Calculate the values for 30 year 10 times and display the values on a graph. If correct should look more or less like the picture attached below.
"""

def calc_J():
    """Calcultation of J as random with mean=loc and std=scale"""
    return  np.random.normal(loc=130, scale=11)  #loc means - mean, scale -std

S0 = 120  #EUR/MWh
k = 1
theta = 4.5  #EUR/h
Lambda = 24
sigma = 0
y = 0.1  #is the annual escalation factor
delta_q = 0.5  #random variable with Poisson distribution with lambda 24.26
#J = calc_J()
T = 3     #years
dt = 1.0 / 365  #1day
N = int(round(T/dt))  #number of periods

def poisson_distribution_value(lam=Lambda, size=None):
    """return  Poisson disribution with @lam
    if size is None - return 1 value (numerical)
    otherwise return list with values with length = size
    """
    return  np.random.poisson(lam, size)

def delta_poisson_distribution(lam=Lambda):
    """return  delta between 2 values from poisson distribution with defined @lam"""
    return  np.diff(poisson_distribution_value(lam, 2))[0]

def delta_brownian():
    """Calculated delta betw    een 2 values with normal distribution"""
    two_randoms = np.random.standard_normal(size = 2)
    return  (two_randoms[1] - two_randoms[0])

def calc_price_delta(prev_price):
    """Calculated delta price based on @prev_price"""
    delta_Z = delta_brownian()
    J = calc_J()

    #delta_q = poisson_distribution_value()
    #delta_q = delta_poisson_distribution()

    delta_price = k * (theta * 24* (1 + y)- prev_price) * dt + sigma * delta_Z + (J - prev_price) * delta_q
    return  delta_price

def calc_price_for_period(prev_price):
    """Calculate price for whole period"""
    result = []
    for i in range(N):
        price = prev_price + calc_price_delta(prev_price)
        prev_price = price
        result.append(price)
    return  result

price = calc_price_for_period(S0)
pylab.plot(price)
pylab.show()
