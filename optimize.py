
from operations import *
from dataclasses import dataclass
from network import *
from docplex.mp.model import Model
import numpy as np
import approx


class Optimize(Operation):
    def __init__(self, safety_level:int=0, ensure_safety:bool=True):
        self.safety_level = safety_level
        self.ensure_safety = ensure_safety


    @requires(Tables.CONN, Cols.UEID, Cols.BID, Cols.DEMAND, Cols.PL, Cols.WEIGHT)
    @requires(Tables.UE, Cols.GAIN, Cols.MAX_POW)
    @requires(Tables.B, Cols.GAIN)
    def execute(self, net: NetworkData) -> None:
        # TODO MODEL PARAMETERS MOVE TO CTOR
        alpha = 0.1 # 
        rho = 1 # energy factor
        err = 0.01 # error factor

        # tables
        conns = net.conns
        fconns = conns[conns['filter']] if 'filter' in conns.columns else conns
        

        self.model = Model('5g_network')

        # constants
        BW = net.channel.bandwidth
        BW = BW[1] - BW[0]


        # decision variables
        Bm = self.model.continuous_var_matrix(fconns.index, net.mcst.levels, 0, BW)
        b = self.model.binary_var_matrix(fconns.index, net.mcst.levels)
        x = self.model.continuous_var_dict(fconns.index, 0)
        y = self.model.continuous_var_dict(fconns.index, 0)

        # derived variables

        ## bandwidth of connections
        B = {
            i: self.model.sum([Bm[i, j] for j in range(net.mcst.levels) ])
            for i in fconns.index
        }

        ## signal to noise
        snr = {
            i: self.model.sum([
                b[i, m] * net.mcst[m][0]
                for m in range(net.mcst.levels)
            ]) for i in fconns.index
        }

        ## capacity of connections
        c = {
            i: self.model.sum([
                Bm[i, m] * net.mcst[m][1]
                for m in range(net.mcst.levels)
            ]) for i in fconns.index
        }

        ## noise and interference
        NI = {
            i: 0 for i in fconns.index
        } # TODO

        ## Signal power
        S = {
            i: snr[i] + NI[i] + row[Cols.PL]
            - net.ues.loc[row[Cols.UEID]][Cols.GAIN]
            - net.gnbs.loc[row[Cols.BID]][Cols.GAIN]
            for i, row in fconns.iterrows()
        }

        # constraints

        for i, row in fconns.iterrows():
            ## power is less than maximum
            self.model.add_constraint(S[i] <= row[Cols.MAX_POW])

            ## only one mcs is selected per connection
            self.model.add_constraint(self.model.sum([
                b[i, m] for m in range(net.mcst.levels)
            ]) == 1)

            ## only selected mcs is used
            for m in range(net.mcst.levels):
                self.model.add_constraint(Bm[i, m] <= BW * b[i, m])

            ## total traffic is less than capacity
            self.model.add_constraint(x[i] + y[i] <= c[i])

        for u, row in net.ues.iterrows():
            ## total bandwidth of a UE is less than BW
            u_conns = fconns[fconns[Cols.UEID] == u]
            self.model.add_constraint(self.model.sum([
                B[i] for i in u_conns.index
            ]) <= BW)

            ## traffic demand of UE is satisfied
            self.model.add_constraint(self.model.sum([
                x[i] for i in u_conns.index
            ]) >= row[Cols.DEMAND])

            ## TODO lazy constraints
            ## single protection
            '''
            for e1 in u_conns.index:
                self.model.add_constraint([
                    self.model.sum([
                        y[e] for e in u_conns.index if e != e1
                    ]) >= x[e1]
                ])
            '''

            ## double protection
            for e1 in u_conns.index:
                for e2 in u_conns.index:
                    if e1 == e2: continue
                    self.model.add_constraint(
                        self.model.sum([
                            y[e] for e in u_conns.index if e != e1 and e != e2
                        ]) >= x[e1] + x[e2]
                    )

        for b in net.gnbs.index:
            ## total bandwidth of a gNB is less than BW
            b_conns = fconns[fconns[Cols.BID] == b]
            self.model.add_constraint(self.model.sum([
                B[i] for i in b_conns.index
            ]) <= BW)
            
        # objective
            
        self.model.minimize(
            self.model.sum([
                row[Cols.WEIGHT] * (x[i] + alpha * y[i]) + rho * S[i]
                for i, row in fconns.iterrows()
            ])
        )

        self.model.solve()

        # Access the solution

        self.model.end()

    
    def get_approximations(self):
        lin2db = approx.lin2db(0.01, 10000)
        db2lin = approx.db2lin(40, 40)

        return (
            self.model.piecewise(0, lin2db, 0, name='lin2db'), # TODO slopes
            self.model.piecewise(0, db2lin, 0, name='db2lin') # TODO slopes
        )
