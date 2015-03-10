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
"""

from arguments import Arguments

def main():
    """
    main
    """
    arg = Arguments()
    print(arg)


if __name__ == "__main__":
    main()
    