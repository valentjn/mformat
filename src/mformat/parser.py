#!/usr/bin/python3

from __future__ import annotations
from typing import cast, List, Optional, Tuple, Union

from .settings import Settings
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
    self.blockDepth: Optional[int] = None

  def appendNewAstNodeAsChild(self, tokenOrClassName: Union[str, Token]) -> AstNode:
    child = AstNode(tokenOrClassName, self)
    self.children.append(child)
    return child

  def appendChild(self, node: AstNode) -> AstNode:
    node.parent = self
    self.children.append(node)
    return node

  def insertNewAstNodeAsChild(self, index: int, tokenOrClassName: Union[str, Token]) -> AstNode:
    child = AstNode(tokenOrClassName, self)
    self.children.insert(index, child)
    return child

  def insertChild(self, index: int, node: AstNode) -> AstNode:
    node.parent = self
    self.children.insert(index, node)
    return node

  def remove(self) -> None:
    assert self.parent is not None
    parentChildren = self.parent.children
    del parentChildren[parentChildren.index(self)]

  def goToParent(self, suffix: str) -> Optional[AstNode]:
    node = self

    while not node.className.endswith(suffix):
      if node.parent is None: return None
      node = node.parent

    return node

  def goToChild(self, suffix: str, reverse: bool = False,
        excludeNode: bool = False) -> Optional[AstNode]:
    if (not excludeNode) and self.className.endswith(suffix): return self
    children = self.children
    if reverse: children = children[::-1]

    for child in children:
      nextNode = child.goToChild(suffix, reverse)
      if nextNode is not None: return nextNode

    return None

  def goToPrev(self, suffix: str) -> Optional[AstNode]:
    return self.goToNext(suffix, True)

  def goToNext(self, suffix: str, reverse: bool = False) -> Optional[AstNode]:
    node = self
    nextNode = node.goToChild(suffix, reverse, True)
    if nextNode is not None: return nextNode

    while node.parent is not None:
      prevNode = node
      node = node.parent
      nodeIndex = node.children.index(prevNode)
      childIndexRange = (range(nodeIndex - 1, -1, -1) if reverse
          else range(nodeIndex + 1, len(node.children)))

      for i in childIndexRange:
        nextNode = node.children[i].goToChild(suffix, reverse)
        if nextNode is not None: return nextNode

    return None

  def _getHierarchy(self) -> List[Tuple[AstNode, int]]:
    hierarchy = []
    node = self

    while node.parent is not None:
      prevNode = node
      node = node.parent
      childIndex = node.children.index(prevNode)
      hierarchy.append((node, childIndex))

    hierarchy.reverse()
    return hierarchy

  def __lt__(self, other: AstNode) -> bool:
    if (self == other) or ((self.parent is None) and (other.parent is None)): return False

    selfHierarchy = self._getHierarchy()
    otherHierarchy = other._getHierarchy()

    if self.parent is None:
      assert len(otherHierarchy) >= 1
      return (otherHierarchy[0][0] == self)
    elif other.parent is None:
      assert len(selfHierarchy) >= 1
      return (selfHierarchy[0][0] == other)

    assert len(selfHierarchy) >= 1
    assert len(otherHierarchy) >= 1
    if selfHierarchy[0][0] != otherHierarchy[0][0]: return False

    for i in range(min(len(selfHierarchy), len(otherHierarchy))):
      if selfHierarchy[i][1] != otherHierarchy[i][1]:
        return selfHierarchy[i][1] < otherHierarchy[i][1]

    return len(selfHierarchy) < len(otherHierarchy)

  def __le__(self, other: AstNode) -> bool:
    return (self == other) or (self < other)

  def __repr__(self, level: int=0) -> str:
    result = "{}{}".format(level * "  ", self.className)
    if self.token is not None: result += f"(code={repr(self.token.code)})"

    if len(self.children) > 0:
      result += "\n{}".format("\n".join(x.__repr__(level + 1) for x in self.children))

    return result

  def __str__(self) -> str:
    code = (self.token.code if self.token is not None else "")
    code += "".join(str(x) for x in self.children)
    return code



def parseTokens(tokens: List[Token], settings: Settings) -> AstNode:
  statements = splitIntoStatements(tokens)
  ast = parseStatements(statements)
  functionsHaveEnd = checkIfFunctionsHaveEnd(ast)
  if functionsHaveEnd is None: functionsHaveEnd = False
  computeBlockDepth(ast, functionsHaveEnd, settings)
  return ast



