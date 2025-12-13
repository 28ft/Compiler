def compute_first(grammar):
    first = {nt: set() for nt in grammar}

    def first_of(symbol):
        if symbol not in grammar:  
            return {symbol}
        return first[symbol]

    changed = True
    while changed:
        changed = False
        for nt in grammar:
            for production in grammar[nt]:
                symbols = production.split()
                can_epsilon = True
                for sym in symbols:
                    f = first_of(sym)
                    before = len(first[nt])
                    first[nt].update(f - {'ε'})
                    if 'ε' not in f:
                        can_epsilon = False
                        break
                if can_epsilon:
                    first[nt].add('ε')
                if len(first[nt]) != before:
                    changed = True
    return first


def compute_follow(grammar, first, start_symbol):
    follow = {nt: set() for nt in grammar}
    follow[start_symbol].add('$')

    def first_of_string(symbols):
        result = set()
        for s in symbols:
            f = first[s] if s in first else {s}
            result |= (f - {'ε'})
            if 'ε' not in f:
                return result
        result.add('ε')
        return result

    changed = True
    while changed:
        changed = False
        for nt in grammar:
            for production in grammar[nt]:
                symbols = production.split()
                for i, sym in enumerate(symbols):
                    if sym in grammar:
                        after = symbols[i+1:]
                        f = first_of_string(after)
                        before = len(follow[sym])
                        follow[sym].update(f - {'ε'})
                        if 'ε' in f or not after:
                            follow[sym].update(follow[nt])
                        if len(follow[sym]) != before:
                            changed = True
    return follow


grammar = {
    'S': ['A X B'],
    'A': ['a A', 'ε'],
    'X':['Y Z', 'c'],
    'Y':['d Y', 'ε'],
    'Z':['e', 'ε'],
    'B': ['b B', 'f']
}


start_symbol = next(iter(grammar))
first = compute_first(grammar)
follow = compute_follow(grammar, first, start_symbol)

print("FIRST sets:")
for nt in first:
    print(f"first({nt}): {first[nt]}")

print("\nFOLLOW sets:")
for nt in follow:
    print(f"follow({nt}): {follow[nt]}")
