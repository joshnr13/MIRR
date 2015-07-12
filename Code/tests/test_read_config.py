import unittest
from config_yaml_reader import parse_list_and_get_random


class TestCase(unittest.TestCase):

    def test_read_distribution_values_yaml(self):
        for data in [
            '1110',
            '1000, normal, 1, 0.09',
            '1000, linear, 0.8, 1.2',
            '1000, weibull, 10',
            '1000, triangular, 0.8, 1.5, 1.1'
        ]:
            result = parse_list_and_get_random(data)
            self.assertTrue(isinstance(result, (int, float)))
            self.assertLess(result, 2000)
            self.assertGreater(result, 10)

