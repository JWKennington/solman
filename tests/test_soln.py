"""Unittests for building solutions files"""


import pathlib
import unittest
from solman import soln


DEMO_ROOT = pathlib.Path(__file__).parent / 'demo'


class SolutionGroupTest(unittest.TestCase):
    def test_demo(self):
        g = soln.SolutionGroup(DEMO_ROOT)
        self.assertEqual(repr(g), "SolutionGroup(SampleName, 4P, 2E)")

        ps = g.problems        
        g.to_latex('demo_tmp.tex')
        print('woo')

    
