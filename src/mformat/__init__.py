#!/usr/bin/python

# Copyright (C) 2020 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations
import argparse
import os
import sys
from typing import List, Optional

from .formatter import formatAst
from .tokenizer import Tokenizer
from .parser import parseTokens
from .settings import Settings

def formatFile(filePath: str) -> str:
  with open(filePath, "r") as f: code = f.read()
  settings = Settings()
  settings.searchAndLoad(filePath)
  return formatCode(code, settings)

def formatCode(code: str, settings: Optional[Settings] = None) -> str:
  if settings is None: settings = Settings()
  tokenizer = Tokenizer()
  tokens = tokenizer.tokenizeCode(code)
  ast = parseTokens(tokens, settings)
  formattedCode = formatAst(ast, settings)
  return formattedCode

def main() -> None:
  parser = argparse.ArgumentParser(description="Format *.m files (MATLAB/Octave source code")
  parser.add_argument("path", metavar="PATH", help="path to *.m source file")
  args = parser.parse_args()

  if os.path.isdir(args.path):
    filePaths: List[str] = []

    for rootDirPath, folderNames, fileNames in os.walk(args.path):
      folderNames.sort()
      filePaths.extend(os.path.join(rootDirPath, x) for x in fileNames if x.endswith(".m"))
  else:
    filePaths = [args.path]

  for filePath in filePaths:
    print(f"Processing '{filePath}'...", file=sys.stderr)
    code = formatFile(filePath)
    print(code)
