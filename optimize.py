
from operations import Operation
from dataclasses import dataclass
from network import NetworkData
import cplex


@dataclass
class MCSTable:
    levels: int = 8
    min_snr: float = -5
    spacing: float = 2
    efficiency: float = 0.9


    def __getitem__(self, level):
        return self.min_snr + level * self.factor    


class Optimize(Operation):
    def __init__(self, safety_level:int=0, ensure_safety:bool=True, mcs_table:MCSTable=MCSTable()):
        self.safety_level = safety_level
        self.ensure_safety = ensure_safety
        self.mcs_table = mcs_table

    def execute(self, net: NetworkData) -> None:
        model = cplex.Cplex()

        

        # Add variables to the model
        # ...

        # Add constraints to the model
        # ...

        # Set objective function
        # ...

        # Solve the model
        model.solve()

        # Access the solution
        # ...

        # Perform optimization based on the solution
        # ...

        # Update the network data
        # ...

        # Print the optimized network data
        # ...

        # Close the CPLEX model
        model.end()