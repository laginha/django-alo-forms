#!/usr/bin/env python
# encoding: utf-8
from setuptools import setup
from setuptools import find_packages

setup(
    name             = 'django-alo-forms',
    version          = '1.9.1',
    author           = "Diogo Laginha",
    author_email     = "diogo.laginha.machado@gmail.com",
    url              = 'https://github.com/laginha/django-alo-forms',
    description      = "Additional Logic on Forms",
    packages         = find_packages(where='src'),
    package_dir      = {'': 'src'},
    install_requires = [
        'django', 'django_easy_response',
    ],
    extras_require   = {},
    zip_safe         = False,
    license          = 'MIT',
    classifiers      = [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Intended Audience :: Developers',
    ]
)
