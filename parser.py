# -*- coding: utf-8 -*-
"""
Compiler Design - Assignment 4 (Practical)
One clean Python script that provides:
Top-down (recursive descent) parser + Parse Tree printing
3) Precise error reporting with line/column (lexer-level)
Usage:
  python compiler_project_final.py <input_file>
If no input_file is given, it reads from stdin.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Optional, Iterable, Any
import sys
import re

# ------------------------- Parse tree node -------------------------
class Node:
    def __init__(self, label: str, children: Optional[List["Node"]] = None, value: Optional[str] = None):
        self.label = label
        self.children = children or []
        self.value = value

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        if self.value is not None:
            line = f"{pad}{self.label}({self.value})"
        else:
            line = f"{pad}{self.label}"
        out = [line]
        for ch in self.children:
            out.append(ch.pretty(indent + 1))
        return "\n".join(out)

# ------------------------- Lexer -------------------------
@dataclass
class Token:
    typ: str          # terminal symbol used by grammar: id, num, if, else, ...
    lexeme: str       # original text
    line: int
    col: int

KEYWORDS = {"if", "else", "while", "return", "int", "float", "bool"}
SINGLE = {
    "(": "(", ")": ")",
    "{": "{", "}": "}",
    "[": "[", "]": "]",
    ",": ",", ";": ";",
    "+": "+", "-": "-",
    "*": "*", "/": "/",
    "=": "=",
    "<": "<", ">": ">",
}

def lex(source: str) -> List[Token]:
    """
    Produces tokens matching grammar terminals.
    Supports: // line comments, /* block comments */
    """
    tokens: List[Token] = []
    i = 0
    line = 1
    col = 1

    def advance(n: int = 1):
        nonlocal i, line, col
        for _ in range(n):
            if i >= len(source):
                return
            ch = source[i]
            i += 1
            if ch == "\n":
                line += 1
                col = 1
            else:
                col += 1

    while i < len(source):
        ch = source[i]

        # whitespace
        if ch.isspace():
            advance(1)
            continue

        # line comment //
        if source.startswith("//", i):
            while i < len(source) and source[i] != "\n":
                advance(1)
            continue

        # block comment /* ... */
        if source.startswith("/*", i):
            advance(2)
            while i < len(source) and not source.startswith("*/", i):
                advance(1)
            if i < len(source):
                advance(2)
            continue

        start_line, start_col = line, col

        # two-char operators
        if source.startswith("==", i):
            tokens.append(Token("==", "==", start_line, start_col))
            advance(2)
            continue
        if source.startswith("!=", i):
            tokens.append(Token("!=", "!=", start_line, start_col))
            advance(2)
            continue

        # identifier / keyword
        if ch.isalpha() or ch == "_":
            j = i
            while j < len(source) and (source[j].isalnum() or source[j] == "_"):
                j += 1
            lexeme = source[i:j]
            typ = lexeme if lexeme in KEYWORDS else "id"
            tokens.append(Token(typ, lexeme, start_line, start_col))
            advance(j - i)
            continue

        # number
        if ch.isdigit():
            j = i
            while j < len(source) and source[j].isdigit():
                j += 1
            lexeme = source[i:j]
            tokens.append(Token("num", lexeme, start_line, start_col))
            advance(j - i)
            continue

        # single-char symbols
        if ch in SINGLE:
            tokens.append(Token(SINGLE[ch], ch, start_line, start_col))
            advance(1)
            continue

        # unknown
        raise SyntaxError(f"Lexical error at line {start_line}, column {start_col}: unexpected character {repr(ch)}")

    tokens.append(Token("$", "$", line, col))
    return tokens

# ------------------------- Grammar (for both parsers) -------------------------
# epsilon productions are represented with empty RHS []
PRODUCTIONS: List[Tuple[str, List[str]]] = [
    ("Program",  ["FuncList"]),
    ("FuncList", ["Func", "FuncList"]),
    ("FuncList", []),

    ("Func",     ["type", "id", "(", "ParamList", ")", "Block"]),

    ("ParamList", ["Param", "MoreParams"]),
    ("ParamList", []),

    ("MoreParams", [",", "Param", "MoreParams"]),
    ("MoreParams", []),

    ("Param", ["type", "id"]),

    ("Block", ["{", "DeclList", "StmtList", "}"]),

    ("DeclList", ["Decl", "DeclList"]),
    ("DeclList", []),

    ("Decl", ["type", "id", "Arr", ";"]),

    ("Arr", ["[", "num", "]", "Arr"]),
    ("Arr", []),

    ("StmtList", ["Stmt", "StmtList"]),
    ("StmtList", []),

    ("Stmt", ["id", "Arr", "=", "Expr", ";"]),
    ("Stmt", ["if", "(", "Cond", ")", "Stmt", "ElsePart"]),
    ("Stmt", ["while", "(", "Cond", ")", "Stmt"]),
    ("Stmt", ["return", "Expr", ";"]),
    ("Stmt", ["Block"]),

    ("ElsePart", ["else", "Stmt"]),
    ("ElsePart", []),

    ("Cond", ["Expr", "Relop", "Expr"]),

    ("Expr", ["Expr", "+", "Term"]),
    ("Expr", ["Expr", "-", "Term"]),
    ("Expr", ["Term"]),

    ("Term", ["Term", "*", "Factor"]),
    ("Term", ["Term", "/", "Factor"]),
    ("Term", ["Factor"]),

    ("Factor", ["(", "Expr", ")"]),
    ("Factor", ["-", "Factor"]),
    ("Factor", ["id", "Arr"]),
    ("Factor", ["num"]),

    ("Relop", ["<"]),
    ("Relop", [">"]),
    ("Relop", ["=="]),
    ("Relop", ["!="]),

    ("type", ["int"]),
    ("type", ["float"]),
    ("type", ["bool"]),
]

START_SYMBOL = "Program"

def build_grammar_maps():
    by_lhs: Dict[str, List[List[str]]] = {}
    for lhs, rhs in PRODUCTIONS:
        by_lhs.setdefault(lhs, []).append(rhs)
    nonterminals = set(by_lhs.keys())
    terminals = set()
    for _, rhs in PRODUCTIONS:
        for s in rhs:
            if s not in nonterminals:
                terminals.add(s)
    terminals.add("$")
    return by_lhs, nonterminals, terminals

GRAMMAR, NONTERMINALS, TERMINALS = build_grammar_maps()

# ------------------------- Top-down parser (recursive descent) -------------------------
class RDParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def cur(self) -> Token:
        return self.tokens[self.pos]

    def match(self, typ: str) -> Token:
        tok = self.cur()
        if tok.typ != typ:
            self.error(f"expected {typ}, got {tok.typ}", tok)
        self.pos += 1
        return tok

    def error(self, msg: str, tok: Optional[Token] = None):
        t = tok or self.cur()
        raise SyntaxError(f"Syntax error at line {t.line}, column {t.col}: {msg} (near '{t.lexeme}')")

    def parse(self) -> Node:
        node = self.parseProgram()
        if self.cur().typ != "$":
            self.error("extra input after valid program")
        return node

    # For each non-terminal, a function:
    def parseProgram(self) -> Node:
        return Node("Program", [self.parseFuncList()])

    def parseFuncList(self) -> Node:
        if self.cur().typ in ("int", "float", "bool"):
            return Node("FuncList", [self.parseFunc(), self.parseFuncList()])
        return Node("FuncList")  # epsilon

    def parseFunc(self) -> Node:
        t = self.parse_type()
        i = self.match("id")
        self.match("(")
        pl = self.parseParamList()
        self.match(")")
        b = self.parseBlock()
        return Node("Func", [t, Node("id", value=i.lexeme), Node("(", value="("), pl, Node(")", value=")"), b])

    def parseParamList(self) -> Node:
        if self.cur().typ in ("int", "float", "bool"):
            return Node("ParamList", [self.parseParam(), self.parseMoreParams()])
        return Node("ParamList")

    def parseMoreParams(self) -> Node:
        if self.cur().typ == ",":
            self.match(",")
            return Node("MoreParams", [Node(",", value=","), self.parseParam(), self.parseMoreParams()])
        return Node("MoreParams")

    def parseParam(self) -> Node:
        t = self.parse_type()
        i = self.match("id")
        return Node("Param", [t, Node("id", value=i.lexeme)])

    def parseBlock(self) -> Node:
        self.match("{")
        dl = self.parseDeclList()
        sl = self.parseStmtList()
        self.match("}")
        return Node("Block", [Node("{", value="{"), dl, sl, Node("}", value="}")])

    def parseDeclList(self) -> Node:
        if self.cur().typ in ("int", "float", "bool"):
            return Node("DeclList", [self.parseDecl(), self.parseDeclList()])
        return Node("DeclList")

    def parseDecl(self) -> Node:
        t = self.parse_type()
        i = self.match("id")
        arr = self.parseArr()
        self.match(";")
        return Node("Decl", [t, Node("id", value=i.lexeme), arr, Node(";", value=";")])

    def parseArr(self) -> Node:
        # Arr -> [ num ] Arr | ε
        if self.cur().typ == "[":
            self.match("[")
            n = self.match("num")
            self.match("]")
            rest = self.parseArr()
            return Node("Arr", [Node("[", value="["), Node("num", value=n.lexeme), Node("]", value="]"), rest])
        return Node("Arr")

    def parseStmtList(self) -> Node:
        if self.cur().typ in ("id", "{", "if", "while", "return"):
            return Node("StmtList", [self.parseStmt(), self.parseStmtList()])
        return Node("StmtList")

    def parseStmt(self) -> Node:
        la = self.cur().typ
        if la == "id":
            i = self.match("id")
            arr = self.parseArr()
            self.match("=")
            e = self.parseExpr()
            self.match(";")
            return Node("Stmt", [Node("id", value=i.lexeme), arr, Node("=", value="="), e, Node(";", value=";")])
        if la == "if":
            self.match("if")
            self.match("(")
            c = self.parseCond()
            self.match(")")
            s = self.parseStmt()
            ep = self.parseElsePart()
            return Node("Stmt", [Node("if", value="if"), Node("(", value="("), c, Node(")", value=")"), s, ep])
        if la == "while":
            self.match("while")
            self.match("(")
            c = self.parseCond()
            self.match(")")
            s = self.parseStmt()
            return Node("Stmt", [Node("while", value="while"), Node("(", value="("), c, Node(")", value=")"), s])
        if la == "return":
            self.match("return")
            e = self.parseExpr()
            self.match(";")
            return Node("Stmt", [Node("return", value="return"), e, Node(";", value=";")])
        if la == "{":
            b = self.parseBlock()
            return Node("Stmt", [b])
        self.error("expected a statement")

    def parseElsePart(self) -> Node:
        if self.cur().typ == "else":
            self.match("else")
            s = self.parseStmt()
            return Node("ElsePart", [Node("else", value="else"), s])
        return Node("ElsePart")

    def parseCond(self) -> Node:
        e1 = self.parseExpr()
        r = self.parseRelop()
        e2 = self.parseExpr()
        return Node("Cond", [e1, r, e2])

    def parseRelop(self) -> Node:
        if self.cur().typ in ("<", ">", "==", "!="):
            tok = self.cur()
            self.pos += 1
            return Node("Relop", [Node(tok.typ, value=tok.lexeme)])
        self.error("expected relational operator (<, >, ==, !=)")

    # Left recursion removed with loops for RD:
    def parseExpr(self) -> Node:
        node = self.parseTerm()
        while self.cur().typ in ("+", "-"):
            op = self.cur()
            self.pos += 1
            right = self.parseTerm()
            node = Node("Expr", [node, Node(op.typ, value=op.lexeme), right])
        return node if node.label == "Expr" else Node("Expr", [node])

    def parseTerm(self) -> Node:
        node = self.parseFactor()
        while self.cur().typ in ("*", "/"):
            op = self.cur()
            self.pos += 1
            right = self.parseFactor()
            node = Node("Term", [node, Node(op.typ, value=op.lexeme), right])
        return node if node.label == "Term" else Node("Term", [node])

    def parseFactor(self) -> Node:
        la = self.cur().typ
        if la == "(":
            self.match("(")
            e = self.parseExpr()
            self.match(")")
            return Node("Factor", [Node("(", value="("), e, Node(")", value=")")])
        if la == "-":
            self.match("-")
            f = self.parseFactor()
            return Node("Factor", [Node("-", value="-"), f])
        if la == "id":
            i = self.match("id")
            arr = self.parseArr()
            return Node("Factor", [Node("id", value=i.lexeme), arr])
        if la == "num":
            n = self.match("num")
            return Node("Factor", [Node("num", value=n.lexeme)])
        self.error("expected a factor: (Expr) | -Factor | id | num")

    def parse_type(self) -> Node:
        if self.cur().typ in ("int", "float", "bool"):
            tok = self.cur()
            self.pos += 1
            return Node("type", [Node(tok.typ, value=tok.lexeme)])
        self.error("expected type (int|float|bool)")

# ------------------------- FIRST/FOLLOW (for SLR) -------------------------
EPS = "ε"

# ------------------------- Runner (Top-down only) -------------------------

def _print_error_context(source: str, line: int, col: int) -> None:
    """Print the source line and a caret under the error column (best effort)."""
    src_lines = source.splitlines()
    if 1 <= line <= len(src_lines):
        s = src_lines[line - 1]
        print(s)
        caret_pos = max(1, col)
        # best-effort caret alignment (tabs may shift)
        print(" " * (caret_pos - 1) + "^")


def run_topdown(source: str, title: str = "Input") -> None:
    print("=" * 80)
    print(title)
    print("=" * 80)
    try:
        tokens = lex(source)
        parser = RDParser(tokens)
        tree = parser.parse()  # includes end-of-input check
        print("\n[Top-Down] Parse Tree:\n")
        print(tree.pretty())
    except SyntaxError as e:
        # Clean, assignment-friendly error (no Python traceback)
        msg = str(e)
        print("\n[Top-Down] ERROR:")
        print(msg)
        m = re.search(r"line\s+(\d+),\s*column\s+(\d+)", msg)
        if m:
            ln = int(m.group(1))
            cn = int(m.group(2))
            print("\nContext:")
            _print_error_context(source, ln, cn)
        return

def main():
    if len(sys.argv) >= 2:
        path = sys.argv[1]
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = sys.stdin.read()

    # Parse the whole content as a single Program (FuncList can contain multiple Funcs)
    run_topdown(content, title="Program")


if __name__ == "__main__":
    main()
