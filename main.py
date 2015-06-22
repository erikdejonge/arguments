# coding=utf-8
"""
arguments test

Usage:
  tests.py [options] <posarg1> <posarg2>

Options:
  -h --help                     Show this screen.
  -o --option=<option1>         An option.
  --opt2=<option2>              An option [default: hello].
  -p --parameter=<parameter>    Folder to check the git repos out [default: 77].
  -v --verbose                  Folder from where to run the command [default: .].
  
author  : rabshakeh (erik@a8.nl)
project : pip
created : 22-06-15 / 17:48
  
"""
from arguments import Arguments


class IArguments(Arguments):
    """
    IArguments
    """
    def __init__(self, doc):
        """
        __init__
        """
        self.help = False
        self.opt2 = False
        self.option = False
        self.parameter = False
        self.posarg1 = 0
        self.posarg2 = ""
        self.verbose = False
        super().__init__(doc)


def main():
    """
    main
    """
    args = IArguments(doc=__doc__)
    print(args)


if __name__ == "__main__":
    main()
