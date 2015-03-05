# arguments
Argument parser based on docopt


##install
```bash
pip install arguments
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