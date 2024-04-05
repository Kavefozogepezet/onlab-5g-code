
from scipy.optimize import bisect
from matplotlib import pyplot as plt
import numpy as np


def approx(fn, dfn, a, b, err):
    segments = [(a, fn(a)-err)]
    while a < b:
        G = lambda x: dfn(x)*(x-a) + fn(a) - fn(x) - 2*err
        if G(b) < 0:
            break

        root = bisect(G, a, b)
        d = dfn(root)
        c = fn(root) - d*root + err
        H = lambda x: fn(x) - d*x - c - err
        if H(b) < 0:
            break

        b2 = bisect(H, root, b)
        a = b2
        segments.append((a, fn(a)-err))

    segments.append((b, fn(b)))
    return segments

func = lambda x: np.log10(5 + 10**x)
dfunc = lambda x: 10**x / (5 + 10**x)

points = approx(func, dfunc, -2, 2, 0.01)

x = np.linspace(-2, 2, 100)
y = func(x)
plt.plot(x, y)

aprx_x = [x for x, _ in points]
aprx_y = [y for _, y in points]

plt.plot(aprx_x, aprx_y)
plt.show()
