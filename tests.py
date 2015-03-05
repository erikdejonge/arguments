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
from unittester import *
from arguments import Arguments


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


    def test_constructor(self):
        """
        test_parse_args
        """
        self.arguments = Arguments(__doc__)
        self.assertIsNotNone(self.arguments)


def main():
    """
    main
    """
    unit_test_main(globals())


if __name__ == "__main__":
    main()
