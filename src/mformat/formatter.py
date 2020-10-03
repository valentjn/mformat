#!/usr/bin/python3

from __future__ import annotations
import copy
import re
from typing import Optional, Tuple

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
  node, _ = goToChild(ast, "statement")
  numberOfNewlines = -1

  while node is not None:
    if (numberOfNewlines == 0) and (str(node) != "\n"):
      node.insertNewAstNodeAsChild(0, Token("\n", -1, "newline"))
      insertedNewline = True
    else:
      insertedNewline = False

    node, numberOfNewlines = goToNextNode(node, "statement", "newline")
    if insertedNewline: numberOfNewlines -= 1



def goToPrevNode(node: AstNode, nextNodeClassName: str, nodeToCountClassName: Optional[str] = None,
      nodeCounter: int = 0) -> Tuple[Optional[AstNode], int]:
  return goToNextNode(node, nextNodeClassName, nodeToCountClassName, nodeCounter, True)

def goToNextNode(node: AstNode, nextNodeClassName: str, nodeToCountClassName: Optional[str] = None,
      nodeCounter: int = 0, reverse: bool = False) -> Tuple[Optional[AstNode], int]:
  nextNode, nodeCounter = goToChild(node, nextNodeClassName,
      nodeToCountClassName, nodeCounter, reverse, True)
  if nextNode is not None: return nextNode, nodeCounter

  while node.parent is not None:
    prevNode = node
    node = node.parent
    nodeIndex = node.children.index(prevNode)
    childIndexRange = (range(nodeIndex - 1, -1, -1) if reverse
        else range(nodeIndex + 1, len(node.children)))

    for i in childIndexRange:
      nextNode, nodeCounter = goToChild(node.children[i], nextNodeClassName,
          nodeToCountClassName, nodeCounter, reverse)
      if nextNode is not None: return nextNode, nodeCounter

  return None, nodeCounter

def goToChild(node: AstNode, nextNodeClassName: str, nodeToCountClassName: Optional[str] = None,
      nodeCounter: int = 0, reverse: bool = False,
      excludeNode: bool = False) -> Tuple[Optional[AstNode], int]:
  if (not excludeNode) and (node.className == nextNodeClassName): return (node, nodeCounter)
  if node.className == nodeToCountClassName: nodeCounter += 1
  children = node.children
  if reverse: children = children[::-1]

  for child in children:
    nextNode, nodeCounter = goToChild(child, nextNodeClassName, nodeToCountClassName, nodeCounter)
    if nextNode is not None: return nextNode, nodeCounter

  return None, nodeCounter



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
