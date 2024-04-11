
from docplex.mp.model import Model

model = Model('network')

x2 = lambda x: x**2
px = lambda x: 1/x

pairs1 = [(x/1000, x2(x/1000)) for x in range(1, 2000)]
pairs2 = [(x/1000, px(x/1000)) for x in range(1, 2000)]

x = model.continuous_var(name='x', lb=0, ub=2)

x2_aprx = model.piecewise(0, pairs1, 0, name='x2')
px_aprx = model.piecewise(0, pairs2, 0, name='px')

model.minimize(x2_aprx(x) + px_aprx(x))

model.print_information()

model.solve()
solution = model.solution
x_value = solution.get_value(x)
print("Solution for x:", x_value)
