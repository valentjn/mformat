#!/usr/bin/python3

from __future__ import annotations
import unittest

import mformat



class MformatTestCase(unittest.TestCase):
  def assertFormat(self, inputCode: str, expectedCode: str) -> None:
    self.assertEqual(mformat.formatCode(inputCode), expectedCode)

  def testOperators(self) -> None:
    expectedCode = "x = a + (b * (c + d)) + e;\n"
    self.assertFormat("x=a+(b*(c+d))+e;", expectedCode)
    self.assertFormat("x  =  a  +  (  b  *  (  c  +  d  )  )  +  e  ;", expectedCode)

  def testBlocks(self) -> None:
    self.assertFormat("if a;b;end;", "if a\n  b;\nend\n")
    self.assertFormat("if a;b; if c ; d; end;end;", "if a\n  b;\n  if c\n    d;\n  end\nend\n")

  def testFunctions(self) -> None:
    self.assertFormat("""
function main
E = m*c*c;

function nested
E = m*c*c;
end
end

function local
E = m*c*c;
end
""".lstrip(), """
function main
E = m * c * c;

function nested
  E = m * c * c;
end
end

function local
E = m * c * c;
end
""".lstrip())
    self.assertFormat("""
function main
E = m*c*c;

function local
E = m*c*c;
""".lstrip(), """
function main
E = m * c * c;

function local
E = m * c * c;
""".lstrip())



if __name__ == "__main__":
  unittest.main(verbosity=2)
