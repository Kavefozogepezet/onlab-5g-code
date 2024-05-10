import numpy as np
from model.operations import *
from model.network import Tables


class DistanceCalc(Operation):
    @requires(Tables.UE, 'x', 'y')
    @requires(Tables.B, 'x', 'y')
    def execute(self, net: NetworkData) -> None:
        x2 = np.subtract.outer(net.gnbs['x'].values, net.ues['x'].values) ** 2
        y2 = np.subtract.outer(net.gnbs['y'].values, net.ues['y'].values) ** 2
        net.conns['distance'] = np.sqrt(x2 + y2)
        print(net.conns['distance'].shape)


class FreeSpacePathloss(Operation):
    def __init__(self, clip: float = 0.1):
        self.clip = clip


    @requires(Tables.CONN, 'distance')
    def execute(self, net: NetworkData) -> None:
        fr = (net.channel.bandwidth[0] + net.channel.bandwidth[1]) / 2
        dst = np.maximum(net.conns['distance'], self.clip)
        net.conns['pathloss'] = 20 * (
            np.log10(dst) +
            np.log10(fr*10e9) +
            np.log10(4 * np.pi / 3e8)
        )


class DistanceWeight(Operation):
    def __init__(self, constant: float):
        self.constant = constant
    

    @requires(Tables.CONN, 'distance')
    def execute(self, net: NetworkData) -> None:
        net.conns['weight'] = net.conns['distance'] + self.constant


class CalcMaxSnr(Operation):
    @requires(Tables.UE, 'max_power', 'gain')
    @requires(Tables.B, 'gain')
    @requires(Tables.CONN, 'pathloss')
    def execute(self, net: NetworkData) -> None:
        u_gain = net.ues['gain'].values
        u_pow = net.ues['max_power'].values
        print(u_gain.shape)
        b_gain = net.gnbs['gain'].values[:, None]
        print(b_gain.shape)
        net.conns['max_snr'] = u_pow - net.conns['pathloss'] + u_gain + b_gain - net.channel.noise


'''
class SimpleConnectionFilter(Operation):
    def __init__(self, min_snr: float):
        self.min_snr = min_snr


    @requires(Tables.CONN, Cols.MAX_POW, Cols.PL)
    def execute(self, net: NetworkData) -> None:
        conns = net.conns
        filter = conns[Cols.MAX_POW] - conns[Cols.PL] - net.channel.noise > self.min_snr
        net.conns = conns[filter]
'''

class MinSnrFilter(Operation):
    @requires(Tables.CONN, 'max_snr')
    def execute(self, net: NetworkData) -> None:
        net.conns['filter'] = net.conns['max_snr'] > net.mcst[0].snr


class ConnectionFilter():
    def __init__(self, net):
        if 'filter' in net.conns:
            self.bidx, self.ueidx = np.where(net.conns['filter'])
        else:
            self.bidx, self.ueidx = np.where(net.conns)

    def __iter__(self):
        return zip(self.bidx, self.ueidx)
    

    def __len__(self):
        return len(self.bidx)
