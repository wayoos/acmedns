# -*- coding: utf-8 -*-

import unittest
import os
from acmedns.config import ConfigurationManager

TEST_CONFIG_FILENAME = os.path.join(os.path.dirname(__file__), 'acmedns_test.conf')


class BasicTestSuite(unittest.TestCase):


    def test_config(self):
        confmng = ConfigurationManager.fromfilename(TEST_CONFIG_FILENAME)
        self.assertEqual(confmng.get('default', 'url'), 'https://acme-v01.api.letsencrypt.org')
        self.assertEqual(confmng.get('adapter-ovh', 'endpoint'), 'ovh-eu')
        self.assertEqual(confmng.get('adapter-ovh', 'application_key'), 'my_app_key')
        self.assertEqual(confmng.get('adapter-ovh', 'application_secret'), 'my_application_secret')
        self.assertEqual(confmng.get('adapter-ovh', 'consumer_key'), 'my_consumer_key')

if __name__ == '__main__':
    unittest.main()
