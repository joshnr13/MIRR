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
    return  np.random.normal(loc=155, scale=81)  #loc means - mean, scale -std

S0 = 120  #EUR/MWh
k = 1
theta = 0.03  #EUR/h
Lambda = 0.02
sigma = 0.01
y = 0  #is the annual escalation factor
delta_q = 24.26  #lambda from table 2
#J = calc_J()
T = 3     #years
dt = 1.0 / 365  #1day
N = int(round(T/dt))  #number of periods



def delta_brownian():
    """Calculated delta betw    een 2 values with normal distribution"""
    two_randoms = np.random.standard_normal(size = 2)
    return  np.sqrt(dt) * (two_randoms[1] - two_randoms[0])

def calc_price_delta(prev_price):
    """Calculated delta price based on @prev_price"""
    delta_Z = delta_brownian()
    J = calc_J()
    #"""delta_price = k * (theta * 24* (1 + y) ) * dt - prev_price + sigma * delta_Z + (J - prev_price) * delta_q"""
    delta_price = sigma * delta_Z + (J - prev_price) * delta_q
    return  delta_price

def calc_price_for_period(prev_price):
    """Calculate delta price for whole period"""
    result = []
    for i in range(N):
        price = prev_price + calc_price_delta(prev_price)
        prev_price = price
        result.append(price)
    return  result

price = calc_price_for_period(S0)
pylab.plot(price)
pylab.show()
