
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

        self.model = Model('5g_network', log_output=True)

        # constants
        BW = net.channel.bandwidth
        BW = BW[1] - BW[0]

        self.calc_max_interference(net, fconns)
        self.create_approximations(BW)

        # decision variables
        Bm = self.model.continuous_var_matrix(fconns.index, net.mcst.levels, 0, BW)
        B = self.model.continuous_var_dict(fconns.index, 0, BW)
        S = self.model.continuous_var_dict(fconns.index)
        b = self.model.binary_var_matrix(fconns.index, net.mcst.levels)
        x = self.model.continuous_var_dict(fconns.index, 0)
        y = self.model.continuous_var_dict(fconns.index, 0)

        # derived variables

        '''
        ## bandwidth of connections
        B = {
            i: self.model.sum([Bm[i, j] for j in range(net.mcst.levels) ])
            for i in fconns.index
        }
        '''

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
            i: net.channel.noise
            #i: self.interference_for(i, row, B, S, fconns, net)
            for i, row in fconns.iterrows()
        }

        '''
        ## Signal power
        S = {
            i: snr[i] + NI[i] + row[Cols.PL]
            - net.ues.loc[row[Cols.UEID]][Cols.GAIN]
            - net.gnbs.loc[row[Cols.BID]][Cols.GAIN]
            for i, row in fconns.iterrows()
        }
        '''

        # constraints

        for e, row in fconns.iterrows():
            self.model.add_constraint(B[e] == self.model.sum([
                Bm[e, m] for m in range(net.mcst.levels)
            ]))

            ## constraint on calculating signal power
            self.model.add_constraint(
                S[e] >= snr[e] + NI[e] + row[Cols.PL]
                - net.ues.loc[row[Cols.UEID]][Cols.GAIN] # gain of UE
                - net.gnbs.loc[row[Cols.BID]][Cols.GAIN] # gain of gNB
            )

            ## power is less than maximum
            self.model.add_constraint(S[e] <= row[Cols.MAX_POW])

            ## only one mcs is selected per connection
            self.model.add_constraint(self.model.sum([
                b[e, m] for m in range(net.mcst.levels)
            ]) == 1)

            ## only selected mcs is used
            for m in range(net.mcst.levels):
                self.model.add_constraint(Bm[e, m] <= BW * b[e, m])

            ## total traffic is less than capacity
            self.model.add_constraint(x[e] + y[e] <= c[e])

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
                B[e] for e in b_conns.index
            ]) <= BW)
            
        # objective
            
        self.model.minimize(
            self.model.sum([
                row[Cols.WEIGHT] * (x[e] + alpha * y[e]) + rho * S[e]
                for e, row in fconns.iterrows()
            ])
        )

        self.model.solve()

        # Access the solution

        print(self.model.get_solve_status())

        self.model.end()


    def interference_for(self, e, row, B, S, fconns, net):
        Gb = net.gnbs.loc[row[Cols.BID]][Cols.GAIN]
        lgB = np.log10(net.channel.bandwidth[1] - net.channel.bandwidth[0])
        lgBe = self.Hz2dB(B[e])
        noise = 10**(net.channel.noise/10)

        Is = [
            self.dBm2mW(
                10 * (lgBe + self.Hz2dB(B[ep]) - lgB) + S[ep] - rowI[Cols.PL] +
                net.ues.loc[rowp[Cols.UEID]][Cols.GAIN] + Gb
            )

            #for eI, rowI in net.conns[net.conns[Cols.BID] == row[Cols.BID]].iterrows()
            for eI, rowI in fconns[fconns[Cols.BID] == row[Cols.BID]].iterrows()
            if row[Cols.UEID] != rowI[Cols.UEID]
            for ep, rowp in fconns[fconns[Cols.UEID] == rowI[Cols.UEID]].iterrows()
            if row[Cols.BID] != rowp[Cols.BID]
        ]

        return self.mW2dbm(noise + self.model.sum(Is))

    
    def create_approximations(self, BW):
        mW2dbm_pre, mW2dbm, mW2dbm_post = approx.lin2db(0.1, 10000, err=0.5)
        self.mW2dbm = self.model.piecewise(mW2dbm_pre, mW2dbm, mW2dbm_post, name='mW2dbm')

        dBm2mW_pre, dBm2mW, dBm2mW_post = approx.db2lin(-40, 40, errp=0.5)
        self.dBm2mW = self.model.piecewise(dBm2mW_pre, dBm2mW, dBm2mW_post, name='dBm2mW')

        Hz2dB_pre, Hz2dB, Hz2dB_post = approx.lin2db(0.1, BW, err=0.5)
        self.Hz2dB = self.model.piecewise(Hz2dB_pre, Hz2dB, Hz2dB_post, name='Hz2dB')

        print(f'Piece count: mW2dBm={len(mW2dbm)}, dBm2mW={len(dBm2mW)}, Hz2dB={len(Hz2dB)}')


    def calc_max_interference(self, net, fconns):
        maxIdb = -np.inf
        maxImW = 0
        count = 0

        print(len(fconns))
        fr = (net.channel.bandwidth[0] + net.channel.bandwidth[1]) / 2

        for e, u, b, xb, yb in zip(fconns.index, fconns['id_ue'], fconns['id_gnb'], fconns['x_gnb'], fconns['y_gnb']):
            I = 0
            for ep, up, bp, xup, yup, s in zip(fconns.index, fconns['id_ue'], fconns['id_gnb'], fconns['x_ue'], fconns['y_ue'], fconns['max_power']):
                if u == up or b == bp:
                    continue
                dst = np.sqrt((xup - xb) ** 2 + (yup - yb) ** 2)
                L = 20 * (np.log10(dst) + np.log10(fr*10e9) + np.log10(4 * np.pi / 3e8))
                Idb = s - L #+ net.ues.loc[up][Cols.GAIN] + net.gnbs.loc[b][Cols.GAIN]
                count += 1
                if Idb > maxIdb:
                    maxIdb = Idb
                I += 10 ** (Idb / 10)
            if I > maxImW:
                maxImW = I

        print(f'Max dbm2mW: {maxIdb}, mW2dBm: {maxImW}, count: {count}')
