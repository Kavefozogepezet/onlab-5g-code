
import matplotlib.pyplot as plot
from operations import *
from network import NetworkData

if __name__ == '__main__':
    net = NetworkData.load('test', force_init=True)

    op = SimplePathLoss(fr_band=(24,40)) & SimpleConnectionFilter(min_snr=0)
    op.execute(net)

    net.save('test')

    print(net.ues)
    print(net.gnbs)
    print(net.conns.to_string())

    for index, row in net.conns.iterrows():
        x1, y1 = row['x_ue'], row['y_ue']
        x2, y2 = row['x_gnb'], row['y_gnb']
        plot.plot([x1, x2], [y1, y2], color='blue', zorder=-10)

    plot.scatter(net.ues['x'], net.ues['y'], label='UEs')
    plot.scatter(net.gnbs['x'], net.gnbs['y'], label='gNBs')
    plot.xlim(0, net.channel.area[0])
    plot.ylim(0, net.channel.area[1])
    plot.gca().set_aspect('equal', adjustable='box')
    plot.show()
