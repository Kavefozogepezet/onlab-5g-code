import unittest

from test.optimizer_test import TestOptimizer
from test.savenet_test import TestSaveNet


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOptimizer))
    suite.addTest(unittest.makeSuite(TestSaveNet))

    runner = unittest.TextTestRunner()
    runner.run(suite) 