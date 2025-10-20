import re


keywords = {'if', 'while', 'for'}


token_specification = [
    ('COMMENT',   r'//.*'),            
    ('RELOP',     r'==|!=|<=|>=|<|>'), 
    ('ASSIGN',    r'='),               
    ('OP',        r'[+\-*/]'),         
    ('NUM',       r'\d+(\.\d+)?'),     
    ('ID',        r'[A-Za-z_]\w*'),    
    ('NEWLINE',   r'\n'),              
    ('SKIP',      r'[ \t]+'),          
    ('MISMATCH',  r'.'),               
]


tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)

symbol_table = set()

def lexer(code):
    tokens = []
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'NUM':
            tokens.append(f'num({value})')
        elif kind == 'ID':
            if value in keywords:
                tokens.append(f'keyword({value})')
            else:
                tokens.append(f'id({value})')
                symbol_table.add(value)
        elif kind == 'RELOP':
            tokens.append(f'relop({value})')
        elif kind == 'ASSIGN':
            tokens.append(f'op({value})')
        elif kind == 'OP':
            tokens.append(f'op({value})')
        elif kind == 'COMMENT':
            tokens.append(f'comment({value})')
        elif kind == 'NEWLINE' or kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            print(f"lexical error: {value}")
    return tokens



if __name__ == '__main__':
    print("Enter your code (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    code = "\n".join(lines)

    result = lexer(code)

    print("\nTokens Output:")
    for token in result:
        print(token)

    print("\nSymbol Table:")
    print(symbol_table)