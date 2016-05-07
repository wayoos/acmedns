# -*- encoding: utf-8 -*-
#
# Copyright (c) 2016 Wayoos
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import unittest
import os
from acmedns.config import ConfigurationManager
from acmedns.adapter.ovh import OvhAdapter

TEST_CONFIG_FILENAME = os.path.join(os.path.dirname(__file__), 'acmedns_test.conf')


class BasicTestSuite(unittest.TestCase):

    def test_config(self):
        config_mng = ConfigurationManager.from_filename(TEST_CONFIG_FILENAME)
        self.assertEqual(config_mng.certs_path, '/etc/certs')

        config = config_mng.get_config()
        self.assertEqual(config.acme_url, 'https://acme-v01.api.letsencrypt.org')
        self.assertEqual(config.account_key, 'account.key')

        adapter = config_mng.get_adapter()
        self.assertIsInstance(adapter, OvhAdapter)

        domains = config_mng.get_domains()
        self.assertListEqual(domains, ['example.com/example.com.csr', 'example2.com/example2.com.csr'], "")

if __name__ == '__main__':
    unittest.main()
