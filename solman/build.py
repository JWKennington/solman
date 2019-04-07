"""Build script"""


import argparse
import pathlib
import re
import typing


def solns_root(solutions_subdir: str='solutions') -> pathlib.Path:
    return pathlib.Path(__file__).parent / solutions_subdir


def find_solutions_groups(pattern: typing.Union[str, re.Pattern]=None) -> typing.List[pathlib.Path]:
    root = solns_root()
    if pattern is None:
        pattern = re.compile('') # match all
    elif isinstance(pattern, str):
        pattern = re.compile(pattern)

    soln_groups = [x for x in root.iterdir() if x.is_dir()]
    return [g for g in soln_groups if pattern.match(g.name)]


def main():
    args = parse()
    # TODO compile things


def parse():
    pass # TODO setup commandline args


if __name__ == '__main__':
    main()

