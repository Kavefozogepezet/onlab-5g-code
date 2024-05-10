import pandas as pd
import numpy as np
from dataclasses import dataclass
from collections import namedtuple


class Tables:
    UE = 'ues'
    B = 'gnbs'
    CONN = 'conns'


class Cols:
    ID = 'id'
    UEID = 'id_ue'
    BID = 'id_gnb'
    X = 'x'
    UEX = 'x_ue'
    BX = 'x_gnb'
    Y = 'y'
    UEY = 'y_ue'
    BY = 'y_gnb'
    MAX_POW = 'max_power'
    DST = 'dst'
    PL = 'pathloss'
    DEMAND = 'demand'
    WEIGHT = 'weight'
    GAIN = 'gain'


@dataclass
class MCSTable:
    levels: int = 8
    min_snr: float = -5
    spacing: float = 2
    efficiency: float = 0.9

    def __getitem__(self, item):
        if item < -self.levels or item >= self.levels:
            raise IndexError("MCS level out of range")
        elif item < 0:
            item = self.levels + item

        snr = self.min_snr + self.spacing * item
        eff = self.efficiency * np.log2(1 + 10**(snr/10))

        MCS = namedtuple('MCS', ['snr', 'efficiency'])
        return MCS(snr, eff)


@dataclass
class Channel:
    noise: float = -100
    area: tuple[int, int] = (100, 100)
    bandwidth: tuple[float, float] = (0, 1)


@dataclass
class NetworkData:
    ues = pd.DataFrame()
    gnbs = pd.DataFrame()
    conns = dict()
    channel = Channel()
    mcst = MCSTable()
