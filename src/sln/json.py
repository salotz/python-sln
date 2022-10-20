"""Module providing a convenience functions and CLI for converting to
JSON.
"""

import argparse
from pathlib import Path
import errno
import os
import sys
import json

from sln import Parser

__all__ = ["parse_to_json"]

def parse_to_json(sln_text: str) -> str:
    """Convert raw sln text to JSON text.

    Args:
        sln_text: The text to convert to JSON

    Returns:
        json_text: The resulting JSON

    """

    return json.dumps(
        Parser(
            sln_text
        ).parse_to_string()
    )

class Cli:

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Convert an SLN file to JSON. Outputs to stdout.",
        )

        self.parser.add_argument(
            "sln_file",
            type=Path,
            help="The SLN file path to convert",
        )

    def parse_args(self):
        args = self.parser.parse_args()
        fpath = Path(args.sln_file)

        return {
            'sln_file' : fpath,
        }

    def run(self):

        args = self.parse_args()

        sln_text = args['sln_file'].read_text()

        json_text = parse_to_json(sln_text)

        sys.stdout.write(json_text)

def cli():
    Cli().run()


if __name__ == "__main__":

    cli()
