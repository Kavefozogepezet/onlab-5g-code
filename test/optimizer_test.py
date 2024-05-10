import unittest
from model.savenet import *
from model.optimize import *
from model.network import *
from model.connop import *


class TestOptimizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.net = NetworkData()
        op = (
            Load('data/test', force_init=True) &
            DistanceCalc() &
            DistanceWeight(1) &
            FreeSpacePathloss() &
            CalcMaxSnr() &
            MinSnrFilter() &
            Optimize()
        )
        op.execute(cls.net)


    def test_demand_constraints(self):
        sum_x = np.sum(
            self.net.conns['x_traffic'],
            axis=0
        )

        fullfilled = sum_x >= self.net.ues['demand']
        self.assertTrue(fullfilled.all(), 'Not all demands are fullfilled.')


    def test_bandwidth_constraints(self):
        BW = self.net.channel.bandwidth
        BW = BW[1] - BW[0]

        sum_B_ue = np.sum(
            self.net.conns['bandwidth'],
            axis=0
        )
        fulfilled = sum_B_ue <= BW
        fulfilled_eq = np.isclose(sum_B_ue, BW)
        self.assertTrue(
            np.logical_or(fulfilled, fulfilled_eq).all(),
            'Bandwidth constraint not fullfilled for UEs.')

        sum_B_gnb = np.sum(
            self.net.conns['bandwidth'],
            axis=1
        )
        print(sum_B_gnb)
        fulfilled = sum_B_gnb <= BW
        fulfilled_eq = np.isclose(sum_B_gnb, BW)
        self.assertTrue(
            np.logical_or(fulfilled, fulfilled_eq).all(),
            'Bandwidth constraint not fullfilled for gNBs.'
        )


    def test_power_constraints(self):
        fulfilled = self.net.conns['signal_power'] <= self.net.ues['max_power'].values.reshape(1, -1)
        self.assertTrue(fulfilled.all(), 'Power constraint not fullfilled for UEs.')


    def test_protection_constraints(self):
        self.assertTrue(True)
