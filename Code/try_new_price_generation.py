import numpy as np
import pylab

"""
We use the Mean-reverting jump diffusion model (formula 4 - see comments)

As inputs we use:
- starting S - config value - 120 EUR/MWh
 - k -  for now use a uniform value - is a config value and set it to 1
- theta -  config value - 0,3 EUR/h
- lambda - config value - 0,02
-  sigma -  for now use a uniform value - is a config value and set it to 0,1
- J use the values in table 2 - see comments
- dq - is a possion process - use lambda from table 2

Calculate the values for 30 year 10 times and display the values on a graph. If correct should look more or less like the picture attached below.
"""
S0 = 120  #EUR/MWh
k = 1
theta = 0.3  #EUR/h
sigma = 0.1
y = 0.02  #is the annual escalation factor
J =  154.85# mu from table 2
delta_q = 24.26  #lambda from table 2
T = 30 * 365 * 24 # 30 years* 365 days * 24 hours
dt = 1  #1hour
N = int(round(T/dt))  # = 262800 number of periods

def delta_brownian():
    """Calculated normal distribution value"""
    return  np.sqrt(dt) *(np.random.standard_normal() - np.random.standard_normal() )

def calc_price_delta(prev_price):
    """Calculated delta price based on @prev_price"""
    delta_Z = delta_brownian()
    delta_price = k * (theta * (1 + y) - prev_price ) * dt + sigma * delta_Z + (J - prev_price) * delta_q
    return  delta_price

def calc_price_for_period(prev_price):
    """Calculate delta price for whole period"""
    result = []
    for i in range(N):
        price_delta = calc_price_delta(prev_price)
        prev_price = price + price_delta
        result.append(prev_price)
    return  result

def calc_price_based_on_brownean(prev_price, brownian):
    result = []
    for delta_z in brownian:
        delta_price = k * (theta * (1 + y) - prev_price ) * dt + sigma * delta_z + (J - prev_price) * delta_q
        prev_price = prev_price + delta_price
        result.append(prev_price)
    return  result


print calc_price_based_on_brownean(120, [-2.55, 2.42, 1.73, -0.47, -1.38, 0.77, 1.44, -2.01])

#price = calc_price_for_period(S0)
#print price[:100]
#pylab.plot(price)
#pylab.show()