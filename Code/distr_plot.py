import scipy.stats as stat
import numpy as np
from matplotlib import pyplot as plt

x = np.linspace(-3, 3, 50)
y = stat.norm.pdf(x)

plt.plot(x, y, linewidth=2)
plt.xlim(-3, 3)
plt.ylim(-0.2, 0.7)
plt.show()
