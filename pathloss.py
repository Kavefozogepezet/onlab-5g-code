from operations import *
import numpy as np
from network import Tables, Cols

class FreeSpacePathloss(Operation):
    @requires(Tables.CONN, Cols.UEX, Cols.UEY, Cols.BX, Cols.BY)
    def execute(self, net: NetworkData) -> None:
        fr = (net.channel.bandwidth[0] + net.channel.bandwidth[1]) / 2
        conns = net.conns
        x2 = (conns['x_ue'] - conns['x_gnb']) ** 2
        y2 = (conns['y_ue'] - conns['y_gnb']) ** 2
        conns['dst'] = np.clip(np.sqrt(x2 + y2), 0.1, None)
        conns['pathloss'] = 20 * (
            np.log10(conns['dst']) +
            np.log10(fr*10e9) +
            np.log10(4 * np.pi / 3e8)
        )
