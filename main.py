import matplotlib.pyplot as plot
from model.operations import *
from model.savenet import *
from model.connop import *
from model.optimize import *
from model.network import NetworkData
from model.interference import PlotInterferenceApprox

class PrintSnr(Operation):
    @requires(Tables.CONN, Cols.MAX_POW, Cols.PL)
    def execute(self, net: NetworkData) -> None:
        conns = net.conns[net.conns['filter']]
        snr = conns[Cols.MAX_POW] - conns[Cols.PL] - net.channel.noise
        print(snr)

if __name__ == '__main__':
    net = NetworkData()

    op = (
        Load('data/test', force_init=True) &
        DistanceCalc() &
        DistanceWeight(1) &
        FreeSpacePathloss() &
        CalcMaxSnr() &
        MinSnrFilter() &
        Optimize()
    )
    op.execute(net)

    BW = net.channel.bandwidth[1] - net.channel.bandwidth[0]
    mcst = MCSTable()
    print(f'Max data rate is {BW * mcst[-1][1]} at snr {mcst[-1].snr}')
    '''
    snr = net.conns['max_snr']
    for b, u in zip(*np.where(net.conns['max_snr'] > net.mcst[0].snr)):
        print(f'Connection {u} -> {b} has snr {snr[b, u]}')
        x1 = net.ues['x'].values[u]
        y1 = net.ues['y'].values[u]
        x2 = net.gnbs['x'].values[b]
        y2 = net.gnbs['y'].values[b]
        plot.plot([x1, x2], [y1, y2])
    '''

    mcs = net.conns['mcs_idx'].flatten()
    filter = net.conns['filter'].flatten()
    mcs = mcs[filter]
    plot.hist(mcs)
    plot.show()


    plot.scatter(net.ues['x'], net.ues['y'], label='UEs')
    plot.scatter(net.gnbs['x'], net.gnbs['y'], label='gNBs')
    plot.xlim(0, net.channel.area[0])
    plot.ylim(0, net.channel.area[1])
    plot.gca().set_aspect('equal', adjustable='box')
    plot.show()
    
