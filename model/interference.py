import numpy as np
import matplotlib.pyplot as plot
import matplotlib.ticker as mtick
from dataclasses import dataclass
from model.connop import ConnectionFilter
from model.operations import *


@dataclass
class InterfApproxData:
    e: tuple[int, int]
    total_interferer_count: int
    selection_count: int
    ues: np.ndarray
    weights: np.ndarray

    _I: np.ndarray
    _sort_idx: np.ndarray
    _aprx_idx: np.ndarray


    def __post_init__(self):
        self.b, self.u = self.e


    def error_for(self, variations):
        randI = self._I * variations
        sum_randI = np.sum(randI)
        sum_I_aprx = np.sum(randI[self._aprx_idx] * self.weights)
        return np.abs(sum_randI - sum_I_aprx) / sum_randI
    

class InterfApproxProvider:
    def __init__(self, net, fconns) -> None:
        self.net = net
        self.fconns = fconns


    def __iter__(self):
        for e in self.fconns:
            b, u = e
            dst, I, ups = self._calc_interferences(self.net, b, u)

            sort_idx = np.argsort(dst)
            sum_I = self._calc_sum_I(I, sort_idx)
            aprx_idx, weights = self._calc_approx_weights(dst, I, sum_I, sort_idx)

            yield InterfApproxData(
                e, len(ups), len(weights),  ups[aprx_idx], weights,
                I, sort_idx, aprx_idx
            )
    

    def _calc_approx_weights(self, dst, I, sum_I, sort_idx):
        exp_range = int(np.log2(len(dst))) + 1

        delta_idx = 10
        aprx_idx = 2 ** np.arange(0, exp_range) - 1
        aprx_idx = np.concatenate(([0, 1, 2, 3], np.arange(4, len(dst), delta_idx)))
        np.random.randint(-delta_idx // 2 + 1, delta_idx // 2, len(aprx_idx) - 5)
        aprx_idx[5:] += np.random.randint(-delta_idx // 2, delta_idx // 2, len(aprx_idx) - 5)

        aprx_sort_idx = sort_idx[aprx_idx]
        weights = np.zeros_like(aprx_idx, dtype=float)
        weights[0] = 1

        for i in range(1, len(aprx_sort_idx)):
            curr = sum_I[aprx_idx[i]]
            next = sum_I[-1] if i + 1 == len(aprx_idx) else sum_I[aprx_idx[i+1]-1]
            weights[i] = 1 + (next - curr) / (I[aprx_sort_idx[i]])

        return aprx_sort_idx, weights


    def _calc_interferences(self, net, b, u):
        u_pow = net.ues['max_power'].values
        u_gain = net.ues['gain'].values
        b_gain = net.gnbs['gain'].values

        dst = np.array([], dtype=float)
        I = np.array([], dtype=float)
        ups = np.array([], dtype=int)

        for up in net.ues.index:
            if u == up:
                continue
            eI = (b, up)
            I_db = u_pow[up] - net.conns['pathloss'][eI] + u_gain[up] + b_gain[b]

            I = np.append(I, 10 ** (I_db / 10))
            dst = np.append(dst, net.conns['distance'][eI])
            ups = np.append(ups, up)

        return dst, I, ups
    

    def _calc_sum_I(self, I, sort_idx):
        I_to_sum = I[sort_idx]
        return np.cumsum(I_to_sum)


class PlotInterferenceApprox(Operation):
    @requires('conns', 'distance', 'pathloss')
    @requires('ues', 'max_power', 'gain')
    @requires('gnbs', 'gain')
    def execute(self, net):
        
        fconns = ConnectionFilter(net)
        variations = np.linspace(0.1, 1, 10)
        errs = np.zeros((len(variations), len(fconns)), dtype=float)
        
        for i, data in enumerate(InterfApproxProvider(net, fconns)):
            '''
            plot.scatter(net.ues['x'], net.ues['y'], label='UEs')
            plot.scatter(net.ues['x'][data.ues], net.ues['y'][data.ues], label='Selected UEs')
            plot.scatter(net.gnbs['x'], net.gnbs['y'], label='gNBs', marker='^')
            plot.scatter(net.gnbs['x'][data.b], net.gnbs['y'][data.b], label='the gNB', marker='^')
            plot.xlim(0, net.channel.area[0])
            plot.ylim(0, net.channel.area[1])
            plot.gca().set_aspect('equal', adjustable='box')
            plot.legend()
            plot.show()
            '''

            for j, var in enumerate(variations):
                pow_mul = 1 + np.random.rand(data.total_interferer_count) * var
                errs[j, i] = data.error_for(pow_mul)
        
        errs *= 100

        fig, ax = plot.subplots()
        ax.boxplot(errs.T, flierprops={'marker': '.', 'markerfacecolor': 'black', 'markeredgewidth': 0}, whis=2.75)
        ax.grid(axis='y')
        ax.set_xticks(range(1, len(variations) + 1), [f'{int(v*100)}%' for v in variations], rotation=45)
        ax.set_yticks(range(0, 21, 2))
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))

        ax.set_xlabel('Eszközök teljesítményének maximális eltérése (%)')
        ax.set_ylabel('Interferencia becslés hibája (%)')
        
        plot.show()

