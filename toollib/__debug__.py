"""
@author axiner
@version v1.0.0
@created 2021/12/14 20:20
@abstract
@description
@history
"""
import unittest

from toollib import here


class TestDebug(unittest.TestCase):

    def test_001(self):
        print(here)
