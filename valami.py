import numpy as np

class IterTest:
    def __iter__(self):
        for i in range(10):
            yield i




for i in IterTest():
    print(i)
