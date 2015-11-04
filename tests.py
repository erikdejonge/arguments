# coding=utf-8
"""
 coding=utf-8
 Author:
   Active8 (04-03-15)
   license: GNU-GPL2
"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
#from unittester import *
from arguments import *
import unittest

def raises_error(*args, **kwds):
    """
    @type args: tuple
    @type kwds: str, unicode
    @return: None
    """
    raise ValueError('Invalid value: %s%s' % (args, kwds))

optionsdoc = """
arguments test
Usage:
  tests.py [options] <posarg1> <posarg2>

Options:
  -h --help                     Show this screen.
  -o --option=<option1>         An option.
  --opt2=<option2>              An option [default: hello].
  -p --parameter=<parameter>    Folder to check the git repos out [default: 77].
  -v --verbose                  Folder from where to run the command [default: .].
"""

optionsdoc2 = """
arguments context test
Usage:
  tests.py contextindicator [options] <posarg1> <posarg2>

Options:
  -h --help                     Show this screen.
  -o --option=<option1>         An option.
  --opt2=<option2>              An option [default: hello].
  -p --parameter=<parameter>    Folder to check the git repos out [default: 77].
  -v --verbose                  Folder from where to run the command [default: .].
"""


class ArgumentTest(unittest.TestCase):
    """
    @type unittest.TestCase: class
    @return: None
    """
    arguments = None

    def test_constructor_empty(self):
        """
        test_parse_args
        """
        myschema = Schema({})

        def test_empty():
            """
            test_empty
            """

            Arguments(optionsdoc, validateschema=myschema, argvalue=[])

        self.assertRaises(SystemExit, test_empty)

        exit_ex = None
        try:
            arg = Arguments(doc=optionsdoc, validateschema=myschema, argvalue=[])
        except BaseException as b:
            exit_ex = b

        self.assertIsNotNone(exit_ex)



    def test_constructor_posargs(self):
        """
        test_parse_args
        """
        myschema = Schema({"posarg1": Or(str), "posarg2": Or(str)})
        exit_ex = None
        args = None
        try:
            args = Arguments(doc=optionsdoc, validateschema=myschema, argvalue=['posval1', 'posval2'])
        except DocoptExit as de:
            exit_ex = de

        self.assertIsNone(exit_ex)
        self.assertIsNotNone(args)
        self.assertEqual(args.posarg1, "posval1")
        self.assertEqual(args.posarg2, "posval2")

    def test_constructor_noschema(self):
        """
        test_constructor_noschema
        """
        inputval = ['-o', '4', "--opt2='foobar'", 'aa', 'bb']
        args = Arguments(doc=optionsdoc, argvalue=inputval)
        self.assertIsNotNone(args)
        self.assertEqual(args.posarg1, "aa")
        self.assertEqual(args.posarg2, "bb")
        self.assertEqual(args.option, 4)
        self.assertEqual(args.opt2, "foobar")

    def test_yaml(self):
        """
        test_yaml
        """
        inputval = ['-o', '4', "--opt2='foobar'", 'aa', 'bb']
        args = Arguments(doc=optionsdoc, argvalue=inputval)
        yamls = args.as_yaml()
        args2 = Arguments(yamlstr=yamls)
        self.assertEqual(args.as_yaml(), args2.as_yaml())

    def test_numbers(self):
        """
        test_numbers
        """
        inputval = ['-o', '4', "--opt2='foobar'", 'aa', 'bb']
        args = Arguments(doc=optionsdoc, argvalue=inputval)
        self.assertIsNotNone(args)
        self.assertEqual(args.option, 4)

    def test_context(self):
        """
        test_context
        """
        inputval = ['contextindicator','-o', '4',  'bb', 'aa']
        args = Arguments(doc=optionsdoc2, argvalue=inputval)

        self.assertIsNotNone(args)
        self.assertEqual(args.option, 4)
        self.assertTrue(args.contextindicator)



def main():
    """
    main
    """
    #unit_test_main(globals())
    pass


if __name__ == "__main__":
    main()
