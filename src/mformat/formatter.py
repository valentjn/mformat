#!/usr/bin/python3

from __future__ import annotations

from .parser import AstNode

def formatAst(ast: AstNode) -> str:
  code = (ast.token.code if ast.token is not None else "")
  code += "".join(formatAst(x) for x in ast.children)
  return code
