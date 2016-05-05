# -*- coding: utf-8 -*-

import acmedns
import unittest


class AdvancedTestSuite(unittest.TestCase):
    """Advanced test cases."""

    def test_thoughts(self):
        acmedns.hmm()


if __name__ == '__main__':
    unittest.main()
