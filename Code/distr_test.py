import scipy.stats as stat
import numpy
import random


for i in range (1, 25):
    print int(1000 * numpy.random.weibull(1.05)), int(random.expovariate(0.001))
    
