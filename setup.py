# coding=utf-8
"""
appinstance
Active8 (04-03-15)
license: GNU-GPL2
"""

from setuptools import setup
setup(name='arguments',
      version='68',
      description='Argument parser based on docopt',
      url='https://github.com/erikdejonge/arguments',
      author='Erik de Jonge',
      author_email='erik@a8.nl',
      license='GPL',
      packages=['arguments', 'fallbackdocopt'],
      zip_safe=True,
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
          "Operating System :: POSIX",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: System",
      ], requires=['future', 'ujson', 'sh'])
