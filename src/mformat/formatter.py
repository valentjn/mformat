#!/usr/bin/python3

from __future__ import annotations
import copy
import re
from typing import Optional, Tuple

from .parser import AstNode
from .settings import Settings
from .tokenizer import Token



class ArtificialToken(Token):
  startPos = -1

  def __init__(self, code: str, className: str) -> None:
    Token.__init__(self, code, ArtificialToken.startPos, className)



def formatAst(ast: AstNode, settings: Settings) -> str:
  ast = copy.deepcopy(ast)

  removeWhitespaces(ast)
  insertNewlinesBetweenStatements(ast)
  removeSuperfluousSemicolons(ast)
  indent(ast, settings)
  insertWhitespaces(ast, settings)

  code = str(ast)
  code = re.sub(r"([^ ]|^) +$", r"\1", code, flags=re.MULTILINE)

  return code



def removeWhitespaces(node: AstNode) -> None:
  oldChildren = list(node.children)

  for i, child in enumerate(oldChildren[::-1]):
    if child.className in ["lineContinuationComment", "whitespace"]:
      del node.children[len(oldChildren) - i - 1]

  for child in node.children: removeWhitespaces(child)



def insertNewlinesBetweenStatements(ast: AstNode) -> None:
  curStatementNode = ast.goToDescendant("statement")
  if curStatementNode is None: return
  nextStatementNode = curStatementNode.goToNext("statement")

  while nextStatementNode is not None:
    newlineNode = curStatementNode.goToNext("newline")
    numberOfNewlines = 0

    while (newlineNode is not None) and (newlineNode < nextStatementNode):
      numberOfNewlines += 1
      newlineNode = newlineNode.goToNext("newline")

    if (numberOfNewlines == 0) and (str(nextStatementNode) != "\n"):
      curStatementNode.appendNewAstNodeAsChild(ArtificialToken("\n", "newline"))

    curStatementNode = nextStatementNode
    nextStatementNode = nextStatementNode.goToNext("statement")



def removeSuperfluousSemicolons(ast: AstNode) -> None:
  blockNode = ast.goToDescendant("Block")

  while blockNode is not None:
    if blockNode.className == "functionBlock":
      statementNodes = []
    else:
      statementNodes = [blockNode.goToDescendant("statement"), blockNode.children[-1]]

    for statementNode in statementNodes:
      if statementNode is None: continue

      while (semicolonNode := statementNode.goToDescendant("semicolon")) is not None:
        semicolonNode.remove()

    blockNode = blockNode.goToNext("Block")



def indent(node: AstNode, settings: Settings) -> None:
  if node.className == "statement":
    if node.blockDepth is not None:
      indentation = (node.blockDepth * settings.indent) * " "
      index = (1 if (len(node.children) >= 1) and (node.children[0].className == "newline") else 0)
      node.insertNewAstNodeAsChild(index, ArtificialToken(indentation, "whitespace"))
  else:
    for child in node.children: indent(child, settings)



def insertWhitespaces(node: AstNode, settings: Settings) -> None:
  if node.className.endswith("OperatorNode"):
    insertSpaces = (node.children[0].className != "empty")

    if insertSpaces and (node.className == "colonOperatorNode"):
      insertSpaces = not (settings.omitSpaceAroundColon and checkMaximumLengthOfArguments(
            node, settings.omitSpaceAroundColonMaxLength, "colonOperator"))

    if insertSpaces:
      node.insertNewAstNodeAsChild(2, ArtificialToken(" ", "whitespace"))
      node.insertNewAstNodeAsChild(1, ArtificialToken(" ", "whitespace"))
  elif node.className == "commaSeparatedList":
    insertSpaces = not (settings.omitSpaceAfterComma
        and checkMaximumLengthOfArguments(node, settings.omitSpaceAfterCommaMaxLength, "comma"))

    if insertSpaces:
      oldChildren = list(node.children)

      for i, child in enumerate(oldChildren[::-1]):
        if child.className == "comma":
          index = len(oldChildren) - i - 1
          node.insertNewAstNodeAsChild(index + 1, ArtificialToken(" ", "whitespace"))
    else:
      return
  elif node.className in ["keyword", "semicolon"]:
    node.appendNewAstNodeAsChild(ArtificialToken(" ", "whitespace"))

  for child in node.children: insertWhitespaces(child, settings)



def checkMaximumLengthOfArguments(node: AstNode, limit: int, excludeClassName: str) -> bool:
  return all(len(str(child)) <= limit for child in node.children
      if child.className != excludeClassName)
