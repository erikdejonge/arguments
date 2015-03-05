#!/usr/bin/env python
# coding=utf-8
"""
arguments test

Usage:
  tests.py <posarg1> <posarg2>

Options:
  -h --help                     Show this screen.
  -o --option=<option1>         An option.
  --option2=<option2>           An option [default: hello].
  -p --parameter=<parameter>    Folder to check the git repos out [default: 77].
  -v --verbose                  Folder from where to run the command [default: .].
"""

# Author:
#   erik@a8.nl (04-03-15)
#   license: GNU-GPL2

import os
import unittest
from arguments import Arguments
from pyprofiler import start_profile, end_profile
from console_utils import console

def raises_error(*args, **kwds):
    """
    @type args: tuple
    @type kwds: str, unicode
    @return: None
    """
    raise ValueError('Invalid value: %s%s' % (args, kwds))


class ArgumentTest(unittest.TestCase):
    """
    @type unittest.TestCase: class
    @return: None
    """
    arguments = None

    def setUp(self):
        """
        setUp
        """
        self.arguments = Arguments(__doc__)


    def test_assert_raises(self):
        """
        test_assert_raises
        """
        self.assertRaises(ValueError, raises_error, 'a', b='c')

    def test_parse_args(self):
        """
        test_parse_args
        """
        self.assertIsNotNone(self.arguments)


def main():
    """
     @DynamicAttrs
    main
    """
    print run_unit_test("ArgumentTest", caller_globals=globals())


if __name__ == "__main__":
    main()
