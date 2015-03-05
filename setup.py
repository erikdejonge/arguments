# coding=utf-8
"""
appinstance
erik@a8.nl (04-03-15)
license: GNU-GPL2
"""
from setuptools import setup
setup(name='arguments',
      version='1',
      description='Argument parser based on docopt',
      url='https://github.com/erikdejonge/arguments',
      author='Erik de Jonge',
      author_email='erik@a8.nl',
      license='GPL',
      packages=['arguments'],
      zip_safe=True, requires=['docopt', 'schema', 'consoleprinter'])
