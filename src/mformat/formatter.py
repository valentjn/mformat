#!/usr/bin/python3

from __future__ import annotations
import copy
import re

from .parser import AstNode
from .settings import Settings
from .tokenizer import Token

def formatAst(ast: AstNode, settings: Settings) -> str:
  ast = copy.deepcopy(ast)

  removeWhitespaces(ast)
  insertWhitespaces(ast, settings)

  code = str(ast)
  code = re.sub(r"([^ ]) +$", r"\1", code, flags=re.MULTILINE)

  return code

def removeWhitespaces(node: AstNode) -> None:
  oldChildren = list(node.children)

  for i, child in enumerate(oldChildren[::-1]):
    if child.className in ["lineContinuationComment", "whitespace"]:
      del node.children[len(oldChildren) - i - 1]

  for child in node.children: removeWhitespaces(child)

def insertWhitespaces(node: AstNode, settings: Settings) -> None:
  if node.className.endswith("OperatorNode"):
    insertSpaces = (node.children[0].className != "empty")

    if insertSpaces and (node.className == "colonOperatorNode"):
      insertSpaces = not (settings.omitSpaceAroundColon and checkMaximumLengthOfArguments(
            node, settings.omitSpaceAroundColonMaxLength, "colonOperator"))

    if insertSpaces:
      node.children.insert(2, AstNode(Token(" ", -1, "whitespace"), node))
      node.children.insert(1, AstNode(Token(" ", -1, "whitespace"), node))
  elif node.className == "commaSeparatedList":
    insertSpaces = not (settings.omitSpaceAfterComma
        and checkMaximumLengthOfArguments(node, settings.omitSpaceAfterCommaMaxLength, "comma"))

    if insertSpaces:
      oldChildren = list(node.children)

      for i, child in enumerate(oldChildren[::-1]):
        if child.className == "comma":
          index = len(oldChildren) - i - 1
          node.children.insert(index + 1, AstNode(Token(" ", -1, "whitespace"), node))
    else:
      return
  elif node.className in ["keyword", "semicolon"]:
    node.appendNewAstNodeAsChild(Token(" ", -1, "whitespace"))

  for child in node.children: insertWhitespaces(child, settings)

def checkMaximumLengthOfArguments(node: AstNode, limit: int, excludeClassName: str) -> bool:
  return all(len(str(child)) <= limit for child in node.children
      if child.className != excludeClassName)
