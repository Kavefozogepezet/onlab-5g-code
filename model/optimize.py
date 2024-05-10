
from docplex.mp.model import Model
import numpy as np
import utils.approx as approx
import time
from model.operations import *
from model.network import *
from model.interference import InterfApproxProvider, InterfApproxData
from model.connop import ConnectionFilter


class Optimize(Operation):
    def __init__(self, safety_level:int=0, ensure_safety:bool=True):
        self.safety_level = safety_level
        self.ensure_safety = ensure_safety


    @requires(Tables.CONN, 'pathloss', 'weight')
    @requires(Tables.UE, 'demand', 'gain', 'max_power')
    @requires(Tables.B, 'gain')
    def execute(self, net: NetworkData) -> None:
        # TODO MODEL PARAMETERS MOVE TO CTOR
        alpha = 0.1 # 
        rho = 1 # energy factor

        # tables
        conns = net.conns
        fconns = ConnectionFilter(net)

        self.model = Model('5g_network', log_output=True)

        # constants
        BW = net.channel.bandwidth
        BW = BW[1] - BW[0]

        self.calc_max_interference(net, fconns)
        #self.create_approximations(BW)

        # decision variables
        Bm = self.model.continuous_var_matrix(fconns, net.mcst.levels, 0, BW)
        B = self.model.continuous_var_dict(fconns, 0, BW)
        S = self.model.continuous_var_dict(fconns)
        bm = self.model.binary_var_matrix(fconns, net.mcst.levels)
        x = self.model.continuous_var_dict(fconns, 0)
        y = self.model.continuous_var_dict(fconns, 0)

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
            e: self.model.sum([
                bm[e, m] * net.mcst[m][0]
                for m in range(net.mcst.levels)
            ]) for e in fconns
        }

        ## capacity of connections
        c = {
            e: self.model.sum([
                Bm[e, m] * net.mcst[m][1]
                for m in range(net.mcst.levels)
            ]) for e in fconns
        }

        ## noise and interference
        NI = {
            e: net.channel.noise
            #i: self.interference_for(i, row, B, S, fconns, net)
            for e in fconns
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

        u_gain = net.ues[Cols.GAIN].values
        u_pow = net.ues[Cols.MAX_POW].values
        u_demand = net.ues[Cols.DEMAND].values
        b_gain = net.gnbs[Cols.GAIN].values

        for b, u in fconns:
            e = (b, u)

            self.model.add_constraint(B[e] == self.model.sum([
                Bm[e, m] for m in range(net.mcst.levels)
            ]))

            ## constraint on calculating signal power
            self.model.add_constraint(
                S[e] >= snr[e] + NI[e] + net.conns['pathloss'][e]
                - u_gain[u] # gain of UE
                - b_gain[b] # gain of gNB
            )

            ## power is less than maximum
            self.model.add_constraint(S[e] <= u_pow[u])

            ## only one mcs is selected per connection
            self.model.add_constraint(self.model.sum([
                bm[e, m] for m in range(net.mcst.levels)
            ]) == 1)

            ## only selected mcs is used
            for m in range(net.mcst.levels):
                self.model.add_constraint(Bm[e, m] <= BW * bm[e, m])

            ## total traffic is less than capacity
            self.model.add_constraint(x[e] + y[e] <= c[e])

        for u in net.ues.index:
            u_conns = [e for e in fconns if e[1] == u]

            ## total bandwidth of a UE is less than BW
            self.model.add_constraint(self.model.sum([
                B[e] for e in u_conns
            ]) <= BW)

            ## traffic demand of UE is satisfied
            self.model.add_constraint(self.model.sum([
                x[e] for e in u_conns
            ]) >= u_demand[u])

            ## TODO lazy constraints
            ## single protection
            '''
            for e1 in u_conns.index:
                self.model.add_constraint([
                    self.model.sum([
                        y[e] for e in u_conns if e != e1
                    ]) >= x[e1]
                ])
            '''

            ## double protection
            for e1 in u_conns:
                for e2 in u_conns:
                    if e1 == e2: continue
                    self.model.add_constraint(
                        self.model.sum([
                            y[e] for e in u_conns if e != e1 and e != e2
                        ]) >= x[e1] + x[e2]
                    )

        for b in net.gnbs.index:
            b_conns = [e for e in fconns if e[0] == b]

            ## total bandwidth of a gNB is less than BW
            self.model.add_constraint(self.model.sum([
                B[e] for e in b_conns
            ]) <= BW)
            
        # objective
            
        self.model.minimize(
            self.model.sum([
                net.conns['weight'][e] * (x[e] + alpha * y[e]) + rho * S[e]
                for e in fconns
            ])
        )

        self.model.solve()

        # Access the solution

        shape = conns['weight'].shape
        net.conns['bandwidth'] = np.zeros(shape, dtype=float)
        net.conns['signal_power'] = np.zeros(shape, dtype=float)
        net.conns['x_traffic'] = np.zeros(shape, dtype=float)
        net.conns['y_traffic'] = np.zeros(shape, dtype=float)
        net.conns['mcs_idx'] = np.zeros(shape, dtype=int)

        for e in fconns:
            net.conns['bandwidth'][e] = B[e].solution_value
            net.conns['signal_power'][e] = S[e].solution_value
            net.conns['x_traffic'][e] = x[e].solution_value
            net.conns['y_traffic'][e] = y[e].solution_value
            net.conns['mcs_idx'][e] = np.argmax([bm[e, m].solution_value for m in range(net.mcst.levels)])
            if np.sum([bm[e, m].solution_value for m in range(net.mcst.levels)]) != 1:
                print(f'Error: multiple MCS selected for {e}')

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

        u_pow = net.ues['max_power'].values
        u_gain = net.ues['gain'].values
        b_gain = net.gnbs['gain'].values

        start_time = time.time()

        for e in fconns:
            b, u = e
            I = 0
            for ep in fconns:
                bp, up = ep
                eI = (b, up)
                if u == up or b == bp:
                    continue
                Idb = u_pow[up] - net.conns['pathloss'][eI] + u_gain[up] + b_gain[b]
                count += 1
                if Idb > maxIdb:
                    maxIdb = Idb
                I += 10 ** (Idb / 10)
            if I > maxImW:
                maxImW = I

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"INTERFERENCE FOR LOOP execution time: {execution_time} seconds")
        '''
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
        '''

        print(f'Max dbm2mW: {maxIdb}, mW2dBm: {maxImW}, count: {count}')
