# coding=utf-8
"""
arguments
Active8 (04-03-15)
license: GNU-GPL2
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import super
from builtins import dict
from builtins import open
from builtins import int
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from builtins import object

# noinspection PyUnresolvedReferences
from fallbackdocopt import DocoptExit, docopt

import os
import sys
import yaml
import shutil
import requests
import zipfile
from os.path import exists, expanduser
from consoleprinter import console, console_warning, handle_ex, consoledict, get_print_yaml, remove_extra_indentation, snake_case, bar


class SchemaError(Exception):
    """Error during Schema validation."""
    def __init__(self, autos, errors):
        """
        @type autos:  list, tuple, str
        @type errors: list, str
        @return: None
        """
        self.autos = autos if isinstance(autos, list) else [autos]
        self.errors = errors if isinstance(errors, list) else [errors]
        Exception.__init__(self, self.code)

    @property
    def code(self):
        """
        code
        """

        def uniq(seq):
            """
            @type seq: str
            @return: None
            """
            seen = set()
            seen_add = seen.add
            return [x for x in seq if x not in seen and not seen_add(x)]

        # noinspection PyTypeChecker
        a = uniq(i for i in self.autos if i is not None)
        # noinspection PyTypeChecker
        e = uniq(i for i in self.errors if i is not None)

        if e:
            return '\n'.join(e)

        return '\n'.join(a)


class And(object):
    """
    And
    """
    def __init__(self, *args, **kw):
        """
        @type args: tuple
        @type **kw: str
        @return: None
        """
        self._args = args
        assert list(kw) in (['error'], [])
        self._error = kw.get('error')

    def __repr__(self):
        """
        __repr__
        """
        return '%s(%s)' % (self.__class__.__name__,

                           ', '.join(repr(a) for a in self._args))

    def validate(self, data):
        """
        @type data: str
        @return: None
        """
        for s in [Schema(s, error=self._error) for s in self._args]:
            data = s.validate(data)

        return data


class Or(And):
    """
    Or
    """
    def validate(self, data):
        """
        @type data: list, tuple
        @return: None
        """
        x = SchemaError([], [])
        for s in [Schema(s, error=self._error) for s in self._args]:
            try:
                return s.validate(data)
            except SchemaError as _x:
                x = _x
        raise SchemaError(['%r did not validate %r' % (self, data)] + x.autos, [self._error] + x.errors)


class Use(object):
    """
    Use
    """
    def __init__(self, callable_, error=None):
        """
        @type callable_:  list, tuple
        @type error: str, None
        @return: None
        """
        assert callable(callable_)
        self._callable = callable_
        self._error = error

    def __repr__(self):
        """
        __repr__
        """
        return '%s(%r)' % (self.__class__.__name__, self._callable)

    def validate(self, data):
        """
        @type data: str
        @return: None
        """
        try:
            return self._callable(data)
        except SchemaError as x:
            raise SchemaError([None] + x.autos, [self._error] + x.errors)
        except BaseException as x:
            f = self._callable.__name__
            raise SchemaError('%s(%r) raised %r' % (f, data, x), self._error)


COMPARABLE, CALLABLE, VALIDATOR, TYPE, DICT, ITERABLE = list(range(6))


def priority(s):
    """
    @type s: object
    @return: None
    """
    if type(s) in (list, tuple, set, frozenset):
        return ITERABLE

    if isinstance(s, dict):
        return DICT

    if issubclass(type(s), type):
        return TYPE

    if hasattr(s, 'validate'):
        return VALIDATOR

    if callable(s):
        return CALLABLE
    else:
        return COMPARABLE


class Schema(object):
    """
    Schema
    """
    def __init__(self, schema, error=None):
        """
        @type schema:  list, tuple
        @type error:  list, tuple
        @return: None
        """
        self._schema = schema
        self._error = error

    def __repr__(self):
        """
        __repr__
        """
        return '%s(%r)' % (self.__class__.__name__, self._schema)

    def add_void_schema_item(self, key):
        """
        @type key: str
        @return: None
        """
        # noinspection PyUnresolvedReferences
        self._schema[key] = Use(str)

    def get_keys(self):
        """
        get_keys
        """
        # noinspection PyUnresolvedReferences
        return list(self._schema.keys())

    def validate(self, data):
        """
        @type data: dict
        @return: None
        """
        s = self._schema
        e = self._error
        nkey = None
        nvalue = None
        flavor = priority(s)

        if flavor == ITERABLE:
            data = Schema(type(s), error=e).validate(data)
            return type(s)(Or(*s, error=e).validate(d) for d in data)

        if flavor == DICT:
            data = Schema(dict, error=e).validate(data)
            new = type(data)()  # new - is a dict of the validated values
            x = None
            coverage = set()  # non-optional schema keys that were matched
            covered_optionals = set()

            # for each key and value find a schema entry matching them, if any
            sorted_skeys = list(sorted(s, key=priority))

            for key, value in list(data.items()):
                valid = False
                skey = None

                for skey in sorted_skeys:
                    svalue = s[skey]
                    try:
                        nkey = Schema(skey, error=e).validate(key)
                    except SchemaError:
                        pass
                    else:
                        try:
                            nvalue = Schema(svalue, error=e).validate(value)
                        except SchemaError as _x:
                            # noinspection PyUnusedLocal
                            x = _x
                            raise
                        else:
                            (covered_optionals if isinstance(skey, Optional)
                             else coverage).add(skey)
                            valid = True
                            break

                if valid:
                    if nkey is None:
                        raise AssertionError("nkey is None")

                    if nvalue is None:
                        raise AssertionError("nvalue is None")

                    new[nkey] = nvalue
                elif skey is not None:
                    if x is not None:
                        raise SchemaError(['invalid value for key %r' % key] + x.autos, [e] + x.errors)

            required = set(k for k in s if not isinstance(k, Optional))
            if coverage != required:
                raise SchemaError('missed keys %r' % (required - coverage), e)

            if len(new) != len(data):
                wrong_keys = set(data.keys()) - set(new.keys())
                s_wrong_keys = ', '.join('%r' % (k,) for k in sorted(wrong_keys))
                raise SchemaError('wrong keys %s in %r' % (s_wrong_keys, data), e)

            # Apply default-having optionals that haven't been used:
            defaults = set(k for k in s if isinstance(k, Optional) and
                           hasattr(k, 'default')) - covered_optionals

            for default in defaults:
                new[default.key] = default.default

            return new

        if flavor == TYPE:
            if isinstance(data, s):
                return data
            else:
                raise SchemaError('%r should be instance of %r' % (data, s), e)

        if flavor == VALIDATOR:
            try:

                # noinspection PyUnresolvedReferences
                return s.validate(data)
            except SchemaError as x:
                raise SchemaError([None] + x.autos, [e] + x.errors)
            except BaseException as x:
                raise SchemaError('%r.validate(%r) raised %r' % (s, data, x),

                                  self._error)

        if flavor == CALLABLE:
            f = s.__name__
            try:

                # noinspection PyCallingNonCallable
                if s(data):
                    return data
            except SchemaError as x:
                raise SchemaError([None] + x.autos, [e] + x.errors)
            except BaseException as x:
                raise SchemaError('%s(%r) raised %r' % (f, data, x),

                                  self._error)

            raise SchemaError('%s(%r) should evaluate to True' % (f, data), e)

        if s == data:
            return data
        else:
            raise SchemaError('%r does not match %r' % (s, data), e)


MARKER = object()


class Optional(Schema):
    """Marker for an optional part of Schema."""
    def __init__(self, *args, **kwargs):
        """
        @type args: tuple
        @type kwargs: dict
        @return: None
        """
        default = kwargs.pop('default', MARKER)
        super(Optional, self).__init__(*args, **kwargs)

        if default is not MARKER:
            # See if I can come up with a static key to use for myself:
            if priority(self._schema) != COMPARABLE:
                raise TypeError(

                    'Optional keys with defaults must have simple, '
                    'predictable values, like literal strings or ints. '
                    '"%r" is too complex.' % (self._schema,))

            self.default = default
            self.key = self._schema


def not_exists(path):
    """
    @type path: str
    @return: None
    """
    return not exists(path)


def flattened(mylist, newlist):
    """
    @type mylist: list
    @type newlist: list
    @return: None
    """
    for item in mylist:
        if isinstance(item, list):
            flattened(item, newlist)
        else:
            newlist.append(item)


def abspath(p):
    """
    @type p: str
    @return: None
    """
    return os.path.normpath(os.path.join(os.getcwd(), p))


def unzip(source_filename, dest_dir):
    """
    @type source_filename: str
    @type dest_dir: str
    @return: None
    """
    zippath = os.path.join(dest_dir, source_filename)

    if not os.path.exists(zippath):
        console("zipfile doesn't exist", zippath, color="red")
        raise FileNotFoundError(zippath)

    with zipfile.ZipFile(zippath) as zf:
        zf.extractall(dest_dir)

    extracted_dir = os.path.join(os.path.join(os.getcwd(), dest_dir), "k8svag-createproject-master")

    if os.path.exists(extracted_dir):
        for mdir in os.listdir(extracted_dir):
            shutil.move(os.path.join(extracted_dir, mdir), dest_dir)

        os.rmdir(extracted_dir)
        os.remove(os.path.join(os.getcwd(), os.path.join(dest_dir, "master.zip")))
    else:
        console_warning(extracted_dir + " not created")
        raise FileExistsError(extracted_dir + " not created")


def download(url, mypath):
    """
    @type url: str∂
    @type mypath: str
    @return: None
    """
    r = requests.get(url, stream=True)
    with open(mypath, 'wb') as f:
        total_length = r.headers.get('content-length')

        if total_length is not None:
            total_length = int(total_length)

            for chunk in bar(r.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1):
                if chunk:
                    f.write(chunk)
                    f.flush()


def delete_directory(dirpath, excluded_file_names):
    """
    @type dirpath: str
    @type excluded_file_names: list, tuple
    @return: int
    """
    for rootpath, dirs, files in os.walk(dirpath):
        for f in files:
            fp = os.path.join(rootpath, f)

            for exname in excluded_file_names:
                if not fp.endswith(exname):
                    if os.path.exists(fp):
                        os.remove(fp)

    dirpaths = []

    for rootpath, dirs, files in os.walk(dirpath):
        dirpaths.append(rootpath)

    dirpaths.sort(key=lambda x: len(x.split("/")))
    dirpaths.reverse()

    for rootpath in dirpaths:
        if dirpath != rootpath:
            if os.path.exists(rootpath):
                os.rmdir(rootpath)

    return len(list(os.walk(dirpath)))


def abort(command, description):
    """
    @type command: str, None
    @type description: str
    @return: None
    """
    if command is None:
        command = "?"

    console("-" + command + ": " + description, color="red", plaintext=True)


def warning(command, description):
    """
    @type command: str, None
    @type description: str
    @return: None
    """
    if command is None:
        command = "?"

    console("-" + command + ": " + description, color="orange", plaintext=True)


def info(command, description):
    """
    @type command: str, None
    @type description: str
    @return: None
    """
    if command is None:
        command = "?"

    console("-" + command + ": " + description, color="green", plaintext=True)


def doinput(description):
    """
    @type description: str
    @return: None
    """
    console(description, color="white", plaintext=True, newline=False)
    return input("$: ").lower()


class Arguments(object):
    """
    Arguments
    """
    def __init__(self, doc=None, validateschema=None, argvalue=None, yamlstr=None, yamlfile=None, parse_arguments=True, persistoption=False, alwaysfullhelp=False, version=None, parent=None):
        """
        @type doc: str, None
        @type validateschema: Schema, None
        @type yamlfile: str, None
        @type yamlstr: str, None
        @type parse_arguments: bool
        @type argvalue: str, None
        @return: None
        """
        self.m_once = None
        self.write = None
        self.load = None
        self.m_schema = validateschema
        self.m_reprdict = {}
        self.m_doc = ""
        self.__add_parent(parent)

        if parent is not None:
            if hasattr(parent, "help") and parent.help is True:
                if len(parent.positional["args"]) == 0:
                    print()

        if doc is not None:
            triggerword = "usage"
            newdoc = remove_extra_indentation(doc, triggerword)
            self.m_doc = newdoc

        self.m_argv = argvalue
        self.m_persistoption = persistoption
        self.m_alwaysfullhelp = alwaysfullhelp
        self.m_version = version

        if not hasattr(self, "m_commandline_help"):
            self.m_commandline_help = {}

        if yamlfile:
            self.from_yaml_file(yamlfile)
        elif yamlstr:
            self.from_yaml(yamlstr)
        elif parse_arguments is True:
            parsedok = False
            exdoc = False
            sysex = False
            try:
                self.parse_arguments(self.m_schema)
                parsedok = True
            except DocoptExit:
                exdoc = True
                raise
            except SystemExit:
                sysex = True
                raise

            finally:
                if parsedok is False and exdoc is False and sysex is False:
                    print()

                if hasattr(self, "help") and getattr(self, "help") is True:
                    if "args" in self.positional:
                        if len(self.positional["args"]) == 0:
                            self.print_commandline_help()

            if self.write is not None:
                fp = open(self.write, "w")
                self.write = ""
                fp.write(self.as_yaml())
                self.write = fp.name
                fp.close()
            elif self.load is not None:
                self.from_yaml_file(self.load)

        if yamlfile:
            raise AssertionError("not implemented")

    def __add_parent(self, parent):
        """
        @type parent: Arguments
        @return: None
        """
        if not hasattr(self, "m_parents"):
            self.m_parents = None

        if parent is not None:
            if not isinstance(self.m_parents, list):
                self.m_parents = []
            self.m_parents.append(parent)

    def parse_arguments(self, schema=True):
        """
        @type schema: Schema
        @return: None
        """
        arguments = None

        if schema is not None:
            self.m_schema = schema

        if self.load is None:
            if self.m_doc is None:
                # noinspection PyUnresolvedReferences
                import __main__
                triggerword = "usage"
                self.m_doc = remove_extra_indentation(__main__.__doc__, triggerword)

            if self.m_persistoption is True:
                optsplit = self.m_doc.split("Options:")
                optsplit[0] += "Options:\n"
                optsplit[0] += """    -w --write=<writeymlpath>\tWrite arguments yaml file.\n    -l --load=<loadymlpath>\tLoad arguments yaml file."""
                self.m_doc = "".join(optsplit)
                console(optsplit)

            self.m_doc += "\n"
            try:
                if self.m_argv is None:
                    self.m_argv = sys.argv[1:]

                sorted_argv = []
                options_argv = []
                next_is_option = False

                for argvitem in self.m_argv:
                    if next_is_option is True:
                        options_argv.append(argvitem)
                        next_is_option = False
                    else:
                        if str(argvitem).startswith("-") and not str(argvitem).startswith("--"):
                            options_argv.append(argvitem)
                            next_is_option = True
                        else:
                            sorted_argv.append(argvitem)

                flattened_sorted_argv = []

                if len(options_argv) > 0:
                    if len(sorted_argv) > 0:
                        sorted_argv.insert(len(sorted_argv) - 1, options_argv)
                    else:
                        sorted_argv.insert(0, options_argv)

                flattened(sorted_argv, flattened_sorted_argv)

                # self.m_argv = flattened_sorted_argv
                arguments = dict(docopt(self.m_doc, self.m_argv, options_first=False, version=self.m_version))

                # console(arguments, plainprint=True, color="green")

                if "--help" in [s for s in arguments.values() if isinstance(s, str)] or "-h" in [s for s in arguments.values() if isinstance(s, str)]:
                    print(self.m_doc.strip())
                    exit(0)
            except DocoptExit:
                if self.m_alwaysfullhelp is True:
                    print(self.m_doc.strip())
                    exit(0)
                else:
                    if "-h" in self.m_argv or "--help" in self.m_argv:
                        print(self.m_doc.strip())
                        exit(0)
                    else:
                        raise

            k = ""
            try:
                if isinstance(arguments, dict):
                    for k in arguments:
                        if "folder" in k or "path" in k:
                            if hasattr(arguments[k], "replace"):
                                arguments[k] = arguments[k].replace("~", expanduser("~"))

                                if arguments[k].strip() == ".":
                                    arguments[k] = os.getcwd()

                                if "./" in arguments[k].strip():
                                    arguments[k] = arguments[k].replace("./", os.getcwd() + "/")

                                arguments[k] = arguments[k].rstrip("/").strip()

            except AttributeError as e:
                console("Attribute error:" + k.strip(), "->", str(e), color="red")

                if isinstance(arguments, dict):
                    for k in arguments:
                        console(k.strip(), color="red")

                handle_ex(e)
        else:
            if isinstance(self.load, str):
                # noinspection PyTypeChecker
                loaded_arguments = yaml.load(open(self.load))
                arguments = {}
                for k in loaded_arguments["options"]:
                    arguments["op_" + k] = loaded_arguments["options"][k]
                for k in loaded_arguments["positional"]:
                    arguments["pa_" + k] = loaded_arguments["positional"][k]
            else:
                console("self.load is not a str", self.load, color="red")
        try:
            if not isinstance(arguments, dict):
                raise AssertionError("arguments should be a dict by now")

            if "--" in arguments:
                del arguments["--"]

            validate_arguments = dict((x.replace("<", "").replace(">", "").replace("--", "").replace("-", "_"), y) for x, y in arguments.items())

            if self.m_schema is not None:
                schema_keys = self.m_schema.get_keys()

                for k in list(validate_arguments.keys()):
                    if k not in schema_keys:
                        self.m_schema.add_void_schema_item(k)
                self.m_schema.validate(validate_arguments)

            arguments = dict((x.replace("<", "pa_").replace(">", "").replace("--", "op_").replace("-", "_"), y) for x, y in arguments.items())
        except SchemaError as e:
            name = self.get_command_path()
            console("-" + name + ": ", "".join([x for x in e.errors if x]), color="red", plainprint=True)
            print()
            print(self.m_doc.strip())
            exit(1)

        options, positional_arguments = self.sort_arguments(arguments)
        self._set_fields(positional_arguments, options)
        checking_commands = False

        for line in self.m_doc.split("\n"):
            if line.strip().lower().startswith("commands:"):
                checking_commands = True

            if checking_commands is True:
                ls = [x for x in line.split(" ") if x]

                if len(ls) > 1:
                    command = ls[0].strip()

                    if command not in self.m_commandline_help:
                        self.m_commandline_help[command] = str(" ".join(ls[1:])).strip()

    def set_command_help(self, command, helptext):
        """
        @type command: str
        @type helptext: str
        @return: None
        """
        if not hasattr(self, "m_commandline_help"):
            self.m_commandline_help = {}

        self.m_commandline_help[command] = helptext

    def print_commandline_help(self):
        """
        @return: bool
        """
        if not hasattr(self, "command"):
            console_warning("No command found in Arguments")
            return False

        cmdpath = "\033[95m" + self.get_command_path() + ": \033[0m\033[95m" + str(self.command) + "\033[0m"
        console(cmdpath, plainprint=True)

        if self.command in self.m_commandline_help:
            console(self.m_commandline_help[self.command], color="green", plainprint=True, indent="    ")

        return True

    @staticmethod
    def not_exists(path):
        """
        @type path: str
        @return: None
        """
        return not_exists(path)

    def snake_case_class_name(self, remove_base_class=True):
        """
        @type remove_base_class: bool
        @return: None
        """
        sn = snake_case(self.__class__.__name__)

        if remove_base_class is True:
            sn = sn.replace("_arguments", "")

        return sn.strip()

    def get_command_path(self):
        """
        get_command_path
        """
        name = ""

        if self.m_parents is not None:
            for parent in self.m_parents:
                name += parent.snake_case_class_name()
                name += " "

        name += self.snake_case_class_name()
        return name

    def for_print(self):
        """
        for_print
        """
        return self.as_string()

    def as_string(self):
        """
        as_string
        """
        return get_print_yaml(self.as_yaml())

    def __str__(self):
        """
        __str__
        """
        s = (str(self.__class__).replace(">", "").replace("class ", "").replace("'", "") + " object at 0x%x>" % id(self))
        s += "\n"
        s += consoledict(self.m_reprdict, printval=False)
        return s

    def _set_fields(self, positional, options):
        """
        _parse_arguments
        """
        dictionary = {}

        if positional is not None and options is not None:
            self.positional = positional.copy()
            self.options = options.copy()
            dictionary = positional.copy()
            dictionary.update(options.copy())
            self.m_reprdict = {"positional": positional.copy(),
                               "options": options.copy()}

        for k, v in dictionary.items():
            if hasattr(v, "strip"):
                v = v.strip("'")
                v = v.strip('"')

            setattr(self, str(k), v)

    @staticmethod
    def sort_arguments(arguments):
        """
        @type arguments: dict
        @return: tuple
        """
        opts = {}
        posarg = {}

        for k in arguments:
            try:
                possnum = arguments[k]

                if isinstance(possnum, str):
                    possnum = possnum.replace("'", "").replace('"', '')

                    if "." in possnum:
                        arguments[k] = float(possnum)
                    else:
                        arguments[k] = int(possnum)

            except ValueError:
                pass

            key = k.replace("pa_", "").replace("op_", "").strip()

            if len(key) > 0:
                if k.startswith("pa_"):
                    posarg[k.replace("pa_", "")] = arguments[k]
                elif k.startswith("op_"):
                    opts[k.replace("op_", "")] = arguments[k]
                else:
                    posarg[k] = arguments[k]
            else:
                console("key not matched", key, color="red")

        return opts, posarg

    def set_reprdict_from_attributes(self):
        reprcopy = self.m_reprdict.copy()
        for kd, d in reprcopy.items():
            for k in d.keys():
                if hasattr(self, k):

                    self.m_reprdict[kd][k] = getattr(self, k)

    def as_yaml(self):
        """
        as_yaml
        """
        self.set_reprdict_from_attributes()
        return "---\n" + yaml.dump(self.m_reprdict, default_flow_style=False)

    def from_yaml_file(self, file_path):
        """
        @type file_path: str, None
        @return: None
        """
        if file_path is None:
            raise AssertionError("file_path is None")

        if exists(file_path):
            self.from_yaml(open(file_path).read())
        else:
            raise AssertionError("File not found: " + file_path)

    def from_yaml(self, yamldata):
        """
        @type yamldata: str
        @return: None
        """
        self.m_reprdict = yaml.load(yamldata)


class BaseArguments(Arguments):
    """
    BaseArguments
    """
    def __init__(self, doc, validateschema, parent=None):
        """
        @type doc: str, unicode
        @type validateschema: Schema, None
        @type parent: Arguments, None
        @return: None
        """
        argvalue = None
        yamlstr = None
        yamlfile = None
        parse_arguments = True
        persistoption = False
        alwaysfullhelp = True
        version = None

        # noinspection PyUnusedLocal
        args = []

        if not hasattr(self, "validcommands"):
            self.validcommands = []

        super().__init__(doc, validateschema, argvalue, yamlstr, yamlfile, parse_arguments, persistoption, alwaysfullhelp, version, parent)

    def validcommand(self, cmd):
        """
        @type cmd: str, unicode
        @return: None
        """
        cmd = cmd.strip()

        if self.validcommands is None:
            return cmd

        if cmd.startswith("-"):
            return cmd

        if len(self.validcommands) > 0:
            if cmd.lower() not in self.validcommands:
                raise SchemaError("tool", errors=cmd + ": command not found")

        return cmd
