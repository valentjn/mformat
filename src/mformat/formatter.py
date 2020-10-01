#!/usr/bin/python3

from __future__ import annotations

from .parser import AstNode
from .settings import Settings

def formatAst(ast: AstNode, settings: Settings) -> str:
  return str(ast)
