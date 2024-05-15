
def single_error(A, k):
    return A**k + k * (1 - A) * A**(k-1)


def two_errors(A, k):
    return single_error(A, k) + k * (k - 1) * (1 - A)**2 * A**(k-2) / 2


def max_connections(func, k):
    eq = lambda A: func(A, k) - A
    root = fsolve(eq, 0.8, factor=0.2)[0]
    return root


if __name__ == '__main__':
    from matplotlib import pyplot as plt
    from scipy.optimize import fsolve
    import numpy as np
    import utils.plotutils as pu

    k1l = np.arange(5, 13)
    k2l = np.arange(9, 15)
    A1 = np.array(
        [max_connections(single_error, k) for k in k1l]
    )
    A2 = np.array(
        [max_connections(two_errors, k) for k in k2l]
    )

    A = 0.9
    k1 = np.linspace(2, 7, 20)
    k2 = np.linspace(3, 13, 20)

    e1 = single_error(A, k1)
    e2 = two_errors(A, k2)

    plt.rcParams.update({'font.size': 9})
    fig, ax = plt.subplots()
    ax.plot(k1, e1, label='$A_1$')
    ax.plot(k2, e2, label='$A_2$')
    ax.plot(k1l, A1, marker='D', markersize=5, linestyle='--', label='$\\mathcal{L}_1$')
    ax.plot(k2l, A2, marker='D', markersize=5, linestyle='--', label='$\\mathcal{L}_2$')
    ax.set_xlabel('Kapcsolatok száma')
    ax.set_ylabel('Rendelkezésre állás')
    ax.set_yticks(np.linspace(0.84, 1, 9))
    legend = ax.legend()
    pu.styled_legend(legend)
    ax.grid()
    pu.export_plot(fig, 'availability.pgf', 3.5)
