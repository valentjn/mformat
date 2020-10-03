#!/usr/bin/python3

from __future__ import annotations
from typing import List, Optional, Union

import re

class TokenClass(object):
  def __init__(self, name: str, pattern: Union[re.Pattern[str], str]) -> None:
    self.name = name
    self.pattern = (re.compile(pattern) if isinstance(pattern, str) else pattern)

  def __repr__(self) -> str:
    return self.name

class Token(object):
  def __init__(self, code: str, startPos: int, className: str) -> None:
    self.code = code
    self.startPos = startPos
    self.className = className
    self.value: Union[str, int, float] = code
    self.groupDepth: Optional[int] = None
    self.evaluate()

  def evaluate(self) -> None:
    if self.className == "singleQuotedString":
      self.value = self.code[1:-1].replace("''", "'")
    elif self.className == "number":
      self.value = float(self.code)
      if self.value == int(self.value): self.value = int(self.value)
    else:
      self.value = self.code

  def isRelevant(self) -> bool:
    return (self.className not in [
        "blockComment", "lineComment", "lineContinuationComment", "newline", "whitespace"])

  def __repr__(self) -> str:
    indent = (self.groupDepth * "  " if self.groupDepth is not None else "")
    return (f"{indent}Token(code={repr(self.code)}, startPos={repr(self.startPos)}, "
        f"className={repr(self.className)}, value={repr(self.value)})")

