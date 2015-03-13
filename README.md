# arguments
Argument parser based on docopt


##install
```bash
pip install arguments
```

##usage
Docopt is used for parsing the docstring (__doc__), arguments bundles the schema parser and returns a OptionParser like object with normalized attributes

For example
```python
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
```

gives

```bash
$ python main.py pval1 pval2
<arguments.Arguments object at 0x1022e0eb8>
options :
    opt2 : hello
    option : None
    parameter : 77
    help : False
    verbose : False
positional :
    posarg1 : pval1
    posarg2 : pval2
```

or

```bash
$ python main.py -h
arguments test

Usage:
  tests.py [options] <posarg1> <posarg2>

Options:
  -h --help                     Show this screen.
  -o --option=<option1>         An option.
  --opt2=<option2>              An option [default: hello].
  -p --parameter=<parameter>    Folder to check the git repos out [default: 77].
  -v --verbose                  Folder from where to run the command [default: .].

$
```

##usage with classes

A nested docker style commandline program

```python
"""
File tooltest.py
"""

import arguments
from arguments import Schema, Use, SchemaError

class BaseArguments(arguments.Arguments):
    def __init__(self, doc, validateschema):
        argvalue = None
        yamlstr = None
        yamlfile = None
        parse_arguments = True
        persistoption = False
        alwaysfullhelp = False
        super().__init__(doc, validateschema, argvalue, yamlstr, yamlfile, parse_arguments, persistoption, alwaysfullhelp)

class MainArguments(BaseArguments):
    """
    MainArguments
    """
    @staticmethod
    def validtool(cmd):
        """
        @type cmd: str, unicode
        @return: None
        """
        validtools = ["tool1", "tool2", "tool3"]

        if cmd.strip().lower() not in validtools:
            raise SchemaError("tool", "*" + cmd + "* is not a valid tool")

        return cmd.strip()

    def __init__(self):
        doc = """
Some tools.
Usage:
    tools [options] [--] <tool> [<args>...]

Options:
    -h --help       Show this screen..
    -v --verbose    Verbose mode.

Commands:
    tool1   Bla bla bla
    tool2   Bla bla bla
    tool3   Bla bla bla
"""
        validateschema = Schema({'tool': Use(self.validtool)})
        self.tool = ""
        super().__init__(doc, validateschema)


class Tool1Arguments(BaseArguments):
    """
    MainArguments
    """
    @staticmethod
    def validtool(cmd):
        """
        @type cmd: str, unicode
        @return: None
        """
        validtools = ["run", "build"]

        if cmd.strip().lower() not in validtools:
            raise SchemaError("tool", "*" + cmd + "* is not a valid tool")

        return cmd.strip()

    def __init__(self):
        doc = """
Tool 1 .
Usage:
    tools tool1 [options] [--] <command> [<args>...]

Options:
    -h --help       Show this screen..
    -v --verbose    Verbose mode.

Commands:
    run     Run the tool
    build   Build the tool
"""
        validateschema = Schema({'tool': Use(self.validtool)})
        self.tool = ""
        super().__init__(doc, validateschema)


def main():
    """
    main
    """
    args = MainArguments()

    print args

    if args.tool.lower() == "vagrant":
        args = VagrantArguments()
        driver_vagrant(args)

if __name__=="__main__":
    main()

```

```sh

$ python tools.py
Usage:
    tools [options] [--] <tool> [<args>...]


$ python tools.py -h
Some tools.
Usage:
    tools [options] [--] <tool> [<args>...]

Options:
    -h --help       Show this screen..
    -v --verbose    Verbose mode.

Commands:
    tool1   Bla bla bla
    tool2   Bla bla bla
    tool3   Bla bla bla


$ python tools.py tool1
<__main__.MainArguments object at 0x108da6748>
options:
    help: False
    verbose: False
positional:
    args: []
    tool: tool1

Usage:
    tools tool1 [options] [--] <command> [<args>...]


$ python tools.py tool1 -h
Tool 1 .
Usage:
    tools tool1 [options] [--] <command> [<args>...]

Options:
    -h --help       Show this screen..
    -v --verbose    Verbose mode.

Commands:
    run     Run the tool
    build   Build the tool



$ python tools.py tool1 run
<__main__.MainArguments object at 0x104414748>
options:
    help: False
    verbose: False
positional:
    args: ['run']
    tool: tool1
```

##Using schema
Assume you are using **docopt** with the following usage-pattern:

```bash
my_program.py [--count=N] <path> <files>
```

and you would like to validate that `<files>` are readable, and that
`<path>` exists, and that `--count` is either integer from 0 to 5, or
`None`.

this is how you validate it using schema:

```python
>>> from arguments import *

>>> s = Schema({'<files>': [Use(open)],
...             '<path>': os.path.exists,
...             '--count': Or(None, And(Use(int), lambda n: 0 < n < 5))})

>>> args = Arguments(validateschema=s)

>>> args.files
[<open file 'LICENSE-MIT', mode 'r' at 0x...>, <open file 'setup.py', mode 'r' at 0x...>]

>>> args.path
'../'

>>> args.count
3
```

As you can see, it validated data successfully, opened files and
converted `'3'` to `int`.