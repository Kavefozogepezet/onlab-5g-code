
import pandas as pd
from io import StringIO
import configparser
from dataclasses import dataclass


class Tables:
    UE = 'ue'
    B = 'gnbs'
    CONN = 'conns'


class Cols:
    ID = 'id'
    UEID = 'id_ue'
    BID = 'if_gnb'
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


@dataclass
class Channel:
    noise: float
    area: tuple[int, int]
    bandwidth: tuple[float, float]


    def to_ini(self):
        config = configparser.ConfigParser()
        config['channel'] = {
            'noise': str(self.noise),
            'area': f'{self.area[0]}x{self.area[1]}',
            'bandwidth': f'{self.bandwidth[0]}-{self.bandwidth[1]}'
        }
        with StringIO() as strio:
            config.write(strio)
            strio.seek(0)
            return strio.read()


@dataclass
class NetworkData:
    ues = pd.DataFrame()
    gnbs = pd.DataFrame()
    conns = pd.DataFrame()
    channel = Channel(0, (0, 0), (0, 0))

