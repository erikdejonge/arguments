# coding=utf-8
"""
arguments
erik@a8.nl (04-03-15)
license: GNU-GPL2
"""

import os
import yaml
from os.path import exists, expanduser
from docopt import docopt
from schema import Schema, SchemaError, Or, Optional, Use
from console_utils import console, handle_ex


class Arguments(object):
    """
    Argument dict to boject
    @DynamicAttrs
    """
    def __init__(self, doc=None, validate_schema=True, yamlfile=None, parse_arg=True, verbose=None):
        """
        @type yamlfile: str, unicode, None
        @type verbose: bool, None
        @return: None
        """
        self.verbose = verbose
        self.once = None
        self.write = None
        self.load = None
        setattr(self, "posarg1", None)
        self.validate_schema = validate_schema
        self.reprdict = {}
        self.doc = doc

        if yamlfile:
            self.from_yaml_file(yamlfile)
        elif parse_arg is True:
            self.parse_args(validate_schema)

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

    @staticmethod
    def colorize_for_print(v):
        """
        @type v: str, unicode
        @return: None
        """
        s = ""
        v = v.strip()

        if v == "false":
            v = "False"
        elif v == "true":
            v = "True"

        num = v.isdigit()

        if not num:
            try:
                v2 = v.replace("'", "").replace('"', "")
                num = float(v2)
                num = True
                v = v2
            except ValueError:
                pass

        ispath = exists(v)

        if num is True:
            s += "\033[93m" + v + "\033[0m"
        elif ispath is True:
            s += "\033[35m" + v + "\033[0m"
        elif v == "False":
            s += "\033[31m" + v + "\033[0m"
        elif v == "True":
            s += "\033[32m" + v + "\033[0m"
        else:
            s += "\033[33m" + v + "\033[0m"

        return s

    def dictionary_for_console(self, argdict, indent=""):
        """
        @type argdict: dict
        @type indent: str
        @return: sp
        """
        keys = argdict.keys()
        keys.sort(key=lambda x: len(x))
        sp = ""
        lk = 0
        ls = []

        for k in keys:
            s = indent + "\033[36m" + k + "`: " + "\033[0m"
            v = str(argdict[k]).strip()
            s += self.colorize_for_print(v)
            ls.append((len(k), s))

            if len(k) > lk:
                lk = len(k)

        for lns, s in ls:
            s = s.replace("`", " " * (1 + (lk - lns)))
            sp += s

        return sp

    def get_print_yaml(self, yamlstring):
        """
        @type yamlstring: str, unicode
        @return: None
        """
        s = ""

        for i in yamlstring.split("\n"):
            ls = [x for x in i.split(":") if x]
            cnt = 0

            if len(ls) > 1:
                for ii in ls:
                    if cnt == 0:
                        s += "\033[36m" + ii + ": " + "\033[0m"
                    else:
                        s += self.colorize_for_print(ii)

                    cnt += 1
            else:
                if i.strip().startswith("---"):
                    s += "\033[95m" + i + "\033[0m"
                else:
                    s += "\033[91m" + i + "\033[0m"

            s += "\n"

        return s.strip()

    @staticmethod
    def not_exists(path):
        """
        @type path: str, unicode
        @return: None
        """
        return not exists(path)

    def for_print(self):
        """
        for_print
        """
        return self.get_print_yaml(self.as_yaml())

    def __str__(self):
        """
        __str__
        """
        return self.__repr__()

    def _set_fields(self, positional, options):
        """
        _parse_args
        """
        dictionary = {}

        if positional and options:
            self.positional = positional.copy()
            self.options = options.copy()
            dictionary = positional.copy()
            dictionary.update(options.copy())
            self.reprdict = {"positional": positional.copy(),
                             "options": options.copy()}

        def _traverse(key, element):
            """
            @type key: str, unicode
            @type element: str, unicode
            @return: None
            """
            if isinstance(element, dict):
                return key, "dicts not allowed"
            else:
                return key, element

        object_dict = dict(_traverse(k, v) for k, v in dictionary.iteritems())
        self.__dict__.update(object_dict)

    @staticmethod
    def sort_arguments(arguments):
        """
        @type arguments: dict
        @return: tuple
        """
        opts = {}
        posarg = {}

        for k in arguments:
            key = k.replace("pa_", "").replace("op_", "").strip()

            if len(key) > 0:
                if k.startswith("pa_"):
                    posarg[k.replace("pa_", "")] = arguments[k]

                if k.startswith("op_"):
                    opts[k.replace("op_", "")] = arguments[k]
            try:
                possnum = arguments[k]

                if isinstance(possnum, str):
                    if "." in possnum:
                        arguments[k] = float(possnum)
                    else:
                        arguments[k] = int(possnum)

            except ValueError:
                pass

        return opts, posarg

    def parse_args(self, validate_schema=True):
        """
        @type validate_schema: bool
        @return: None
        """
        if validate_schema is not None:
            self.validate_schema = validate_schema

        if self.load is None:
            if self.doc is None:
                self.doc = __doc__

            self.doc += """  -w --write=<writeymlpath>\tWrite arguments yaml file.
  -l --load=<loadymlpath>\tLoad arguments yaml file.
"""
            arguments = dict(docopt(self.doc))
            k = ""
            try:
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
                for k in arguments:
                    console(k.strip(), color="red")

                handle_ex(e)
        else:
            loaded_arguments = yaml.load(open(self.load))
            arguments = {}
            for k in loaded_arguments["options"]:
                arguments["op_" + k] = loaded_arguments["options"][k]
            for k in loaded_arguments["positional"]:
                arguments["pa_" + k] = loaded_arguments["positional"][k]
        try:
            schema = Schema({"pa_command": Or(None, str),
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

            if "--" in arguments:
                del arguments["--"]

            arguments = dict((x.replace("<", "pa_").replace(">", "").replace("--", "op_").replace("-", "_"), y) for x, y in arguments.viewitems())

            if self.validate_schema is True:
                arguments = schema.validate(arguments)
        except SchemaError as e:
            if "lambda" in str(e):
                err = "Error: giturl should end with .git"
            else:
                err = ""

            handle_ex(e, extra_info=err)

        if self.verbose:
            print self.arguments_for_console(arguments)

        options, positional_arguments = self.sort_arguments(arguments)
        self._set_fields(positional_arguments, options)

    def arguments_for_console(self, arguments):
        """
        @type arguments: dict
        @return: None
        """
        s = ""
        opts, posarg = self.sort_arguments(arguments)
        newline = False

        if posarg:
            s += "\033[91mPositional arguments:\033[0m"
            s += self.dictionary_for_console(posarg, "\n  ")
            newline = True

        if opts:
            if newline:
                s += "\n\n"

            s += "\033[91mOptions:\033[0m"
            s += self.dictionary_for_console(opts, "\n  ")

        return s + "\n"

    def as_yaml(self):
        """
        as_yaml
        """
        return "---\n" + yaml.dump(self.reprdict, default_flow_style=False)

    def from_yaml_file(self, file_path):
        """
        @type file_path: str, unicode
        @return: None
        """
        if exists(file_path):
            self.from_yaml(open(file_path).read())
        else:
            raise AssertionError("File not found: " + file_path)

    def from_yaml(self, yamldata):
        """
        @type yamldata: str, unicode
        @return: None
        """
        self.reprdict = yaml.load(yamldata)
