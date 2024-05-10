from model.network import NetworkData


class RequiredColumnMissingException(Exception):
    def __init__(self, table, column, classname) -> None:
        super().__init__(
            f'Table "{table}" has no column "{column}", but operation "{classname}" requires it.') 


def requires(table: str, *columns: str):
    def requires_dec(func):
        def check_colums(self, net):
            real_cols = getattr(net, table)
            if table != 'conns':
                real_cols = real_cols.columns
            for column in columns:
                if column not in real_cols:
                    raise RequiredColumnMissingException(table, column, self.__class__.__name__)
            func(self, net)
        return check_colums
    return requires_dec


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

