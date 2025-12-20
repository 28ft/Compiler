class Token:
    def __init__(self, name=None, attribute=None):
        self.name = name
        self.attribute = attribute
    
    def setName(self, name):
        self.name = name
    
    def setAttribute(self, attribute):
        self.attribute = attribute
    
    def __str__(self):
        if self.attribute:
            return f"{self.name}({self.attribute})"
        return f"{self.name}"

class SymbolTable:
    def __init__(self):
        self.rows = []
        # self.addKeywordsToSymbolTable()
    
    def addKeywordsToSymbolTable(self):
        keywords = ["if", "while", "for", "return", "int", "float", "bool"]
        for keyword in keywords:
            self.rows.append({
                "lexeme": keyword,
                "type": "keyword",
                "address": len(self.rows)
            })
    
    def addKeyword(self, keyword):
        if not any(row["lexeme"] == keyword for row in self.rows):
            self.rows.append({
                "lexeme": keyword,
                "type": "keyword", 
                "address": len(self.rows)
            })
    
    def installID(self, lexeme):
        for idx, row in enumerate(self.rows):
            if row["lexeme"] == lexeme:
                return idx
            
        self.rows.append({
            "lexeme": lexeme,
            "type": "id",
            "address": len(self.rows)
        })
        return len(self.rows) - 1
    
    def getTokenName(self, lexeme):
        for row in self.rows:
            if row["lexeme"] == lexeme:
                return row['type']
        return None
    
    def isKeyword(self, lexeme):
        keywords = ["if", "else", "while", "return", "int", "float", "bool", "for"]
        return lexeme in keywords

class InputFileReader:
    def __init__(self, user_code):
        self.content = user_code
        self.position = 0
    
    def getNextChar(self):
        if self.position < len(self.content):
            char = self.content[self.position]
            self.position += 1
            return char
        return None
    
    def retract(self, backwardSteps=1):
        self.position = max(0, self.position - backwardSteps)
    
    def isEOF(self):
        return self.position >= len(self.content)
    
    def close(self):
        pass

