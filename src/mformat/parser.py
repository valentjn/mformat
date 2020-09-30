#!/usr/bin/python3

from __future__ import annotations
from typing import cast, List, Optional, Union

from .tokenizer import Token

# from https://www.mathworks.com/help/matlab/matlab_prog/operator-precedence.html
operatorPrecedence = {
      "logicalNotOperator" : 0,
      "multiplicationOperator" : 1,
      "rightDivisionOperator" : 1,
      "leftDivisionOperator" : 1,
      "matrixMultiplicationOperator" : 1,
      "matrixRightDivisionOperator" : 1,
      "matrixLeftDivisionOperator" : 1,
      "additionOperator" : 2,
      "subtractionOperator" : 2,
      "colonOperator" : 3,
      "ltOperator" : 4,
      "lteOperator" : 4,
      "gtOperator" : 4,
      "gteOperator" : 4,
      "eqOperator" : 4,
      "neOperator" : 4,
      "logicalAndOperator" : 5,
      "logicalOrOperator" : 6,
      "shortCircuitLogicalAndOperator" : 7,
      "shortCircuitLogicalOrOperator" : 8,
    }



class AstNode(object):
  def __init__(self, tokenOrClassName: Union[str, Token], parent: Optional[AstNode] = None) -> None:
    if isinstance(tokenOrClassName, Token):
      self.className = tokenOrClassName.className
      self.token: Optional[Token] = tokenOrClassName
    else:
      self.className = tokenOrClassName
      self.token = None

    self.parent = parent
    self.children: List[AstNode] = []

  def appendNewAstNodeAsChild(self, tokenOrClassName: Union[str, Token]) -> AstNode:
    child = AstNode(tokenOrClassName, self)
    self.children.append(child)
    return child

  def appendChild(self, node: AstNode) -> AstNode:
    self.children.append(node)
    return node

  def __repr__(self, level: int=0) -> str:
    result = "{}{}".format(level * "  ", self.className)
    if self.token is not None: result += f"(code={repr(self.token.code)})"

    if len(self.children) > 0:
      result += "\n{}".format("\n".join(x.__repr__(level + 1) for x in self.children))

    return result



def parseTokens(tokens: List[Token]) -> AstNode:
  statements = splitIntoStatements(tokens)
  ast = parseStatements(statements)
  return ast



def splitIntoStatements(tokens: List[Token]) -> List[List[Token]]:
  statements: List[List[Token]] = []
  currentStatement = []
  previousToken = None

  for token in tokens:
    currentStatement.append(token)

    if ((token.className == "semicolon")
          or ((token.className == "comma") and (token.depth == 0))
          or ((token.className == "newline")
            and (previousToken is not None)
            and (previousToken.className != "lineContinuationComment"))):
      # to join newlines with last statement
      #if ((token.className == "newline") and (len(currentStatement) == 1)
      #      and (len(statements) > 0)):
      #  statements[-1].append(token)
      #else:
      #  statements.append(currentStatement)

      statements.append(currentStatement)
      currentStatement = []

    previousToken = token

  statements.append(currentStatement)

  return statements



def parseStatements(statements: List[List[Token]]) -> AstNode:
  ast = AstNode("statementSequence")
  curNode = ast

  for statement in statements:
    firstNonWhitespaceToken = None

    for token in statement:
      if token.className != "whitespace":
        firstNonWhitespaceToken = token
        break

    statementAstNode = parseStatement(statement)
    keyword: str

    if ((firstNonWhitespaceToken is not None)
          and (firstNonWhitespaceToken.className == "keyword")
          and ((keyword := cast(str, firstNonWhitespaceToken.value)) in
            ["case", "catch", "classdef", "else", "elseif", "end", "for",
            "function", "if", "otherwise", "parfor", "switch", "try", "while"])):
      if keyword in ["classdef", "for", "function", "if", "parfor", "switch", "try", "while"]:
        curNode = curNode.appendNewAstNodeAsChild("block").appendNewAstNodeAsChild(keyword)
        curNode.appendChild(statementAstNode)
        curNode = curNode.appendNewAstNodeAsChild("statementSequence")
      elif keyword in ["case", "catch", "else", "elseif", "otherwise"]:
        curNode = goUpToParent(curNode, "block").appendNewAstNodeAsChild(keyword)
        curNode.appendChild(statementAstNode)
        curNode = curNode.appendNewAstNodeAsChild("statementSequence")
      elif keyword == "end":
        curNode = goUpToParent(curNode, "block")
        curNode.appendChild(statementAstNode)
        assert curNode.parent is not None
        curNode = curNode.parent
      else:
        raise ValueError(f"unknown keyword '{keyword}'")
    else:
      statementAstNode.parent = curNode
      curNode.children.append(statementAstNode)

  return ast



