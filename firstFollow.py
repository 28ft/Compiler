def split_production(prod):
    """تجزیه رشته تولید به نمادها - نسخه اصلاح‌شده"""
    symbols = []
    i = 0
    n = len(prod)
    
    while i < n:
        # نادیده گرفتن فاصله
        if prod[i].isspace():
            i += 1
            continue
        
        # شناسه‌ها و اعداد
        if prod[i].isalpha():
            start = i
            while i < n and (prod[i].isalnum() or prod[i] == '_' or prod[i] == "'"):
                i += 1
            symbols.append(prod[start:i])
        
        # اعداد
        elif prod[i].isdigit():
            start = i
            while i < n and prod[i].isdigit():
                i += 1
            symbols.append(prod[start:i])
        
        # سایر کاراکترها
        else:
            symbols.append(prod[i])
            i += 1
    
    return symbols


def compute_first(grammar):
    """محاسبه FIRST برای گرامر"""
    first = {nt: set() for nt in grammar}
    terminals = set()
    
    # شناسایی پایانه‌ها (یک بار اولیه)
    for prods in grammar.values():
        for prod in prods:
            if prod == 'e':
                continue
            for sym in split_production(prod):
                if sym not in grammar and sym != 'e':
                    terminals.add(sym)
    
    # الگوریتم اصلی FIRST
    changed = True
    while changed:
        changed = False
        for nt, prods in grammar.items():
            for prod in prods:
                if prod == 'e':
                    if 'e' not in first[nt]:
                        first[nt].add('e')
                        changed = True
                    continue
                
                symbols = split_production(prod)
                all_epsilon = True
                
                for sym in symbols:
                    if sym in terminals:
                        if sym not in first[nt]:
                            first[nt].add(sym)
                            changed = True
                        all_epsilon = False
                        break
                    else:  # غیرپایانه
                        before = len(first[nt])
                        first[nt] |= first.get(sym, set()) - {'e'}
                        if len(first[nt]) > before:
                            changed = True
                        
                        if 'e' not in first.get(sym, set()):
                            all_epsilon = False
                            break
                
                if all_epsilon and 'e' not in first[nt]:
                    first[nt].add('e')
                    changed = True
    
    return first, terminals


def compute_follow_simple(grammar, first, terminals):
    """محاسبه FOLLOW - نسخه ساده و صحیح"""
    follow = {nt: set() for nt in grammar}
    start_symbol = list(grammar.keys())[0]
    follow[start_symbol].add('$')
    
    changed = True
    while changed:
        changed = False
        
        for A, prods in grammar.items():
            for prod in prods:
                if prod == 'e':
                    continue
                
                symbols = split_production(prod)
                
                for i, B in enumerate(symbols):
                    if B not in grammar:
                        continue  # فقط غیرپایانه‌ها
                    
                    # قاعده ۱: FIRST(نمادهای بعدی) را اضافه کن
                    if i + 1 < len(symbols):
                        j = i + 1
                        while j < len(symbols):
                            X = symbols[j]
                            
                            if X in grammar:  # غیرپایانه
                                # FIRST(X) بدون ε اضافه شود
                                new_items = first.get(X, set()) - {'e'}
                                if new_items:
                                    old_size = len(follow[B])
                                    follow[B] |= new_items
                                    if len(follow[B]) > old_size:
                                        changed = True
                                
                                # اگر X می‌تواند ε تولید کند، به سراغ بعدی برو
                                if 'e' in first.get(X, set()):
                                    j += 1
                                else:
                                    break  # X نمی‌تواند ε تولید کند
                            else:  # پایانه
                                # خود پایانه را اضافه کن
                                if X not in follow[B]:
                                    follow[B].add(X)
                                    changed = True
                                break  # پایانه ε نیست
                    
                    # قاعده ۲: اگر تمام نمادهای بعدی می‌توانند ε تولید کنند
                    # یا اگر B آخرین نماد است
                    apply_follow_A = False
                    
                    if i == len(symbols) - 1:  # B آخرین نماد است
                        apply_follow_A = True
                    else:
                        # بررسی کن آیا همه نمادهای بعدی می‌توانند ε تولید کنند
                        all_can_be_epsilon = True
                        for j in range(i + 1, len(symbols)):
                            X = symbols[j]
                            if X in terminals or 'e' not in first.get(X, set()):
                                all_can_be_epsilon = False
                                break
                        
                        if all_can_be_epsilon:
                            apply_follow_A = True
                    
                    if apply_follow_A:
                        old_size = len(follow[B])
                        follow[B] |= follow[A]
                        if len(follow[B]) > old_size:
                            changed = True
    
    return follow


# ================ تست ================


grammar = {
    'E': ['T E\''],
    'E\'': ['+ T E\'', 'e'],
    'T': ['F T\''],
    'T\'': ['* F T\'', 'e'],
    'F': ['( E )', 'id']
}

first, terminals = compute_first(grammar)
follow1 = compute_follow_simple(grammar, first, terminals)

print("FIRST Sets:")
for nt in sorted(grammar.keys()):
    print(f"  FIRST({nt}) = {sorted(first.get(nt, []))}")

print("\nFOLLOW Sets:")
for nt in sorted(grammar.keys()):
    print(f"  FOLLOW({nt}) = {sorted(follow1.get(nt, []))}")
