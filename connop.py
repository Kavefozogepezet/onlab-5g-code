from operations import *
import numpy as np
from network import Tables, Cols


class DistanceCalc(Operation):
    @requires(Tables.CONN, Cols.UEX, Cols.UEY, Cols.BX, Cols.BY)
    def execute(self, net: NetworkData) -> None:
        conns = net.conns
        x2 = (conns[Cols.UEX] - conns[Cols.BX]) ** 2
        y2 = (conns[Cols.UEY] - conns[Cols.BY]) ** 2
        conns[Cols.DST] = np.sqrt(x2 + y2)


class FreeSpacePathloss(Operation):
    def __init__(self, clip: float = 0.1):
        self.clip = clip


    @requires(Tables.CONN, Cols.DST)
    def execute(self, net: NetworkData) -> None:
        fr = (net.channel.bandwidth[0] + net.channel.bandwidth[1]) / 2
        dst = np.maximum(net.conns[Cols.DST], self.clip)
        net.conns[Cols.PL] = 20 * (
            np.log10(dst) +
            np.log10(fr*10e9) +
            np.log10(4 * np.pi / 3e8)
        )


class DistanceWeight(Operation):
    def __init__(self, constant: float):
        self.constant = constant
    

    @requires(Tables.CONN, Cols.DST)
    def execute(self, net: NetworkData) -> None:
        net.conns[Cols.WEIGHT] = net.conns[Cols.DST] + self.constant


class SimpleConnectionFilter(Operation):
    def __init__(self, min_snr: float):
        self.min_snr = min_snr


    @requires(Tables.CONN, Cols.MAX_POW, Cols.PL)
    def execute(self, net: NetworkData) -> None:
        conns = net.conns
        filter = conns[Cols.MAX_POW] - conns[Cols.PL] - net.channel.noise > self.min_snr
        net.conns = conns[filter]


class MinSnrFilterFilter(Operation):
    @requires(Tables.CONN, Cols.MAX_POW, Cols.PL, Cols.UEID, Cols.BID)
    @requires(Tables.UE, Cols.GAIN)
    @requires(Tables.B, Cols.GAIN)
    def execute(self, net: NetworkData) -> None:
        conns = net.conns
        conns_gain = (conns[[Cols.UEID, Cols.BID]]
            .merge(net.ues[[Cols.ID, Cols.GAIN]], left_on=Cols.UEID, right_on=Cols.ID, how='inner')
            .drop(columns=Cols.ID)
            .merge(net.gnbs[[Cols.ID, Cols.GAIN]], left_on=Cols.BID, right_on=Cols.ID, how='inner', suffixes=(None, '_2'))
            .drop(columns=Cols.ID)
        )
        print(conns_gain)

        net.conns['filter'] = (
            conns[Cols.MAX_POW] - conns[Cols.PL] - net.channel.noise
            + conns_gain[Cols.GAIN] + conns_gain['gain_2'] > net.mcst.min_snr)
