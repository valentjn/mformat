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
from typing import Any, Dict, List, Optional

from .formatter import formatAst
from .tokenizer import Tokenizer
from .parser import parseTokens
from .settings import Settings

def formatFile(filePath: str, dictSettings: Dict[str, Any] = {}) -> str:
  with open(filePath, "r") as f: code = f.read()
  settings = Settings()
  settings.searchAndLoad(filePath)
  settings.applyDict(dictSettings)
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
  defaultSettings = vars(Settings())

  for settingMetaData in Settings.metaData:
    name, type_ = settingMetaData.name, settingMetaData.type_

    if type_ == bool:
      description = settingMetaData.description
      noDescription = settingMetaData.noDescription
      assert noDescription is not None

      if defaultSettings[name]:
        description += " (default)"
      else:
        noDescription += " (default)"

      parser.add_argument(f"--{name}", action="store_true", dest=name,
          default=None, help=description)
      parser.add_argument(f"--no{name[0].upper()}{name[1:]}", action="store_false", dest=name,
          default=None, help=noDescription)
    else:
      parser.add_argument(f"--{name}", type=settingMetaData.type_,
          metavar=settingMetaData.type_.__name__.upper(),
          help=f"{settingMetaData.description} (default: {repr(defaultSettings[name])})")

  parser.add_argument("path", metavar="PATH", help="Path to *.m source file")
  args = parser.parse_args()

  settingNames = [x.name for x in Settings.metaData]
  dictSettings = {x : y for x, y in vars(args).items() if (x in settingNames) and (y is not None)}

  if os.path.isdir(args.path):
    filePaths: List[str] = []

    for rootDirPath, folderNames, fileNames in os.walk(args.path):
      folderNames.sort()
      filePaths.extend(os.path.join(rootDirPath, x) for x in fileNames if x.endswith(".m"))
  else:
    filePaths = [args.path]

  for filePath in filePaths:
    print(f"Processing '{filePath}'...", file=sys.stderr)
    code = formatFile(filePath, dictSettings)
    print(code)