def splitIntoStatements(tokens: List[Token]) -> List[List[Token]]:
  statements: List[List[Token]] = []
  curStatement = []
  prevToken = None

  for token in tokens:
    curStatement.append(token)

    if ((token.className == "semicolon")
          or ((token.className == "comma") and (token.groupDepth == 0))
          or ((token.className == "newline")
            and (prevToken is not None)
            and (prevToken.className != "lineContinuationComment"))):
      # to join newlines with last statement
      #if ((token.className == "newline") and (len(curStatement) == 1)
      #      and (len(statements) > 0)):
      #  statements[-1].append(token)
      #else:
      #  statements.append(curStatement)

      statements.append(curStatement)
      curStatement = []

    prevToken = token

  statements.append(curStatement)

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
        curNode = curNode.appendNewAstNodeAsChild(f"{keyword}Block")
        curNode = curNode.appendNewAstNodeAsChild(keyword)
        curNode.appendChild(statementAstNode)
        curNode = curNode.appendNewAstNodeAsChild("statementSequence")
      elif keyword in ["case", "catch", "else", "elseif", "otherwise"]:
        parent = curNode.goToParent("Block")
        assert parent is not None
        curNode = parent
        curNode = curNode.appendNewAstNodeAsChild(keyword)
        curNode.appendChild(statementAstNode)
        curNode = curNode.appendNewAstNodeAsChild("statementSequence")
      elif keyword == "end":
        parent = curNode.goToParent("Block")
        assert parent is not None
        curNode = parent
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
  groupDepthOffset = tokens[0].groupDepth

  node = divideAndConquerParseStatementFragmentWithClassName(tokens, "assignmentOperator")
  if node is not None: return node

  if any((x.className == "comma") and (x.groupDepth == groupDepthOffset) for x in tokens):
    node = AstNode("commaSeparatedList")
    lastTopLevelCommaTokenIndex = -1

    for i, token in enumerate(tokens):
      if (token.className == "comma") and (token.groupDepth == groupDepthOffset):
        node.appendChild(parseStatementFragment(tokens[lastTopLevelCommaTokenIndex+1:i]))
        node.appendNewAstNodeAsChild(token)
        lastTopLevelCommaTokenIndex = i

    if lastTopLevelCommaTokenIndex < len(tokens) - 1:
      node.appendChild(parseStatementFragment(tokens[lastTopLevelCommaTokenIndex+1:]))

    return node

  topLevelOperatorTokenIndices = [i for i, token in enumerate(tokens)
      if (token.groupDepth == groupDepthOffset) and token.className.endswith("Operator")]

  if len(topLevelOperatorTokenIndices) > 0:
    i = max(topLevelOperatorTokenIndices, key=lambda i: operatorPrecedence[tokens[i].className])
    return divideAndConquerParseStatementFragment(tokens, i)

  relevantTopLevelTokenIndices = [i for i, token in enumerate(tokens)
      if (token.groupDepth == groupDepthOffset) and token.isRelevant()]

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



def checkIfFunctionsHaveEnd(node: AstNode) -> Optional[bool]:
  if node.className == "functionBlock":
    return (len(node.children) >= 2) and containsEnd(node.children[1])
  else:
    for child in node.children:
      if (functionsHaveEnd := checkIfFunctionsHaveEnd(child)) is not None: return functionsHaveEnd

    return None



def containsEnd(node: AstNode) -> bool:
  if (node.className == "keyword") and (node.token is not None) and (node.token.code == "end"):
    return True
  else:
    return any(containsEnd(x) for x in node.children)



def computeBlockDepth(ast: AstNode, functionsHaveEnd: bool, settings: Settings) -> None:
  nodeStack = [(ast, 0, 0)]
  mainFunctionStarted = False
  mainFunctionEnded = False

  while len(nodeStack) > 0:
    node, blockDepth, functionDepth = nodeStack.pop()
    node.blockDepth = blockDepth

    if (node.parent is not None) and node.parent.className.endswith("Block"):
      if (node.className in ["case", "otherwise"]) and settings.indentCaseOtherwise: blockDepth += 1

      parentIsFunction = (node.parent.className == "functionBlock")

      if parentIsFunction:
        if not mainFunctionStarted:
          mainFunctionStarted = True
        elif (not functionsHaveEnd) or (functionDepth == 0):
          mainFunctionEnded = True

      parentIsMainFunction = parentIsFunction and (not mainFunctionEnded) and (functionDepth == 0)
      parentIsNestedFunction = parentIsFunction and functionsHaveEnd and (functionDepth >= 1)
      parentIsLocalFunction = (parentIsFunction and (not parentIsMainFunction)
          and (not parentIsNestedFunction))
      childFunctionDepth = functionDepth

      if parentIsLocalFunction: blockDepth = 0

      if parentIsFunction and (functionsHaveEnd or (functionDepth == 0)):
        childFunctionDepth += 1

      for child in node.children[::-1]:
        childBlockDepth = blockDepth

        if ((child.className != "statement")
              and ((not parentIsFunction)
                or (parentIsMainFunction and settings.indentMainFunction)
                or (parentIsLocalFunction and settings.indentLocalFunction)
                or (parentIsNestedFunction and settings.indentNestedFunction))):
          childBlockDepth += 1

        nodeStack.append((child, childBlockDepth, childFunctionDepth))
    else:
      for child in node.children[::-1]:
        nodeStack.append((child, blockDepth, functionDepth))
