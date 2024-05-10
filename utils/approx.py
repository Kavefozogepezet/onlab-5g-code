
from scipy.optimize import bisect
import numpy as np


def approx(fun, derivative, a, b, err, convex=True):
    fn = fun if convex else lambda x: -fun(x)
    dfn = derivative if convex else lambda x: -derivative(x)

    neg = 1 if convex else -1

    segments = [(a, neg*(fn(a)-err))]
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
        segments.append((a, neg*(fn(a)-err)))

    segments.append((b, neg*fn(b)))
    return segments


def adaptive_approx(fun, derivative, bounds: list[float], errp=0.01, convex=True):
    points = []
    for i, a in enumerate(bounds[:-1]):
        b = bounds[i+1]
        err = errp*fun(a)
        points += approx(fun, derivative, a, b, err, convex)[:-1]
    points.append((bounds[-1], fun(bounds[-1])))
    return points


def lin2db(a, b, err=0.01):
    fn = lambda x: 10 * np.log10(x)
    dfn = lambda x: 10 / (x * np.log(10))

    x = np.linspace(a, b, 10000)
    return dfn(a), approx(fn, dfn, a, b, err, False), dfn(b)


def db2lin(a, b, **kwargs):
    fn = lambda x: 10**(x/10)
    dfn = lambda x: np.log(10) * 10**(x/10 - 1)
    points = None

    if 'errp' in kwargs:
        errp = kwargs['errp']
        # 
        bound1 =  int(np.ceil(a/10)) * 10
        boundk_1 = int(np.floor(b/10)) * 10
        bounds = list(range(bound1, boundk_1+1, 10))
        if bound1 != a: bounds.insert(0, a)
        if boundk_1 != b: bounds.append(b)
        points = adaptive_approx(fn, dfn, bounds, errp, True)
    else:
        err = kwargs.get('err', 0.01)
        points = approx(fn, dfn, a, b, err, True)

    return dfn(a), points, dfn(b)


if __name__ == '__main__':
    from matplotlib import pyplot as plt
    import utils.plotutils as pu

    fig, ax = plt.subplots()

    _, dlp, _ = db2lin(-10, 10, errp=0.05)
    dlx = np.linspace(-10, 10, 10000)
    dly = 10**(dlx/10)

    ax.plot(dlx, dly, label='function', linestyle='dashed', linewidth=1)
    ax.plot([x for x, _ in dlp], [y for _, y in dlp], label='approximation', linewidth=1)

    ax.set_ylim(0, 3)
    ax.set_xlim(-5, 5)
    ax.axvline(0, color='black', linestyle='dotted', linewidth=1)

    ax.set_xlabel('dBm')
    ax.set_ylabel('mW')

    pu.styled_legend(ax)
    pu.export_plot(fig, 'data/db2lin.pgf', 3)
    plt.clf()

    fig, ax = plt.subplots()

    _, ldp, _ = lin2db(0.01, 40, 0.5)
    ldx = np.linspace(0.01, 40, 100)
    ldy = 10*np.log10(ldx)

    ax.plot(ldx, ldy, label='function', linestyle='dashed', linewidth=1)
    ax.plot([x for x, _ in ldp], [y for _, y in ldp], label='approximation', linewidth=1)

    print(len(ldp))

    #ax.set_ylim(-20, 40)
    #ax.set_xlim(0, 10000)

    ax.set_xlabel('mW')
    ax.set_ylabel('dBm')

    pu.styled_legend(ax)
    pu.export_plot(fig, 'data/lin2db.png', 10)
    plt.clf()
