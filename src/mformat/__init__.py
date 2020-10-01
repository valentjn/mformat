#!/usr/bin/python3

from __future__ import annotations
import argparse
import os
import sys
from typing import List

from .tokenizer import Tokenizer
from .parser import parseTokens
from .formatter import formatAst

def formatFile(filePath: str) -> str:
  with open(filePath, "r") as f: code = f.read()
  return formatCode(code)

def formatCode(code: str) -> str:
  tokenizer = Tokenizer()
  tokens = tokenizer.tokenizeCode(code)
  ast = parseTokens(tokens)
  formattedCode = formatAst(ast)
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