def parseStatement(statement: List[Token]) -> AstNode:
  node = AstNode("statement")
  irrelevantTokensBeforeNode = node.appendNewAstNodeAsChild("irrelevantTokens")
  statementBodyNode = node.appendNewAstNodeAsChild("statementBody")
  irrelevantTokensAfterNode = node.appendNewAstNodeAsChild("irrelevantTokens")

  relevantTokenIndexStart = None

  for i, token in enumerate(statement):
    if token.isRelevant() and (token.className != "keyword"):
      relevantTokenIndexStart = i
      break

  if relevantTokenIndexStart is None:
    for token in statement: irrelevantTokensBeforeNode.appendNewAstNodeAsChild(token)
    return node

  relevantTokensIndexEnd = len(statement)

  for i, token in enumerate(statement[::-1]):
    if token.isRelevant() and (token.className != "semicolon"):
      relevantTokensIndexEnd = len(statement) - i
      break

  assert 0 <= relevantTokenIndexStart <= relevantTokensIndexEnd <= len(statement)

  for token in statement[:relevantTokenIndexStart]:
    irrelevantTokensBeforeNode.appendNewAstNodeAsChild(token)

  for token in statement[relevantTokensIndexEnd:]:
    irrelevantTokensAfterNode.appendNewAstNodeAsChild(token)

  relevantTokens = statement[relevantTokenIndexStart:relevantTokensIndexEnd]
  statementBodyNode.appendChild(parseStatementFragment(relevantTokens))
  return node



