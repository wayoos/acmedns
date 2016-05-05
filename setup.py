# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='acme-dns',
    version='0.0.1',
    description='Issue and renew TLS certs from Let''s Encrypt with DNS challenge',
    long_description=readme,
    author='Stephane Cusin',
    author_email='staff@wayoos.com',
    url='https://github.com/wayoos/acme-dns',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)