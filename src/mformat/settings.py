#!/usr/bin/python

# Copyright (C) 2020 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional



class SettingMetaData(object):
  def __init__(self, name: str, type_: type, description: str,
        noDescription: Optional[str] = None) -> None:
    self.name = name
    self.type_ = type_
    self.description = description
    self.noDescription = noDescription



class Settings(object):
  metaData = [
        SettingMetaData("indent", int,
          "Number of spaces or tabs to indent a block"),
        SettingMetaData("indentCaseOtherwise", bool,
          "Indent case and otherwise blocks in switch blocks",
          "Don't indent case and otherwise blocks in switch blocks"),
        SettingMetaData("indentMainFunction", bool,
          "Indent the main function (= the first function)",
          "Don't indent the main function (= the first function)"),
        SettingMetaData("indentLocalFunction", bool,
          "Indent local functions (= other non-nested functions)",
          "Don't indent local functions (= other non-nested functions)"),
        SettingMetaData("indentNestedFunction", bool,
          "Indent nested functions",
          "Don't ndent nested functions"),
        SettingMetaData("omitSpaceAfterComma", bool,
          "Don't insert spaces after commas if all arguments of the comma-separated "
            "list have at most omitSpaceAfterCommaMaxLength characters",
          "Always insert spaces after commas"),
        SettingMetaData("omitSpaceAfterCommaMaxLength", int,
          "Maximum number of characters for omitSpaceAfterComma to be applied"),
        SettingMetaData("omitSpaceAroundColon", bool,
          "Don't insert spaces around colons if both operands have at most "
            "omitSpaceAroundColonMaxLength characters",
          "Always insert spaces around colons"),
        SettingMetaData("omitSpaceAroundColonMaxLength", int,
          "Maximum number of characters for omitSpaceAroundColon to be applied"),
        SettingMetaData("newlineAtEndOfFile", bool,
          "Insert a newline at the end of files",
          "Don't insert a newline at the end of files"),
      ]

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
    self.applyDict(jsonSettings)

  def save(self, filePath: str) -> None:
    selfSettings = vars(self)
    with open(filePath, "w") as f: json.dump(selfSettings, f)

  def applyDict(self, dictSettings: Dict[str, Any]) -> None:
    selfSettings = vars(self)

    for name, value in dictSettings.items():
      if name in selfSettings: setattr(self, name, value)
