# coding=utf-8
"""
arguments
Active8 (04-03-15)
license: GNU-GPL2
"""

import arguments


class BaseArguments(arguments.Arguments):
    """
    Default initializations for this program (no schema validateion)
    """
    def __init__(self, doc):
        """
        @type doc: str, unicode
        @return: None
        """
        argvalue = None
        yamlstr = None
        yamlfile = None
        parse_arguments = True
        persistoption = False
        alwaysfullhelp = False
        validateschema = None
        version = "Argument classbased example 0.1.1"
        super().__init__(doc, validateschema, argvalue, yamlstr, yamlfile, parse_arguments, persistoption, alwaysfullhelp, version)


class MainArguments(BaseArguments):
    """
    First level of the commandline hierarchy
    """
    def __init__(self):
        doc = """
            Some tools.
            Usage:
                classbased.py [options] [--] <tool> [<args>...]

            Options:
                -h --help       Show this screen..
                -v --verbose    Verbose mode.

            Commands:
                tool1   Tool1 description here
                tool2   Tool2 ...
        """
        self.tool = ""
        super().__init__(doc)


class Tool1Arguments(BaseArguments):
    """
    Tool1, second level of the commandline hierarchy
    """
    def __init__(self):
        doc = """
            Tool 1
            Usage:
                classbased.py tool1 [options] [--] <command> [<args>...]

            Options:
                -h --help       Show this screen..
                -v --verbose    Verbose mode.

            Commands:
                run     Run the tool
                build   Build the tool
        """
        self.command = ""

        super().__init__(doc)


class Tool2Arguments(BaseArguments):
    """
    Tool2, second level of the commandline hierarchy
    """
    def __init__(self):
        doc = """
            Tool 2
            Usage:
                classbased.py tool2 [options] [--] <command> [<args>...]

            Options:
                -h --help       Show this screen..
                -v --verbose    Verbose mode.

            Commands:
                upload  Upload something
                delete  Delete something
        """
        self.command = ""
        super().__init__(doc)


def main():
    """
    main
    """
    args = MainArguments()

    if args.tool.lower() == "tool1":
        args = Tool1Arguments()
    elif args.tool.lower() == "tool2":
        args = Tool2Arguments()
    else:
        print("Unknown tool", args.tool)

    print(args)


if __name__ == "__main__":
    main()