class Tokenizer(object):
  _blockCommentTokenClass = TokenClass("blockComment", r"%\{(\n(.|\n)*\n|\n)[ \t]*%\}(?=\n|$)")
  _conjugateTransposeOperatorTokenClass = TokenClass("conjugateTransposeOperator", r"'")
  _openingParenthesisWithIdentifierTokenClass = (
      TokenClass("openingParenthesisWithIdentifier", r"\("))
  _closingParenthesisWithIdentifierTokenClass = (
      TokenClass("closingParenthesisWithIdentifier", r"\)"))
  _openingBraceWithIdentifierTokenClass = TokenClass("openingBraceWithIdentifier", r"\{")
  _closingBraceWithIdentifierTokenClass = TokenClass("closingBraceWithIdentifier", r"\}")

  _tokenClasses = [
        TokenClass("lineComment", r"%.*"),
        TokenClass("lineContinuationComment", r"\.\.\..*(\n|$)"),
        TokenClass("keyword", r"(break|case|catch|classdef|continue|else|elseif|"
          r"end|for|function|global|if|otherwise|parfor|persistent|return|"
          r"spmd|switch|try|while)(?=[^A-Za-z0-9_]|$)"),
        TokenClass("singleQuotedString", r"'([^'\n]*('')*)*'(?=[^']|$)"),
        TokenClass("identifier", r"[A-Za-z][A-Za-z0-9_]*"),
        TokenClass("number", r"([0-9]+|[0-9]*\.[0-9]+|[0-9]+\.[0-9]*)([eE][0-9]+)?"),
        TokenClass("openingParenthesisWithoutIdentifier", r"\("),
        TokenClass("closingParenthesis", r"\)"),
        TokenClass("openingBracketWithoutIdentifier", r"\["),
        TokenClass("closingBracket", r"\]"),
        TokenClass("openingBraceWithoutIdentifier", r"\{"),
        TokenClass("closingBrace", r"\}"),
        TokenClass("eqOperator", r"=="),
        TokenClass("neOperator", r"~="),
        TokenClass("assignmentOperator", r"="),
        TokenClass("shortCircuitLogicalAndOperator", r"&&"),
        TokenClass("logicalAndOperator", r"&"),
        TokenClass("shortCircuitLogicalOrOperator", r"\|\|"),
        TokenClass("logicalOrOperator", r"\|"),
        TokenClass("logicalNotOperator", r"~"),
        TokenClass("lteOperator", r"<="),
        TokenClass("ltOperator", r"<"),
        TokenClass("gteOperator", r">="),
        TokenClass("gtOperator", r">"),
        TokenClass("additionOperator", r"\+"),
        TokenClass("subtractionOperator", r"-"),
        TokenClass("multiplicationOperator", r"\.\*"),
        TokenClass("matrixMultiplicationOperator", r"\*"),
        TokenClass("rightDivisionOperator", r"\./"),
        TokenClass("leftDivisionOperator", r"\.\\"),
        TokenClass("matrixRightDivisionOperator", r"/"),
        TokenClass("matrixLeftDivisionOperator", r"\\"),
        TokenClass("powerOperator", r"\.\^"),
        TokenClass("matrixPowerOperator", r"\^"),
        TokenClass("transposeOperator", r"\.'"),
        TokenClass("colonOperator", r":"),
        TokenClass("period", r"\."),
        TokenClass("comma", r","),
        TokenClass("semicolon", r";"),
        TokenClass("tilde", r"~"),
        TokenClass("whitespace", r"[ \t]+"),
        TokenClass("newline", r"\n"),
      ]

  def __init__(self) -> None:
    self._code = ""
    self._tokens: List[Token] = []
    self._pos = 0
    self._curLine = ""
    self._posInCurLine = 0
    self._onlyWhitespaceLeftOfPosInCurLine = True
    self._lastRelevantToken: Optional[Token] = None
    self._groupingStack: List[str] = []

  def tokenizeCode(self, code: str) -> List[Token]:
    self._code = code
    self._tokens = []
    self._pos = 0
    self._lastRelevantToken = None
    self._groupingStack = []

    while self._pos < len(self._code):
      self._updateLineInfo()

      if (self._onlyWhitespaceLeftOfPosInCurLine
            and self._matchTokenClass(self._blockCommentTokenClass)):
        continue
      elif ((self._lastRelevantToken is not None)
            and (self._lastRelevantToken.className in ["identifier", "number",
              "closingParenthesis", "closingBracket", "closingBrace"])
            and self._matchTokenClass(self._conjugateTransposeOperatorTokenClass)):
        continue
      elif ((self._lastRelevantToken is not None)
            and (self._lastRelevantToken.className == "identifier")
            and (self._matchTokenClass(self._openingParenthesisWithIdentifierTokenClass)
              or self._matchTokenClass(self._openingBraceWithIdentifierTokenClass))):
        continue

      tokenClassMatched = False
      tokenClass = None

      for tokenClass in self._tokenClasses:
        if self._matchTokenClass(tokenClass):
          tokenClassMatched = True
          break

      if not tokenClassMatched:
        self._appendToken(Token(self._code[self._pos], self._pos, "unknown"))

    return self._tokens

  def _updateLineInfo(self) -> None:
    lineEndPos = self._pos
    while (lineEndPos < len(self._code)) and (self._code[lineEndPos] != "\n"): lineEndPos += 1

    lineStartPos = self._pos - 1
    while (lineStartPos >= 0) and (self._code[lineStartPos] != "\n"): lineStartPos -= 1
    lineStartPos += 1

    self._curLine = self._code[lineStartPos:lineEndPos]
    self._posInCurLine = self._pos - lineStartPos
    self._onlyWhitespaceLeftOfPosInCurLine = True

    for i in range(self._posInCurLine):
      if (self._curLine[i] != " ") and (self._curLine[i] != "\t"):
        self._onlyWhitespaceLeftOfPosInCurLine = False
        break

  def _matchTokenClass(self, tokenClass: TokenClass) -> bool:
    if (match := re.match(tokenClass.pattern, self._code[self._pos:])) is not None:
      matchString = match.group()
      self._appendToken(Token(matchString, self._pos, tokenClass.name))
      return True
    else:
      return False

  def _appendToken(self, token: Token) -> None:
    self._tokens.append(token)
    self._pos += len(token.code)
    if token.isRelevant(): self._lastRelevantToken = token
    token.groupDepth = len(self._groupingStack)

    if token.className.startswith("opening"):
      self._groupingStack.append(token.className[7:])
    elif token.className.startswith("closing"):
      token.className += ("WithIdentifier"
          if (len(self._groupingStack) > 0) and "WithIdentifier" in self._groupingStack[-1]
          else "WithoutIdentifier")
      self._groupingStack.pop()
      token.groupDepth -= 1
