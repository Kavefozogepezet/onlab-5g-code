
def single_error_demand(k):
    return k / (k - 1)


def two_error_demand(k):
    return (k - 1) / (k - 2)


if __name__ == '__main__':
    import numpy as np
    from matplotlib import pyplot as plt
    import utils.plotutils as pu

    k1 = np.linspace(2, 8, 40)
    k2 = np.linspace(3, 8, 40)

    d1 = single_error_demand(k1)
    d2 = two_error_demand(k2)
    d2pd1 = two_error_demand(k2) / single_error_demand(k2)

    plt.rcParams.update({'font.size': 9})
    fig, ax = plt.subplots()
    ax.plot(k1, d1, label='$D_1/D$')
    ax.plot(k2, d2, label='$D_2/D$')
    ax.plot(k2, d2pd1, label='$D_2/D_1$')
    ax.set_yticks([1, 1.05, 1.1, 1.2, 1.4, 1.6, 1.8, 2])
    ax.set_xticks([2, 3, 4, 5, 6, 7, 8])
    ax.set_xlabel('Kapcsolatok száma')
    ax.set_ylabel('Adatfolyam igények aránya')
    legend = ax.legend()
    pu.styled_legend(legend)
    ax.grid()

    size = fig.get_size_inches()
    size[0] *= 2/3.5
    fig.set_size_inches(size)

    pu.export_plot(fig, 'demand_ratio.pgf', 2)