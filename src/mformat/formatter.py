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
  insertNewlines(ast)
  indent(ast, settings)
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



def insertNewlines(ast: AstNode) -> None:
  nodeStack = [ast]
  foundNewlineSinceLastStatement = True

  while len(nodeStack) > 0:
    node = nodeStack.pop()
    nodeStack.extend(node.children[::-1])

    if node.className == "statement":
      if foundNewlineSinceLastStatement or (str(node) == "\n"):
        foundNewlineSinceLastStatement = False
      else:
        node.insertNewAstNodeAsChild(0, Token("\n", -1, "newline"))
    elif node.className == "newline":
      foundNewlineSinceLastStatement = True



def indent(node: AstNode, settings: Settings) -> None:
  if node.className == "statement":
    if node.blockDepth is not None:
      indentation = (node.blockDepth * settings.indent) * " "
      index = (1 if (len(node.children) >= 1) and (node.children[0].className == "newline") else 0)
      node.insertNewAstNodeAsChild(index, Token(indentation, -1, "whitespace"))
  else:
    for child in node.children: indent(child, settings)



def insertWhitespaces(node: AstNode, settings: Settings) -> None:
  if node.className.endswith("OperatorNode"):
    insertSpaces = (node.children[0].className != "empty")

    if insertSpaces and (node.className == "colonOperatorNode"):
      insertSpaces = not (settings.omitSpaceAroundColon and checkMaximumLengthOfArguments(
            node, settings.omitSpaceAroundColonMaxLength, "colonOperator"))

    if insertSpaces:
      node.insertNewAstNodeAsChild(2, Token(" ", -1, "whitespace"))
      node.insertNewAstNodeAsChild(1, Token(" ", -1, "whitespace"))
  elif node.className == "commaSeparatedList":
    insertSpaces = not (settings.omitSpaceAfterComma
        and checkMaximumLengthOfArguments(node, settings.omitSpaceAfterCommaMaxLength, "comma"))

    if insertSpaces:
      oldChildren = list(node.children)

      for i, child in enumerate(oldChildren[::-1]):
        if child.className == "comma":
          index = len(oldChildren) - i - 1
          node.insertNewAstNodeAsChild(index + 1, Token(" ", -1, "whitespace"))
    else:
      return
  elif node.className in ["keyword", "semicolon"]:
    node.appendNewAstNodeAsChild(Token(" ", -1, "whitespace"))

  for child in node.children: insertWhitespaces(child, settings)



def checkMaximumLengthOfArguments(node: AstNode, limit: int, excludeClassName: str) -> bool:
  return all(len(str(child)) <= limit for child in node.children
      if child.className != excludeClassName)
