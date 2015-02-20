#!/usr/bin/env python
# encoding: utf-8
from setuptools import setup, find_packages
import pip

requirements = pip.req.parse_requirements('requirements.txt')
install_requires = [
    str(each.req) for each in requirements if each.req
]

setup(
    name             = 'alo-forms',
    version          = '1.0',
    author           = "Diogo Laginha",
    url              = 'https://github.com/laginha/django-alo-forms',
    description      = "Additional Logic on Forms",
    packages         = find_packages(where='src'),
    package_dir      = {'': 'src'},
    install_requires = install_requires,
    extras_require   = {},
    zip_safe         = False,
)
