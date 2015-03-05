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


def run_unit_test(class_name=None, methodname=None, caller_globals=None, failfast=True, profile=False, quiet=False):
    """
    @type class_name: str, unicode
    @type methodname: str, unicode
    @type caller_globals: str, unicode
    @type failfast: bool
    @type profile: bool
    @return: None
    """

    #clear_screen()
    suite = unittest.TestSuite()

    if failfast is None:
        failfast = True

    if methodname and not class_name:
        for i in caller_globals:
            if isinstance(caller_globals[i], type):
                if issubclass(caller_globals[i], unittest.TestCase):
                    for m in dir(caller_globals[i]):
                        if methodname == m:
                            if class_name:
                                console("found another", m, "in", i, color="red")
                                a = raw_input("would you like to use this one? (y/n=default): ")

                                if a.strip().lower() == "y":
                                    class_name = i
                            else:
                                if quiet is False:
                                    console("found", m, "in", i, color="cyan")

                                class_name = i

        if not class_name:
            raise ValueError("run_unit_test:cannot find class for method")

    cl = [os.path.basename(os.getcwd())]

    if methodname and class_name:
        cl.append(class_name + ":" + methodname)
    elif class_name:
        cl.append(class_name)
    elif methodname:
        cl.append(methodname)

    if failfast is True:
        if quiet is False:
            cl.append("failing fast")

    if class_name != "_*_":
        if len(cl) > 0:
            if quiet is False:
                console(*cl, color="cyan")

    if methodname and class_name:
        cls = caller_globals[class_name]
        suite.addTest(cls(methodname))
    else:
        if class_name is not None:
            suite = unittest.TestLoader().loadTestsFromTestCase(caller_globals[class_name])
        else:
            if "TESTDIR" in os.environ:
                suite = unittest.TestLoader().discover(os.environ["TESTDIR"])
            else:
                suite = unittest.TestLoader().discover(".")

    profiletrace = None

    if profile is True:
        profiletrace = start_profile()

    if quiet is True:
        buffer = ""
        result = unittest.TextTestRunner(failfast=failfast, stream=open("/dev/null", "w"), buffer=buffer).run(suite)
    else:
        result = unittest.TextTestRunner(failfast=failfast).run(suite)

    if profiletrace is not None:
        end_profile(profiletrace, items=50)

    return result

def main():
    """
     @DynamicAttrs
    main
    """
    print run_unit_test("ArgumentTest", caller_globals=globals())


if __name__ == "__main__":
    main()
