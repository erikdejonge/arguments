# arguments
Argument parser based on docopt


##install
```bash
pip install arguments
```

##usage
Docopt is used for parsing the docstring (__doc__), arguments bundles the schema parser and returns a OptionParser like object with normalized attributes

For example
```
arguments test

Usage:
  tests.py <posarg1> <posarg2>

Options:
  -h --help                     Show this screen.
  -o --option=<option1>         An option.
  --option2=<option2>           An option [default: hello].
  -p --parameter=<parameter>    Folder to check the git repos out [default: 77].
  -v --verbose                  Folder from where to run the command [default: .].
```

called like

```bash
python tests.py pval1 pval2
```

will when called in python return

```python
>>> myargs = Arguments()
>>> print myargs.posarg1
pyval1

>>> print myargs.posarg2
pyval2
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