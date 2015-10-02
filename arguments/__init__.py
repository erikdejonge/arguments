#!/usr/bin/env python3
# coding=utf-8
"""

Usage:
Inherit from baseclass
arguments

Active8 (04-03-15)
license: GNU-GPL2
"""
from __future__ import division, print_function, absolute_import, unicode_literals
from future import standard_library

import os
import sys
import json
import yaml
import pickle
import collections

from fallbackdocopt import docopt, DocoptExit
from os.path import exists, expanduser
from consoleprinter import abort, console, handle_ex, snake_case, get_print_yaml, console_warning, remove_escapecodes, remove_extra_indentation

COMPARABLE, CALLABLE, VALIDATOR, TYPE, DICT, ITERABLE = list(range(6))

MARKER = object()


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
                raise SchemaError('%r.validate(%r) raised %r' % (s, data, x), self._error)

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
        self.doprinthelp = False
        self.m_once = None
        self.write = None
        self.load = None
        self.m_schema = validateschema
        self.m_reprdict = {}
        self.m_doc = ""
        self.__add_parent(parent)
        self.parsedarguments = {}
        self.command = ""

        if not hasattr(self, "validcommands"):
            self.validcommands = []

        if parent is not None:
            if hasattr(parent, "help") and parent.help is True:
                if len(parent.positional["args"]) == 0:
                    print()

        if doc is None:
            # noinspection PyUnresolvedReferences
            import __main__
            console("Arguments first param 'doc' is not set using __main__.__doc__ now", plaintext=True, color='orange')
            triggerword = "usage"
            console(remove_extra_indentation(__main__.__doc__, triggerword), plaintext=True)
            self.m_doc = remove_extra_indentation(__main__.__doc__, triggerword)

        if doc is not None:
            triggerword = "usage"
            newdoc = remove_extra_indentation(doc, triggerword)
            self.m_doc = self.reorder_commandlist(newdoc)

        self.m_argv = argvalue
        self.m_persistoption = persistoption
        self.m_alwaysfullhelp = alwaysfullhelp
        self.m_version = version

        if not hasattr(self, "m_commandline_help"):
            self.m_commandline_help = {}

        self.m_commandline_help_default = {}

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
                    # noinspection PyUnresolvedReferences


                    if self.command and len(self.m_argv) > 1:
                        # noinspection PyUnresolvedReferences
                        if self.m_argv[-2] is self.command and self.command in self.validcommands:
                            self.print_commandline_help(usageonly=False)
                        else:
                            if self.doprinthelp:
                                print("doprinthelp")
                                self.print_commandline_help(usageonly=False)

                                if self.m_parents is not None:
                                    raise SystemExit(0)
                    else:
                        self.print_commandline_help(usageonly=False)
                    raise SystemExit(1)
                else:
                    if exdoc is True:
                        print(self.get_usage_from_mdoc())
                        raise SystemExit(1)

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

    @staticmethod
    def reorder_commandlist(doc):
        """
        @type doc: str
        @return: None
        """
        cmdbuffering = False
        commands = {}
        newdoc = ""
        end_of_doc = []
        end_of_doc_markers = ["author", "project", "created"]
        for line in doc.split("\n"):
            eofm = False
            for marker in end_of_doc_markers:
                if line.replace(" ", "").strip().startswith(marker+":"):
                    eofm = True
            if eofm is True:
                end_of_doc.append(line)
            else:
                if cmdbuffering is True and line.find(" ")==0:
                    ls = line.strip().split()

                    if len(ls) > 0 and len(ls[0].strip()) > 0:
                        commands[ls[0]] = " ".join(ls[1:])
                else:
                    newdoc += line
                    newdoc += "\n"

                if "commands:" in line.lower():
                    cmdbuffering = True

        commandkeys = sorted(commands.keys())
        longest = 0

        for cmd in commandkeys:
            if len(cmd) > longest:
                longest = len(cmd)
        newdoc = newdoc.strip()+"\n"
        for cmd in commandkeys:
            if len(commands[cmd].strip()) > 0:
                newdoc += " " * 4
                newdoc += cmd +" : "
                newdoc += " " * 2
                newdoc += " " * (longest - len(cmd))
                newdoc += commands[cmd].strip()
                newdoc += "\n"
        if len(end_of_doc) > 0:
            newdoc = newdoc.strip()+"\n\n"
            for line in end_of_doc:
                newdoc += line+"\n"
        return newdoc.strip()

    def get_usage_from_mdoc(self):
        """
        get_usage_from_mdoc
        """
        usage = self.m_doc.strip().split("Usage:")

        if len(usage) > 1:
            usage = "\033[34mUsage:\033[34m" + usage[1]

        return "\n".join(usage.strip().split("\n")[:2]) + "\033[0m"

    def parse_arguments(self, schema=True):
        """
        @type schema: Schema
        @return: None
        """
        arguments = None

        if schema is not None:
            self.m_schema = schema

        if self.load is None:
            if self.m_persistoption is True:
                optsplit = self.m_doc.split("Options:")
                optsplit[0] += "Options:\n"
                optsplit[0] += """    -w --write=<writeymlpath>\tWrite arguments yaml file.\n    -l --load=<loadymlpath>\tLoad arguments yaml file."""
                self.m_doc = "".join(optsplit)
                console(optsplit)
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

                if self.m_parents:
                    for parent in self.m_parents:
                        if parent.command:
                            # pass
                            # console_warning("removed parent")
                            self.m_argv.remove(parent.command)

                arguments = dict(docopt(self.m_doc, self.m_argv, options_first=False, version=self.m_version))
                self.parsedarguments = arguments.copy()

                if "--help" in [s for s in arguments.keys() if isinstance(s, str)] or "-h" in [s for s in arguments.keys() if isinstance(s, str)]:
                    self.doprinthelp = True
            except DocoptExit:
                if self.m_alwaysfullhelp is True:
                    for sarg in list(sys.argv):
                        if "-h" in sarg or "--help" in sarg:
                            self.print_commandless_help()
                            exit(1)
                    else:

                        usage = self.get_usage_from_mdoc()
                        print("\033[34m" + usage + "\033[0m")

                    raise SystemExit(0)
                else:
                    if "-h" in self.m_argv or "--help" in self.m_argv:
                        self.print_commandless_help()

                        raise SystemExit(0)
                    else:
                        raise

            k = ""
            try:
                if isinstance(arguments, dict):
                    for k in arguments:
                        trypath = False

                        if isinstance(arguments[k], str):
                            trypath = "~" in arguments[k] or "/" in arguments[k]

                        if trypath is False:
                            trypath = "folder" in k or "path" in k

                        if trypath:
                            if hasattr(arguments[k], "replace"):
                                arguments[k] = arguments[k].replace("~", expanduser("~"))

                                if arguments[k].strip() == ".":
                                    arguments[k] = os.getcwd()

                                if "./" in arguments[k].strip():
                                    arguments[k] = os.path.abspath(arguments[k])

                                if arguments[k].rstrip("/").strip() != "/":
                                    arguments[k] = arguments[k].rstrip("/").strip()

                            if hasattr(arguments[k], "strip") and arguments[k].strip() == "":
                                arguments[k] = "/"

            except AttributeError as e:
                console("Attribute error:" + k.strip(), "->", str(e), color="red")

                if isinstance(arguments, dict):
                    for k in arguments:
                        console(k.strip(), color="red")

                handle_ex(e)
        else:
            if isinstance(self.load, str) and self.load is not None:
                loaded_arguments = yaml.load(open(str(self.load)))
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
            abort(name, "".join([x for x in e.errors if x]))
            print()
            print(self.m_doc.strip())

            raise

        options, positional_arguments = self.sort_arguments(arguments)
        self._set_fields(positional_arguments, options)
        checking_commands = False

        for line in self.m_doc.split("\n"):
            if line.strip().lower().startswith("commands:"):
                checking_commands = True

            if checking_commands is True:
                ls = [x for x in line.split() if x]

                if len(ls) > 1:
                    command = ls[0].strip()

                    if command not in self.m_commandline_help and command not in ["author", "date", "project"]:
                        if command not in self.m_commandline_help_default:
                            self.m_commandline_help_default[command] = str(" ".join(ls[1:])).strip()

    def print_commandless_help(self):
        """
        print_commandless_help
        """
        doc_help = self.m_doc.strip().split("\n")

        if len(doc_help) > 0:
            print("\033[33m--\033[0m")
            print("\033[34m" + doc_help[0] + "\033[0m")

            asp = "author  :"
            doc_help_rest = "\n".join(doc_help[1:])

            if asp in doc_help_rest:
                doc_help_rest = doc_help_rest.split("author  :")

                if len(doc_help_rest) > 1:
                    print("\n\033[33m" + doc_help_rest[0].strip() + "\n")
                    print("\033[37m" + asp + doc_help_rest[1] + "\033[0m")
                else:
                    print(doc_help_rest)
            else:
                print(doc_help_rest)

            print("\033[33m--\033[0m")
        else:
            print("\033[31mERROR, doc should have more then one line\033[0m")
            print(self.m_doc)

    def set_command_help(self, command, helptext):
        """
        @type command: str
        @type helptext: str
        @return: None
        """
        if not hasattr(self, "m_commandline_help"):
            self.m_commandline_help = {}

        self.m_commandline_help[command] = helptext

    def print_commandline_help(self, usageonly=False):
        """
        @type usageonly: bool
        @return: None
        """
        if not hasattr(self, "command"):
            console_warning("No command found in Arguments")
            return False

        if usageonly is True:
            usage = self.get_usage_from_mdoc()
        else:
            usage = self.m_doc

        have_command = False

        for line in usage.split("\n"):
            # noinspection PyUnresolvedReferences
            if self.command in self.m_commandline_help and line.strip().startswith(self.command):
                have_command = True
                break

        if have_command:
            for line in usage.split("\n"):
                ls = line.split()

                # noinspection PyUnresolvedReferences
                if self.command in self.m_commandline_help and line.strip().startswith(self.command):
                    print("\033[32m" + line + "\033[0m")

                    if len(ls) > 0:
                        ls = [x for x in ls if x]

                        if ls:
                            # noinspection PyUnresolvedReferences
                            if ls[0] == self.command:
                                js = remove_escapecodes("".join(line.split(ls[0], maxsplit=1)))
                                lenjs = len(remove_escapecodes(ls[0]).strip())

                                if lenjs < 3:
                                    lenjs = 1

                                spaces = (len(js) - len(js.strip())) + lenjs
                                lineorg = line

                                # noinspection PyUnresolvedReferences
                                line = "\033[36m" + self.m_commandline_help[self.command] + "\033[0m"

                                # line = line.replace(ls[0], "", 1).strip()

                                if line not in lineorg:
                                    print((spaces * " ") + line)

                elif line.strip().startswith(self.command + " "):
                    print("\033[32m" + line + "\033[0m")
                else:
                    print(line)
        else:
            self.print_commandless_help()

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

    def as_string(self):
        """
        as_string
        """
        return get_print_yaml(self.as_yaml())

    def for_print(self):
        """
        for_print
        """
        s = "\033[34m" + self.get_object_info() + "\033[0m"
        s += "\n"
        s += self.as_string()
        return s

    def get_subclass(self):
        """
        get_subclass
        """

        strbldr = """
            class IArguments(Arguments):
                \"\"\"
                IArguments
                \"\"\"
                def __init__(self, doc=None, validateschema=None, argvalue=None, yamlstr=None, yamlfile=None, parse_arguments=True, persistoption=False, alwaysfullhelp=False, version=None, parent=None):
                    \"\"\"
                    @type doc: str, None
                    @type validateschema: Schema, None
                    @type yamlfile: str, None
                    @type yamlstr: str, None
                    @type parse_arguments: bool
                    @type argvalue: str, None
                    @return: None
                    \"\"\"
        """
        strbldr = remove_extra_indentation(strbldr)
        strbldr += "\n"
        self.set_reprdict_from_attributes()
        strbldr += self.write_members()
        strbldr += 8 * " " + "super().__init__(doc, validateschema, argvalue, yamlstr, yamlfile, parse_arguments, persistoption, alwaysfullhelp, version, parent)\n\n"
        strbldr2 = """
            class IArguments(Arguments):
                \"\"\"
                IArguments
                \"\"\"
                def __init__(self, doc):
                    \"\"\"
                    __init__
                    \"\"\"
        """
        strbldr2 = remove_extra_indentation(strbldr2)
        strbldr2 += "\n"
        strbldr2 += self.write_members()
        strbldr2 += 8 * " " + "super().__init__(doc)\n\n"
        return strbldr2

        # return strbldr + "\n\n" + strbldr2
    def write_members(self):
        """
        write_members
        """
        s = ""
        objattributes = list(self.m_reprdict["positional"].keys())
        objattributes.extend(list(self.m_reprdict["options"].keys()))
        objattributes.sort()

        for objattr in objattributes:
            s += 8 * " " + "self." + objattr + "="

            if objattr in self.m_reprdict["positional"]:
                td = self.m_reprdict["positional"]

                if isinstance(td[objattr], int):
                    s += "0"
                elif isinstance(td[objattr], float):
                    s += "0.0"
                elif isinstance(td[objattr], bool):
                    s += "False"
                else:
                    s += '""'
            else:
                s += "False"

            s += "\n"

        return s

    def __str__(self):
        """
        __str__
        """

        if not sys.stdout.isatty():
            self.set_reprdict_from_attributes()
            value = self.m_reprdict
            s = self.get_objectdata_json(str(value))
        else:
            s = "\033[37m" + self.get_subclass() + "\033[0m"
            s += self.get_object_info()
            s += "\n"
            s += get_print_yaml(self.as_yaml())

        return s

    def get_objectdata_json(self, value):
        """
        @type value: str
        @return: str
        """
        od = collections.OrderedDict()
        s = "{} class 0x{:x}".format(self.__class__.__name__, id(self))
        od["o"] = s
        od["v"] = str(value)
        return json.dumps(od)

    def get_object_info(self):
        """
        Returns object info in following form <module.class object at address>
        """
        objectinfo = str(self.__class__).replace(">", "")
        objectinfo = objectinfo.replace("class ", "")
        objectinfo = objectinfo.replace("'", "")
        objectinfo += " object at 0x%x>" % id(self)
        return objectinfo

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
        """
        set_reprdict_from_attributes
        """
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

    def save(self, path):
        """
        @type path: str
        @return: None
        """
        dirname = os.path.dirname(path)

        if len(dirname) > 0:
            if not os.path.exists(dirname):
                os.makedirs(dirname, exist_ok=True)

        self.set_reprdict_from_attributes()
        pickle.dump(self.m_reprdict, open(path, "wb"))

    def load(self, path):
        """
        @type path: str
        @return: None
        """
        if not os.path.exists(path):
            raise FileExistsError(path)

        self.m_reprdict = pickle.load(open(path, "rb"))


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
                raise SchemaError("tool", errors=cmd + " command not found")

        return cmd


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
                if not os.path.basename(fp) == exname:
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
                os.removedirs(rootpath)

    return len(list(os.walk(dirpath)))


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


def not_exists(path):
    """
    @type path: str
    @return: None
    """
    return not exists(path)


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

standard_library.install_aliases()
