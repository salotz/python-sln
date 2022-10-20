# Python SLN Parser

SLN is the Scopes List Notation.

See the reference
[here](https://scopes.readthedocs.io/en/latest/dataformat/).

SLN is similar to s-expressions from lisps but with Pythonic
indentation/whitespace extensions.

The preferred file extension is `*.sln`.

SLN is the textual notation for the
[Scopes](https://sr.ht/~duangle/scopes/) programming language and the
[MajorEO](https://hg.sr.ht/~duangle/majoreo) package manager.

## Installing

```sh
pip install git+https://github.com/salotz/python-sln.git
```

## Usage

See the `examples` folder for some examples of using the modules in
your code.

There is also an executable available for conversion to JSON that
sends the JSON to stdout:

```sh
sln-to-json file.sln
```

This is currently not implemented to handle very large files so use
with caution.

## Developing

Uses `hatch` for the build system so install that.

```sh
  make bumpversion
  make build
  HATCH_INDEX_AUTH=... make publish
```
