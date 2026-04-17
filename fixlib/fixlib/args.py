import argparse
import os
import shutil
import subprocess
from collections import defaultdict
from typing import List, Dict, Any, Union, Callable, Optional, Sequence, Tuple

DEFAULT_ENV_ARGS_PREFIX = "FIX_"


class Namespace(argparse.Namespace):
    def __getattr__(self, item: str) -> Any:
        return None


class _MachineHelpAction(argparse.Action):
    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str = argparse.SUPPRESS,
        default: str = argparse.SUPPRESS,
        help: Optional[str] = None,
    ) -> None:
        super(_MachineHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None,
    ) -> None:
        parser.print_machine_help()  # type: ignore
        parser.exit()


class ArgumentParser(argparse.ArgumentParser):
    # Class variable containing the last return value of parse_args()
    # If parse_args() hasn't been called yet will return None for any
    # attribute.
    args = Namespace()

    def __init__(
        self,
        *args: Any,
        env_args_prefix: str = DEFAULT_ENV_ARGS_PREFIX,
        add_machine_help: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.env_args_prefix = env_args_prefix
        self.add_machine_help = add_machine_help
        self.register("action", "machine_help", _MachineHelpAction)

        if self.add_machine_help:
            self.add_argument(
                "--machine-help",
                action="machine_help",
                help="print machine readable help",
            )

    def print_machine_help(self) -> None:
        pass

    def parse_known_args(  # type: ignore
        self, args: Optional[Sequence[str]] = None, namespace: Optional[Namespace] = None
    ) -> Tuple[Namespace, List[str]]:
        pass


def get_arg_parser(
    add_help: bool = True,
    description: str = "fix",
    env_args_prefix: str = DEFAULT_ENV_ARGS_PREFIX,
) -> ArgumentParser:
    arg_parser = ArgumentParser(description=description, add_help=add_help, env_args_prefix=env_args_prefix)
    return arg_parser


# removed from types in 3.0-3.9: introduced again in 3.10
NoneType = type(None)


def convert(value: Any, type_goal: Union[type, Callable[[Any], Any]]) -> Any:
    if type_goal is NoneType:
        return value
    elif isinstance(type_goal, type):
        try:
            if type_goal in (str, int, float, complex):
                return type_goal(value)
            elif type_goal is bool:
                return value.lower() in ("true", "1", "yes")
            else:
                # don't know how to handle this type
                return value
        except Exception:
            # can not convert value
            return value
    elif callable(type_goal):
        return type_goal(value)


def args_dispatcher(dispatch_to: List[str], use_which: bool, argv: List[str]) -> Dict[str, List[str]]:
    pass
