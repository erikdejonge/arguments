# coding=utf-8
"""
 coding=utf-8
 Author:
   erik@a8.nl (04-03-15)
   license: GNU-GPL2
"""
from unittester import *
from arguments import *


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

        self.assertRaises(DocoptExit, test_empty)

        exit_ex = None
        try:
            Arguments(optionsdoc, myschema, argvalue=[])
        except DocoptExit as de:
            exit_ex = de

        self.assertIsNotNone(exit_ex)

        retval = "Usage:\n  tests.py [options] <posarg1> <posarg2>"
        self.assertEqual(exit_ex.usage.strip(), retval.strip())

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
        test_parse_args
        """
        args = None
        inputval = ['-o', '4', "--opt2='foobar'", 'aa', 'bb']

        args = Arguments(doc=optionsdoc, argvalue=inputval)
        self.assertIsNotNone(args)
        self.assertEqual(args.posarg1, "aa")
        self.assertEqual(args.posarg2, "bb")
        self.assertEqual(args.option, "4")
        self.assertEqual(args.opt2, "foobar")

    def test_yaml(self):


        inputval = ['-o', '4', "--opt2='foobar'", 'aa', 'bb']

        args = Arguments(doc=optionsdoc, argvalue=inputval)
        yaml = args.as_yaml()
        args2 = Arguments(yamlstr=yaml)
        self.assertEqual(args.as_yaml(), args2.as_yaml())

def main():
    """
    main
    myschema = Schema({"pa_command": Or(None, str),
                             "pa_giturl": Or(None, lambda x: ".git" in x),
                             Optional("-i"): int,
                             Optional("op_help"): Or(Use(bool), error="[-h|--help] must be a bool"),
                             Optional("op_verbose"): Or(Use(bool), error="[-v|--verbose] must be a bool"),
                             Optional("op_once"): Or(Use(bool), error="[-o|--once] must be a bool"),
                             Optional("op_interval"): Or(Use(int), error="[-i|--interval] must be an int"),
                             Optional("op_load"): Or(None, exists, error='[-l|--load] path should not exist'),
                             Optional("op_write"): Or(None, self.not_exists, exists, error='[-w|--write] path exists'),
                             Optional("op_gitfolder"): Or(str, exists, error='[-g|--gitfolder] path should exist'),
                             Optional("op_cmdfolder"): Or(str, exists, error='[-c|--cmdfolder] path should exist')})

    """

    #import sys
    #arguments = docopt(optionsdoc)
    # print "---"
    # print arguments
    unit_test_main(globals())


if __name__ == "__main__":
    main()
