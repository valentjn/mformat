#!/usr/bin/python3

from __future__ import annotations
import json
import os

class Settings(object):
  def __init__(self) -> None:
    self.indent = 2
    self.indentCaseOtherwise = True
    self.indentMainFunction = False
    self.indentLocalFunction = False
    self.indentNestedFunction = True
    self.omitSpaceAfterComma = True
    self.omitSpaceAfterCommaMaxLength = 1
    self.omitSpaceAroundColon = True
    self.omitSpaceAroundColonMaxLength = 5
    self.newlineAtEndOfFile = True

  def searchAndLoad(self, codeFilePath: str) -> bool:
    curDirPath = os.path.dirname(os.path.abspath(codeFilePath))
    prevDirPath = None
    settingsFileName = ".mformat.json"

    while not os.path.isfile(settingsFilePath := os.path.join(curDirPath, settingsFileName)):
      prevDirPath = curDirPath
      curDirPath = os.path.dirname(curDirPath)
      if curDirPath == prevDirPath: return False

    self.load(settingsFilePath)
    return True

  def load(self, filePath: str) -> None:
    with open(filePath, "r") as f: jsonSettings = json.load(f)
    assert isinstance(jsonSettings, dict)
    for name, value in jsonSettings.items(): setattr(self, name, value)

  def save(self, filePath: str) -> None:
    jsonSettings = vars(self)
    with open(filePath, "w") as f: json.dump(jsonSettings, f)
