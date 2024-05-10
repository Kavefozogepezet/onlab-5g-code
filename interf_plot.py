from model.operations import *
from model.savenet import *
from model.connop import *
from model.optimize import *
from model.network import NetworkData
from model.interference import PlotInterferenceApprox


if __name__ == '__main__':
    net = NetworkData()
    op = (
        Load('data/test', force_init=True) &
        DistanceCalc() &
        FreeSpacePathloss() &
        CalcMaxSnr() &
        MinSnrFilter() &
        PlotInterferenceApprox()
    )
    op.execute(net)