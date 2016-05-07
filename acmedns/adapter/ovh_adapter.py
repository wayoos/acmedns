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

import logging
import ovh
from adapter import Adapter

log = logging.getLogger(__name__)


class OvhAdapter(Adapter):

    def __init__(self):
        self.endpoint = None
        self.application_key = None
        self.application_secret = None
        self.consumer_key = None
        self.client = None

    def setup(self, params):
        self.endpoint = params['endpoint']
        self.application_key = params['application_key']
        self.application_secret = params['application_secret']
        self.consumer_key = params['consumer_key']
        self.client = ovh.Client(self.endpoint, self.application_key, self.application_secret, self.consumer_key)

    def deploy_challenge(self, domain, tokenin):
        token = "\"" + tokenin + "\""
        ndd = domain.split(".")
        if len(ndd) == 2:
            subdomain = "_acme-challenge"
            basedomain = ndd[0] + "." + ndd[1]
        else:
            subdomain = "_acme-challenge." + ndd[0]
            basedomain = ndd[1] + "." + ndd[2]
        log.info("Deploy TXT domain: {0} subdomain: {1}".format(basedomain, subdomain))
        record = self.client.post('/domain/zone/%s/record' % basedomain, fieldType="TXT", subDomain=subdomain, ttl=60,
                                  target=token)
        log.info("Deploy record id: {0}".format(record))

        self.client.post('/domain/zone/%s/refresh' % basedomain)

        return record

    def delete_challenge(self, record):
        self.client.delete('/domain/zone/%s/record/%s' % (record['zone'], record['id']))
        self.client.post('/domain/zone/%s/refresh' % record['zone'])
