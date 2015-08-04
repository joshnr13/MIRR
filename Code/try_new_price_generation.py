import numpy as np
import pylab
from rm import calcStatistics

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

S0 = 70  #EUR/MWh
k = 5
theta = 70  #EUR/MWh
Lambda = 24  # Lambda for the Poisson process used for price jumps
sigma = 0.5
y = 0.02  #is the annual escalation factor
delta_q = 0.5  #random variable with Poisson distribution with lambda 24.26
#J = calc_J()
T = 10     #years
dt = 1.0 / 365  #1day
N = int(round(T/dt))  #number of periods

class Poisson_step():
    """class for holding generated Poisson values"""
    def __init__(self, lam, size):
        self.lam = lam
        self.size = size
        self.generate_values()
        self.make_step()
        self.make_function()

    def generate_values(self):
        """Generate poisson values"""
        self.vals = poisson_distribution_value(self.lam, self.size)

    def make_step(self):
        """Make step (path) from generated poisson values"""
        self.step_vals = np.cumsum(self.vals)

    def make_function(self):
        """Make function - dict
        where key in integers from x value,
        value - current iteration no, ie y value
        """
        result = {}
        x0 = 0
        for i, x in enumerate(self.step_vals):
            vals_range = xrange(x0, x)
            for k in vals_range:
                result[k] = i
            x0 = x
        self.function = result

    def get_delta(self, index):
        """return  delta between current index and previous"""
        return  self.function[index] - self.function[index-1]


def calc_J():
    """Calcultation of J as random with mean=loc and std=scale"""
    return  np.random.normal(loc=0, scale=1)  #loc means - mean, scale -std

def poisson_distribution_value(lam=Lambda, size=None):
    """return  Poisson disribution with @lam
    if size is None - return 1 value (numerical)
    otherwise return list with values with length = size
    """
    return  np.random.poisson(lam, size)

def calc_price_delta(prev_price, iteration_no):
    """Calculated delta price based on @prev_price"""
    delta_Z = np.random.normal(loc=0, scale=0.4)
    J = calc_J()

    delta_q = poisson_steps.get_delta(iteration_no)

    delta_price = k * (theta * (1 + y*iteration_no/365)- prev_price) * dt + sigma * delta_Z + (J*(1 + y*iteration_no/365)) * delta_q
    return  delta_price

def calc_price_for_period(prev_price):
    """Calculate price for whole period"""
    result = []
    for i in range(1, N+1):
        price = prev_price + calc_price_delta(prev_price, i)
        prev_price = price
        result.append(price)
    return  result

if __name__ == '__main__':

    poisson_steps = Poisson_step(Lambda, size=N)
    price = calc_price_for_period(S0)

    stats = calcStatistics(price)
    fig = pylab.figure()

    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)  # share ax1's xaxis

    stats = "; ".join(['%s=%s' % (k, round(v, 2)) for k, v in stats.items()])
    ax1.plot(price)
    ax2.hist(price, label='Electricity price histogram\n$%s$' %stats)
    # Shink current axis's height by 10% on the bottom
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

    # Put a legend below current axis
    ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
              fancybox=True, shadow=True)

    pylab.show()
    print N
