# coding=utf-8
"""
appinstance
Active8 (04-03-15)
license: GNU-GPL2
"""
from setuptools import setup
setup(name='arguments',
      version='11',
      description='Argument parser based on docopt',
      url='https://github.com/erikdejonge/arguments',
      author='Erik de Jonge',
      author_email='erik@a8.nl',
      license='GPL',
      packages=['arguments'],
      zip_safe=True,
      install_requires=['docopt', 'schema', 'consoleprinter'])
