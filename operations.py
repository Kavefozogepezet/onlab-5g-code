
from network import NetworkData
import numpy as np
import math


class Operation:
    def execute(self, net: NetworkData) -> None:
        raise NotImplementedError('execute() must be implemented by operation')
    

    def __and__(self, other):
        if issubclass(type(other), Operation):
            return OpSequence(self, other)
        elif issubclass(type(other), OpSequence):
            return other & self
        else:
            raise TypeError('Operation can only be combined with Operation or OpSequence')
    

class OpSequence(Operation):
    def __init__(self, *ops):
        self.ops = ops

    
    def __and__(self, other):
        if issubclass(type(other), Operation):
            return OpSequence(*self.ops, other)
        elif issubclass(type(other), OpSequence):
            return OpSequence(*self.ops, *other.ops)
        else:
            raise TypeError('OpSequence can only be combined with Operation or OpSequence')
        

    def __iand__(self, other):
        if issubclass(type(other), Operation):
            self.ops.append(other)
            return self
        elif issubclass(type(other), OpSequence):
            self.ops.extend(other.ops)
            return self
        else:
            raise TypeError('OpSequence can only be combined with Operation or OpSequence')
        

    def execute(self, net: NetworkData) -> None:
        for op in self.ops:
            op.execute(net)


class SimplePathLoss(Operation):
    def __init__(self, fr_band: tuple[float, float]):
        self.fr = (fr_band[0] + fr_band[1]) / 2


    def execute(self, net: NetworkData) -> None:
        conns = net.conns
        x2 = (conns['x_ue'] - conns['x_gnb']) ** 2
        y2 = (conns['y_ue'] - conns['y_gnb']) ** 2
        conns['dst'] = np.clip(np.sqrt(x2 + y2), 0.1, None)
        conns['pathloss'] = 20 * (
            np.log10(conns['dst']) +
            np.log10(self.fr*10e9) +
            math.log10(4 * math.pi / 3e8)
        )


class SimpleConnectionFilter(Operation):
    def __init__(self, min_snr: float):
        self.min_snr = min_snr


    def execute(self, net: NetworkData) -> None:
        conns = net.conns
        filter = conns['max_power'] - conns['pathloss'] - net.channel.noise > self.min_snr
        net.conns = conns[filter]
