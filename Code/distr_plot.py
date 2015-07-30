import scipy.stats as stat
import numpy as np
from matplotlib import pyplot as plt

"""x = np.linspace(-1, 3000, 5000)
#y = stat.norm.pdf(x)
y = stat.exponweib.pdf(x, 1.74, 500)

plt.plot(x, y, linewidth=2)
#plt.xlim(-3, 3)
#plt.ylim(-0.2, 0.7)
plt.show()

"""
from scipy.stats import exponweib

fig, ax = plt.subplots(1, 1)
a, c = 0.001, 1.75
mean, var, skew, kurt = exponweib.stats(a, c, moments='mvsk')
x = np.linspace(exponweib.ppf(0.01, a, c),
                exponweib.ppf(0.99, a, c), 100)
ax.plot(x, exponweib.pdf(x, a, c),
        'r-', lw=5, alpha=0.6, label='exponweib pdf')

plt.show()
