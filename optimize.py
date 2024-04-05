
from operations import Operation
from dataclasses import dataclass
from network import NetworkData
from docplex.mp.model import Model
import numpy as np
from network import Cols


@dataclass
class MCSTable:
    levels: int = 8
    min_snr: float = -5
    spacing: float = 2
    efficiency: float = 0.9


    def __getitem__(self, level):
        snr = self.min_snr + level * self.spacing
        eff = np.log2(1 + 10**(snr/10)) * self.efficiency
        return (snr, eff)


class Optimize(Operation):
    def __init__(self, safety_level:int=0, ensure_safety:bool=True, mcs_table:MCSTable=MCSTable()):
        self.safety_level = safety_level
        self.ensure_safety = ensure_safety
        self.mcst = mcs_table

    def execute(self, net: NetworkData) -> None:
        model = Model('5g network')

        # important constants
        BW = net.channel.bandwidth
        BW = BW[1] - BW[0]


        # decision variables
        Bm = model.continuous_var_matrix(net.conns.index, self.mcst.levels, 0, BW)
        b = model.binary_var_matrix(net.conns.index, self.mcst.levels)
        x = model.continuous_var_dict(net.conns.index, 0)
        y = model.continuous_var_dict(net.conns.index, 0)

        # derived variables

        ## bandwidth of connections
        B = {
            i: model.sum([Bm[i, j] for j in range(self.mcst.levels) ])
            for i in net.conns.index
        }

        ## signal to noise
        snr = {
            i: model.sum([
                b[i, m] * self.mcst[m][0]
                for m in range(self.mcst.levels)
            ]) for i in net.conns.index
        }

        ## capacity of connections
        c = {
            i: model.sum([
                Bm[i, m] * self.mcst[m][1]
                for m in range(self.mcst.levels)
            ]) for i in net.conns.index
        }

        ## interference
        I = {
            i: 0 for i in net.conns.index
        } # TODO

        ## Signal power
        S = {
            i: snr[i] + I[i] + row[Cols.PL] # TODO gain
            for i, row in net.conns.iterrows()
        }

        # constraints

        ## power is less than maximum
        for i, row in net.conns.iterrows():
            model.add_constraint(S[i] <= row[Cols.MAX_POW])

        ## only one mcs is used per connection
        for i in net.conns.index:
            model.add_constraint(model.sum([
                b[i, m] for m in range(self.mcst.levels)
            ]) == 1)

        ## total bandwidth of UE and gNB is less than BW
        for u in net.ues['id']:
            u_conns = net.conns[net.conns['id_ue'] == u]
            model.add_constraint(model.sum([
                B[i] for i in u_conns.index
            ]) <= BW)

        for b in net.gnbs['id']:
            b_conns = net.conns[net.conns['id_gnb'] == b]
            model.add_constraint(model.sum([
                B[i] for i in b_conns.index
            ]) <= BW)

        ## total traffic is less than capacity
        for i in net.conns.index:
            model.add_constraint(x[i] + y[i] <= c[i])

        ## traffic demand of UE is satisfied
        for u, D in net.ues[Cols.ID, Cols.DEMAND]:
            print(u)
            u_conns = net.conns[net.conns['id_ue'] == u]
            model.add_constraint(model.sum([
                x[i] for i in u_conns.index
            ]) >= D)

        ## TODO protection constraints
            
        # objective
            
        rho = 1 # TODO energy factor
            
        model.minimize(
            model.sum([
                row[Cols.WEIGHT] * (x[i] + y[i]) + rho * S[i]
                for i, row in net.conns.interrows()
            ])
        )

        model.solve()

        # Access the solution

        model.end()