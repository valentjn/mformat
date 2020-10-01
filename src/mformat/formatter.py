#!/usr/bin/python3

from __future__ import annotations

from .parser import AstNode
from .settings import Settings

def formatAst(ast: AstNode, settings: Settings) -> str:
  code = (ast.token.code if ast.token is not None else "")
  code += "".join(formatAst(x, settings) for x in ast.children)
  return code