class LexicalAnalyzer:
    def __init__(self, user_code):
        self.inputFile = InputFileReader(user_code)
        self.symbolTable = SymbolTable()
        self.errors = []
    
    def isDigit(self, ch):
        return ch is not None and ch.isdigit()
    
    def isLetter(self, ch):
        return ch is not None and ch.isalpha()
    
    def isDelimiter(self, ch):
        return ch is not None and ch in [' ', '\t', '\n', '\r']
    
    def eatWS(self):
        while True:
            ch = self.inputFile.getNextChar()
            if ch is None:
                break
            if not self.isDelimiter(ch):
                self.inputFile.retract(1)
                break
            
    def opParenthesToken(self):
        ch = self.inputFile.getNextChar()
        if ch == "(":
            return Token("opParenthes", ch)
        self.inputFile.retract(1)
        return None
    
    def clpParenthesToken(self):
        ch = self.inputFile.getNextChar()
        if ch == ")":
            return Token("clParenthes", ch)
        self.inputFile.retract(1)
        return None
    
    def opBracketToken(self):
        ch = self.inputFile.getNextChar()
        if ch == "[":
            return Token("opBracket", ch)
        self.inputFile.retract(1)
        return None
    
    def clBracketToken(self):
        ch = self.inputFile.getNextChar()
        if ch == "]":
            return Token("clBracket", ch)
        self.inputFile.retract(1)
        return None
    
    def opCurlyBracketToken(self):
        ch = self.inputFile.getNextChar()
        if ch == "{":
            return Token("opCurlyBracket", ch)
        self.inputFile.retract(1)
        return None
    
    def clCurlyBracketToken(self):
        ch = self.inputFile.getNextChar()
        if ch == "}":
            return Token("clCurlyBracket", ch)
        self.inputFile.retract(1)
        return None
    
    def semicolonToken(self):
        ch = self.inputFile.getNextChar()
        if ch == ';':
            return Token("semicolon", ";")
        self.inputFile.retract(1)
        return None
    
    def commaToken(self):
        ch = self.inputFile.getNextChar()
        if ch == ',':
            return Token("comma", ",")
        self.inputFile.retract(1)
        return None

    def colonToken(self):
        ch = self.inputFile.getNextChar()
        if ch == ':':
            return Token("colon", ":")
        self.inputFile.retract(1)
        return None

    def commentToken(self):
        ch = self.inputFile.getNextChar()
        if ch == '/':
            ch2 = self.inputFile.getNextChar()
            if ch2 == '/':
                comment_text = "//"
                while True:
                    ch = self.inputFile.getNextChar()
                    if ch is None or ch == '\n':
                        break
                    comment_text += ch
                return Token("comment", comment_text.strip())
            else:
                self.inputFile.retract(2)
                return None
        else:
            self.inputFile.retract(1)
            return None
        
    def arithOpToken(self):
        state = 0
        token = Token("arithOp")
        
        while True:
            if state == 0:
                ch = self.inputFile.getNextChar()
                if ch == '+':
                    state = 1
                elif ch == '-':
                    state = 2
                elif ch == '*':
                    state = 3
                elif ch == '/':
                    state = 4
                else:
                    self.inputFile.retract(1)
                    return None
            elif state == 1:
                token.setAttribute("+")
                return token
            elif state == 2:
                token.setAttribute("-")
                return token
            elif state == 3:
                token.setAttribute("*")
                return token
            elif state == 4:
                token.setAttribute("/")
                return token
    
    def relOpToken(self):
        state = 0
        token = Token("relOp")
        
        while True:
            if state == 0:
                ch = self.inputFile.getNextChar()
                if ch == '>':
                    state = 1
                elif ch == '<':
                    state = 4
                elif ch == '=':
                    state = 7
                elif ch == '!':
                    state = 9
                else:
                    self.inputFile.retract(1)
                    return None
            
            elif state == 1:  # >
                ch = self.inputFile.getNextChar()
                if ch == '=':
                    state = 2
                else:
                    state = 3
            
            elif state == 2:  # >=
                token.setAttribute(">=")
                return token
            
            elif state == 3:  # >
                self.inputFile.retract(1)
                token.setAttribute(">")
                return token
            
            elif state == 4:  # <
                ch = self.inputFile.getNextChar()
                if ch == '=':
                    state = 5
                else:
                    state = 6
            
            elif state == 5:  # <=
                token.setAttribute("<=")
                return token
            
            elif state == 6:  # <
                self.inputFile.retract(1)
                token.setAttribute("<")
                return token
            
            elif state == 7:  # =
                ch = self.inputFile.getNextChar()
                if ch == '=':
                    state = 8
                else:
                    state = 10
            
            elif state == 8:  # ==
                token.setAttribute("==")
                return token
            
            elif state == 9:  # !
                ch = self.inputFile.getNextChar()
                if ch == '=':
                    state = 11
                else:
                    self.inputFile.retract(2)
                    return None
            
            elif state == 10:  # = (assignment)
                self.inputFile.retract(2)
                return None
            
            elif state == 11:  # !=
                token.setAttribute("!=")
                return token
    
    def assignOpToken(self):
        state = 0
        token = Token("assignOp")
        
        while True:
            if state == 0:
                ch = self.inputFile.getNextChar()
                if ch == '=':
                    state = 1
                else:
                    self.inputFile.retract(1)
                    return None
            elif state == 1:
                token.setAttribute("=")
                return token
    
    def numberToken(self):
        state = 1
        value = ""
        token = Token("num")
        
        while True:

            if self.inputFile.isEOF():
                if value: 
                    token.setAttribute(value)
                    return token
                else:
                    return None
            
            if state == 1:
                ch = self.inputFile.getNextChar()
                if self.isDigit(ch):
                    value += ch
                    state = 3
                elif (ch == "+") or (ch == "-"):
                    value += ch
                    state = 2
                else:
                    self.inputFile.retract(1)
                    return None
            
            elif state ==2:
                ch = self.inputFile.getNextChar()
                if self.isDigit(ch):
                    value += ch
                    state = 3
                else:
                    self.inputFile.retract(2)
                    return None

            elif state == 3:
                ch = self.inputFile.getNextChar()
                if self.isDigit(ch):
                    value += ch
                elif ch == ".":
                    value += ch
                    state = 4
                elif ch == "e":
                    value += ch
                    state = 6
                else:
                    self.inputFile.retract(1)
                    token.setAttribute(value)
                    state = 10
                    return token
                
            elif state == 4:
                ch = self.inputFile.getNextChar()
                if self.isDigit(ch):
                    value += ch
                    state = 5
                else:
                    self.inputFile.retract(2)
                    return None
                
            elif state == 5:
                ch = self.inputFile.getNextChar()
                if self.isDigit(ch):
                    value += ch
                elif ch == "e":
                    value += ch
                    state = 6
                else:
                    self.inputFile.retract(1)
                    token.setAttribute(value)
                    state = 11
                    return token
                
            elif state == 6:
                ch = self.inputFile.getNextChar()
                if self.isDigit(ch):
                    value += ch
                    state = 8
                elif (ch == "+") or (ch == "-"):
                    value += ch
                    state = 7
                else:
                    self.inputFile.retract(2)
                    return None
                
            elif state == 7:
                ch = self.inputFile.getNextChar()
                if self.isDigit(ch):
                    value += ch
                    state = 8
                else:
                    self.inputFile.retract(3)
                    return None
                
            elif state == 8:
                ch = self.inputFile.getNextChar()
                if self.isDigit(ch):
                    value += ch
                else:
                    self.inputFile.retract(1)
                    token.setAttribute(value)
                    state = 9
                    return token
    
    def idAndKeywordToken(self):
        state = 0
        lexeme = ""
        token = None
        
        while True:
            if state == 0:
                ch = self.inputFile.getNextChar()
                if self.isLetter(ch):
                    lexeme += ch
                    state = 1
                else:
                    self.inputFile.retract(1)
                    return None
            
            elif state == 1:
                ch = self.inputFile.getNextChar()
                if self.isLetter(ch) or self.isDigit(ch):
                    lexeme += ch
                else:
                    self.inputFile.retract(1)
                    state = 2
            
            elif state == 2:
                if self.symbolTable.isKeyword(lexeme):
                    token = Token("keyword", lexeme)
                    self.symbolTable.addKeyword(lexeme)
                    return token

                # token_name = self.symbolTable.getTokenName(lexeme)
                # if token_name:
                #     if token_name == "keyword":
                #         token = Token("keyword", lexeme)
                #     else:
                #         token = Token("id", lexeme)
                #     return token
                else:
                    token = Token("id", lexeme)
                    self.symbolTable.installID(lexeme)
                    return token
    
    def getNextToken(self):
        self.eatWS()

        if self.inputFile.isEOF():
            return None

        token = self.commentToken()
        if token: return token

        token = self.opParenthesToken()
        if token: return token

        token = self.clpParenthesToken()
        if token: return token

        token = self.opBracketToken()
        if token: return token

        token = self.clBracketToken()
        if token: return token

        token = self.opCurlyBracketToken()
        if token: return token

        token = self.clCurlyBracketToken()
        if token: return token

        token = self.semicolonToken()
        if token: return token

        token = self.commaToken()
        if token: return token

        token = self.colonToken()
        if token: return token
        
        token = self.relOpToken()
        if token: return token
    
        token = self.arithOpToken()
        if token: return token

        token = self.assignOpToken()
        if token: return token
        
        token = self.numberToken()
        if token: return token
        
        token = self.idAndKeywordToken()
        if token: return token

        ch = self.inputFile.getNextChar()
        if ch is not None:
            error_token = Token("unknown", ch)
            self.errors.append(f"Lexical error: Unknown character '{ch}'")
            return error_token
        
        return None
    
    def getLexicalErrors(self):
        return self.errors
    
    def hasErrors(self):
        return len(self.errors) > 0