def parseStatementFragment(tokens: List[Token]) -> AstNode:
  if len(tokens) == 0: return AstNode("empty")
  depthOffset = tokens[0].depth

  node = divideAndConquerParseStatementFragmentWithClassName(tokens, "assignmentOperator")
  if node is not None: return node

  topLevelOperatorTokenIndices = [i for i, token in enumerate(tokens)
      if (token.depth == depthOffset) and token.className.endswith("Operator")]

  if len(topLevelOperatorTokenIndices) > 0:
    i = max(topLevelOperatorTokenIndices, key=lambda i: operatorPrecedence[tokens[i].className])
    return divideAndConquerParseStatementFragment(tokens, i)

  relevantTopLevelTokenIndices = [i for i, token in enumerate(tokens)
      if (token.depth == depthOffset) and token.isRelevant()]

  #while (len(relevantTopLevelTokenIndices) > 0) and (
  #      tokens[relevantTopLevelTokenIndices[-1]].className in ["comma", "newline", "semicolon"]):
  #  relevantTopLevelTokenIndices.pop()

  if len(relevantTopLevelTokenIndices) == 0:
    node = AstNode("irrelevantTokens")
    for token in tokens: node.appendNewAstNodeAsChild(token)
    return node
  elif len(relevantTopLevelTokenIndices) == 1:
    node = AstNode("relevantToken")
    relevantTokenIndex = relevantTopLevelTokenIndices[0]
    irrelevantTokensBeforeNode = node.appendNewAstNodeAsChild("irrelevantTokens")
    node.appendNewAstNodeAsChild(tokens[relevantTokenIndex])
    irrelevantTokensAfterNode = node.appendNewAstNodeAsChild("irrelevantTokens")

    for token in tokens[:relevantTokenIndex]:
      irrelevantTokensBeforeNode.appendNewAstNodeAsChild(token)

    for token in tokens[relevantTokenIndex+1:]:
      irrelevantTokensAfterNode.appendNewAstNodeAsChild(token)

    return node

  lastRelevantTopLevelToken = tokens[relevantTopLevelTokenIndices[-1]]
  secondToLastRelevantTopLevelToken = tokens[relevantTopLevelTokenIndices[-2]]

  groupingClassNamesWithIdentifier = {
        "ParenthesisWithIdentifier" : ("functionCall", "calledFunction", "functionArguments"),
        "BraceWithIdentifier" : ("cellReference", "referencedCell", "cellReferenceArguments"),
      }

  groupingClassNamesWithoutIdentifier = {
        "ParenthesisWithoutIdentifier" : ("parenthesisGroup", "groupContents"),
        "BracketWithoutIdentifier" : ("bracketGroup", "groupContents"),
        "BraceWithoutIdentifier" : ("braceGroup", "groupContents"),
      }

  if (((lastRelevantTopLevelToken.className == "identifier")
          and (secondToLastRelevantTopLevelToken.className == "period"))
        or (lastRelevantTopLevelToken.className.startswith("closing")
          and lastRelevantTopLevelToken.className.endswith("WithIdentifier"))):
    if lastRelevantTopLevelToken.className == "identifier":
      classNames = ("structReference", "referencedStruct", "structReferenceArguments")
    else:
      groupingType = lastRelevantTopLevelToken.className[7:]
      classNames = groupingClassNamesWithIdentifier[groupingType]
      assert (secondToLastRelevantTopLevelToken.className == f"opening{groupingType}")

    node = AstNode(classNames[0])
    node.appendNewAstNodeAsChild(classNames[1]).appendChild(parseStatementFragment(
        tokens[:relevantTopLevelTokenIndices[-2]]))
    node.appendNewAstNodeAsChild(secondToLastRelevantTopLevelToken)
    node.appendNewAstNodeAsChild(classNames[2]).appendChild(parseStatementFragment(
        tokens[relevantTopLevelTokenIndices[-2]+1:relevantTopLevelTokenIndices[-1]]))
    node.appendNewAstNodeAsChild(lastRelevantTopLevelToken)
    irrelevantTokens = node.appendNewAstNodeAsChild("irrelevantTokens")

    for token in tokens[relevantTopLevelTokenIndices[-1]+1:]:
      irrelevantTokens.appendNewAstNodeAsChild(token)

    return node
  elif lastRelevantTopLevelToken.className.startswith("closing"):
    groupingType = lastRelevantTopLevelToken.className[7:]
    groupingClassName = groupingClassNamesWithoutIdentifier[groupingType]
    assert len(relevantTopLevelTokenIndices) == 2
    assert (secondToLastRelevantTopLevelToken.className == f"opening{groupingType}")
    node = AstNode(groupingClassName[0])
    irrelevantTokensBeforeNode = node.appendNewAstNodeAsChild("irrelevantTokens")
    node.appendNewAstNodeAsChild(secondToLastRelevantTopLevelToken)
    node.appendNewAstNodeAsChild(groupingClassName[1]).appendChild(parseStatementFragment(
        tokens[relevantTopLevelTokenIndices[-2]+1:relevantTopLevelTokenIndices[-1]]))
    node.appendNewAstNodeAsChild(lastRelevantTopLevelToken)
    irrelevantTokensAfterNode = node.appendNewAstNodeAsChild("irrelevantTokens")

    for token in tokens[:relevantTopLevelTokenIndices[-2]]:
      irrelevantTokensBeforeNode.appendNewAstNodeAsChild(token)

    for token in tokens[relevantTopLevelTokenIndices[-1]+1:]:
      irrelevantTokensAfterNode.appendNewAstNodeAsChild(token)

    return node
  elif any((x.className == "comma") and (x.depth == depthOffset) for x in tokens):
    node = AstNode("commaSeparatedList")
    lastTopLevelCommaTokenIndex = -1

    for i, token in enumerate(tokens):
      if (token.className == "comma") and (token.depth == depthOffset):
        node.appendChild(parseStatementFragment(tokens[lastTopLevelCommaTokenIndex+1:i]))
        node.appendNewAstNodeAsChild(token)
        lastTopLevelCommaTokenIndex = i

    if lastTopLevelCommaTokenIndex < len(tokens) - 1:
      node.appendChild(parseStatementFragment(tokens[lastTopLevelCommaTokenIndex+1:]))

    return node
  else:
    import pprint
    pprint.pprint(tokens)
    raise RuntimeError("unexpected last relevant top-level token "
        f"'{lastRelevantTopLevelToken.className}'")



def divideAndConquerParseStatementFragmentWithClassName(
      tokens: List[Token], className: str) -> Optional[AstNode]:
  for i in range(len(tokens)):
    if tokens[i].className == className: return divideAndConquerParseStatementFragment(tokens, i)

  return None

def divideAndConquerParseStatementFragment(tokens: List[Token], i: int) -> AstNode:
  node = AstNode(f"{tokens[i].className}Node")
  node.appendChild(parseStatementFragment(tokens[:i]))
  node.appendNewAstNodeAsChild(tokens[i])
  node.appendChild(parseStatementFragment(tokens[i+1:]))
  return node



def goUpToParent(node: AstNode, parentClassName: str) -> AstNode:
  while node.className != parentClassName:
    assert node.parent is not None
    node = node.parent

  return node
