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

import base64
import logging
import subprocess
import re
import binascii
import json
import hashlib
import copy
import dns.resolver
import dns.exception
import time
import textwrap
import sys
import os
try:
    from urllib.request import urlopen  # Python 3
except ImportError:
    from urllib2 import urlopen  # Python 2

log = logging.getLogger(__name__)


class ClientConfig(object):

    def __init__(self, acme_url, account_key, contact_email, checkend):
        self.acme_url = acme_url
        self.account_key = account_key
        self.contact_email = contact_email
        self.checkend = checkend


class Client:

    def __init__(self, config, adapter):
        self.config = config
        self.adapter = adapter
        self.__load_account_key()

    # helper function base64 encode for jose spec
    @staticmethod
    def __b64(b):
        return base64.urlsafe_b64encode(b).decode('utf8').replace("=", "")

    def __load_account_key(self):
        # parse account key to get public key
        log.debug("Parsing account key %s", self.config.account_key)
        proc = subprocess.Popen(["openssl", "rsa", "-in", self.config.account_key, "-noout", "-text"],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise IOError("OpenSSL Error: {0}".format(err))
        pub_hex, pub_exp = re.search(
            r"modulus:\n\s+00:([a-f0-9\:\s]+?)\npublicExponent: ([0-9]+)",
            out.decode('utf8'), re.MULTILINE | re.DOTALL).groups()
        pub_exp = "{0:x}".format(int(pub_exp))
        pub_exp = "0{0}".format(pub_exp) if len(pub_exp) % 2 else pub_exp
        self.header = {
            "alg": "RS256",
            "jwk": {
                "e": Client.__b64(binascii.unhexlify(pub_exp.encode("utf-8"))),
                "kty": "RSA",
                "n": Client.__b64(binascii.unhexlify(re.sub(r"(\s|:)", "", pub_hex).encode("utf-8"))),
            },
        }
        account_key_json = json.dumps(self.header['jwk'], sort_keys=True, separators=(',', ':'))
        self.thumbprint = Client.__b64(hashlib.sha256(account_key_json.encode('utf8')).digest())

    # helper function make signed requests
    def __send_signed_request(self, url, payload):
        payload64 = Client.__b64(json.dumps(payload).encode('utf8'))
        protected = copy.deepcopy(self.header)
        protected["nonce"] = urlopen(self.config.acme_url + "/directory").headers['Replay-Nonce']
        protected64 = Client.__b64(json.dumps(protected).encode('utf8'))
        proc = subprocess.Popen(["openssl", "dgst", "-sha256", "-sign", self.config.account_key],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate("{0}.{1}".format(protected64, payload64).encode('utf8'))
        if proc.returncode != 0:
            raise IOError("OpenSSL Error: {0}".format(err))
        data = json.dumps({
            "header": self.header, "protected": protected64,
            "payload": payload64, "signature": Client.__b64(out),
        })
        try:
            resp = urlopen(url, data.encode('utf8'))
            return resp.getcode(), resp.read()
        except IOError as e:
            return getattr(e, "code", None), getattr(e, "read", e.__str__)()

    def reg_account(self):
        log.info("Registering account...")
        code, result = self.__send_signed_request(self.config.acme_url + "/acme/new-reg", {
            "resource": "new-reg",
            "contact": ["mailto:"+self.config.contact_email],
            "agreement": "https://letsencrypt.org/documents/LE-SA-v1.0.1-July-27-2015.pdf",
        })
        if code == 201:
            log.info("Registered!")
        elif code == 409:
            log.info("Already registered!")
        else:
            raise ValueError("Error registering: {0} {1}".format(code, result))

    @staticmethod
    def wait_challenge_deployed(domain):
        count = 0
        is_deployed = Client.check_domain(domain)
        while count < 24 and not is_deployed:
            time.sleep(5)
            count += 1
            is_deployed = Client.check_domain(domain)
        return is_deployed

    @staticmethod
    def check_domain(domain):
        try:
            answers = dns.resolver.query('_acme-challenge.{0}'.format(domain), 'TXT')
            if len(answers) > 0:
                return True
        except dns.exception.DNSException as e:
            log.debug("TXT not found: %s", e)
        except:
            log.error("Unexpected error: %s", sys.exc_info()[0])
            raise
        return False

    def sign(self, csr_file):
        sign_cert_file_name = csr_file.rsplit(".", 1)[0]
        sign_cert_file_name += '.crt'
        sign_cert_file_name = os.path.abspath(sign_cert_file_name)
        log.debug("Sign cert file name: %s", sign_cert_file_name)

        if os.path.isfile(sign_cert_file_name):
            # check if certificat is valid
            proc = subprocess.Popen(["openssl", "x509", "-checkend", self.config.checkend, "-in", sign_cert_file_name, "-noout"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if proc.returncode == 0:
                log.info("Certificat is valid for next {0}s : {1}".format(self.config.checkend, sign_cert_file_name))
                return

        return

        # find domains
        log.info("Parsing CSR %s", csr_file)
        proc = subprocess.Popen(["openssl", "req", "-in", csr_file, "-noout", "-text"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise IOError("Error loading {0}: {1}".format(csr_file, err))
        domains = set([])
        common_name = re.search(r"Subject:.*? CN=([^\s,;/]+)", out.decode('utf8'))
        if common_name is not None:
            domains.add(common_name.group(1))
        subject_alt_names = re.search(r"X509v3 Subject Alternative Name: \n +([^\n]+)\n", out.decode('utf8'), re.MULTILINE|re.DOTALL)
        if subject_alt_names is not None:
            for san in subject_alt_names.group(1).split(", "):
                if san.startswith("DNS:"):
                    domains.add(san[4:])

        # verify each domain
        for domain in domains:
            log.info("Verifying %s", domain)

            # get new challenge
            code, result = self.__send_signed_request(self.config.acme_url + "/acme/new-authz", {
                "resource": "new-authz",
                "identifier": {"type": "dns", "value": domain},
            })
            log.debug("Requesting challenges: {0} {1}".format(code, result))
            if code != 201:
                raise ValueError("Error requesting challenges: {0} {1}".format(code, result))

            challenge = [c for c in json.loads(result.decode('utf8'))['challenges'] if c['type'] == "dns-01"][0]
            token = re.sub(r"[^A-Za-z0-9_\-]", "_", challenge['token'])
            keyauthorization = "{0}.{1}".format(token, self.thumbprint)
            dnstoken = self.__b64(hashlib.sha256(keyauthorization).digest())

            ndd = domain.split(".")
            if len(ndd) == 2:
                subdomain = "_acme-challenge"
                basedomain = ndd[0] + "." + ndd[1]
            else:
                subdomain = "_acme-challenge." + ndd[0]
                basedomain = ndd[1] + "." + ndd[2]

            record = self.adapter.deploy_challenge(basedomain, subdomain, dnstoken)
            try:
                is_deployed = Client.wait_challenge_deployed(domain)

                if is_deployed:

                    # notify challenge are met
                    code, result = self.__send_signed_request(challenge['uri'], {
                        "resource": "challenge",
                        "keyAuthorization": keyauthorization,
                    })
                    if code != 202:
                        raise ValueError("Error triggering challenge: {0} {1}".format(code, result))

                    # wait for challenge to be verified
                    while True:
                        try:
                            resp = urlopen(challenge['uri'])
                            challenge_status = json.loads(resp.read().decode('utf8'))
                            log.debug(challenge_status)
                        except IOError as e:
                            raise ValueError("Error checking challenge: {0} {1}".format(
                                e.code, json.loads(e.read().decode('utf8'))))
                        if challenge_status['status'] == "pending":
                            log.debug("Pending")
                            time.sleep(1)
                        elif challenge_status['status'] == "valid":
                            log.debug("{0} verified!".format(domain))
                            break
                        else:
                            raise ValueError("{0} challenge did not pass: {1}".format(
                                domain, challenge_status))
            finally:
                self.adapter.delete_challenge(record)

        # get the new certificate
        log.info("Signing certificate...")
        proc = subprocess.Popen(["openssl", "req", "-in", csr_file, "-outform", "DER"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        csr_der, err = proc.communicate()
        code, result = self.__send_signed_request(self.config.acme_url + "/acme/new-cert", {
            "resource": "new-cert",
            "csr": self.__b64(csr_der),
        })
        if code != 201:
            raise ValueError("Error signing certificate: {0} {1}".format(code, result))

        sign_cert = """-----BEGIN CERTIFICATE-----\n{0}\n-----END CERTIFICATE-----\n""".format(
            "\n".join(textwrap.wrap(base64.b64encode(result).decode('utf8'), 64)))

        sign_cert_file = open(sign_cert_file_name, 'w')
        sign_cert_file.write(sign_cert)
        sign_cert_file.close()
        log.info("Certificate signed %s", sign_cert_file_name)