def get_user_input():
    print("Please enter your code (enter an empty line to finish):")
    print("=" * 50)
    
    lines = []
    while True:
        try:
            line = input()
            if line == "":
                break
            lines.append(line)
        except EOFError:
            break
    
    return "\n".join(lines)

def main():
    print("Lexical Analyzer")
    print("=" * 50)
    
    user_code = get_user_input()

    if not user_code.strip():
        print("No code has entered")
        return

    try:
        lexicalAnalyzer = LexicalAnalyzer(user_code)
        
        print("\nResult:")
        print("=" * 50)
        
        token_count = 0
        
        token = lexicalAnalyzer.getNextToken()
        while token is not None:
            print(token)
            token_count += 1
            token = lexicalAnalyzer.getNextToken()
        
        if lexicalAnalyzer.hasErrors():
            print(f"\nLexical Errors ({len(lexicalAnalyzer.errors)}):")
            print("-" * 50)
            for error in lexicalAnalyzer.getLexicalErrors():
                print(f"  {error}")
        else:
            print(f"\nNo lexical errors found!")

        print("\nSymbol Table:")
        print("┌───────┬──────────────┬────────────┬─────────┐")
        print("│ Index │   Lexeme     │ Token Type │ Address │")
        print("├───────┼──────────────┼────────────┼─────────┤")
        for idx, row in enumerate(lexicalAnalyzer.symbolTable.rows):
            print(f"│ {idx:5} │ {row['lexeme']:12} │ {row['type']:10} │ {row['address']:7} │")
        print("└───────┴──────────────┴────────────┴─────────┘")
        
    except Exception as e:
        print(f"error: {e}")


if __name__ == "__main__":
    main()