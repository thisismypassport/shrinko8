from utils import *
from pico_defs import from_pico_chars
from pico_tokenize import TokenType, is_identifier, keywords
from pico_parse import VarKind, NodeType, Local
from pico_minify import format_string_literal

global_callbacks = {
    "_init", "_draw", "_update", "_update60",
}

member_strings = {
    "n",
    "__index", "__newindex", "__len", "__eq", "__lt", "__le",
    "__add", "__sub", "__mul", "__div", "__idiv", "__mod",
    "__pow", "__and", "__or", "__xor", "__shl", "__shr",
    "__lshr", "__rotl", "__rotr", "__concat", "__unm", "__not",
    "__peek", "__peek2", "__peek4", "__call", "__tostring",
    "__pairs", "__ipairs", "__metatable", "__gc", "__mode",
}

def rename_tokens(ctxt, root, rename):
    all_globals = ctxt.globals.copy()
    global_knowns = global_callbacks.copy()
    member_knowns = member_strings.copy()
    known_tables = set()
    preserve_globals = False
    preserve_members = False
    members_as_globals = False

    if isinstance(rename, dict):
        members_as_globals = rename.get("members=globals", False)
        rules_input = rename.get("rules")
        if rules_input:
            for key, value in rules_input.items():
                if value == False:
                    if key == "*":
                        preserve_globals = True
                    elif key == "*.*":
                        preserve_members = True
                    elif key.endswith(".*"):
                        known_tables.add(key[:-2])
                    elif key.startswith("*."):
                        member_knowns.add(key[2:])
                    else:
                        global_knowns.add(key)
                elif value == True:
                    if key == "*":
                        preserve_globals = False
                    elif key == "*.*":
                        preserve_members = False
                    elif key.endswith(".*"):
                        known_tables.discard(key[:-2])
                    elif key.startswith("*."):
                        member_knowns.discard(key[2:])
                    else:
                        all_globals.discard(key)
                        global_knowns.discard(key)
                else:
                    fail(value)

    # collect char histogram

    char_uses = CounterDictionary()
    def collect_chars(token):
        if token.type != TokenType.ident and not token.fake:
            sublang = getattr(token, "sublang", None)
            if sublang and sublang.get_unminified_chars:
                for ch in sublang.get_unminified_chars():
                    char_uses[ch] += 1
            else:
                for ch in token.value:
                    char_uses[ch] += 1

    root.traverse_tokens(collect_chars)

    k_identifier_chars = string.ascii_letters + string.digits + "_"
    
    ident_chars = []
    for ch in sorted(char_uses, key=lambda k: char_uses[k], reverse=True):
        if ch in k_identifier_chars:
            ident_chars.append(ch)
    
    for ch in k_identifier_chars:
        if ch not in ident_chars:
            ident_chars.append(ch)

    ident_char_order_map = {ch1: ch2 for ch1, ch2 in zip(ident_chars, ident_chars[1:])}

    # collect ident uses

    global_uses = CounterDictionary()
    member_uses = CounterDictionary()
    local_uses = CounterDictionary()
    scopes = []

    def compute_effective_kind(node, kind, explicit):
        if kind == VarKind.member:
            table_name = None
            
            if node.parent.type == NodeType.member and node.parent.key == node and node.parent.child.type == NodeType.var:
                var_node = node.parent.child
                table_name = var_node.name

                if not explicit and var_node.var and var_node.var.keys_kind != None:
                    return compute_effective_kind(node, var_node.var.keys_kind, explicit=True)

            elif not explicit and node.parent.type == NodeType.table_member and node.parent.key == node:
                table_node = node.parent.parent
                if table_node.keys_kind != None:
                    return compute_effective_kind(node, table_node.keys_kind, explicit=True)

                if table_node.parent.type in (NodeType.assign, NodeType.local) and table_node in table_node.parent.sources:
                    assign_i = table_node.parent.sources.index(table_node)
                    target_node = list_get(table_node.parent.targets, assign_i)
                    if target_node and target_node.type == NodeType.var and target_node.var and target_node.var.keys_kind != None:
                        return compute_effective_kind(node, target_node.var.keys_kind, explicit=True)
            
            if preserve_members:
                return None
            elif node.name in member_knowns:
                return None
            elif table_name in known_tables:
                return None
            elif table_name == "_ENV":
                return compute_effective_kind(node, VarKind.global_, explicit=True)
            
            if members_as_globals:
                kind = VarKind.global_

        elif kind == VarKind.global_:
            if not explicit:
                env_var = node.parent_scope.find("_ENV")
                if env_var and env_var.keys_kind != None:
                    return compute_effective_kind(node, env_var.keys_kind, explicit=True)

            if preserve_globals:
                return None
            elif node.name in global_knowns:
                return None
            elif node.name in all_globals:
                global_knowns.add(node.name)
                return None

        elif kind == VarKind.local:
            if node.var.implicit:
                return None
            elif node.name == "_ENV": # e.g. new locals named it
                return None

        return kind

    def collect_idents_pre(node):
        scope = node.start_scope
        if e(scope):
            scope.used_globals = set()
            scope.used_locals = set()
            scopes.append(scope)
            
        if node.type == NodeType.var:
            node.effective_kind = compute_effective_kind(node, default(node.var_kind, node.kind), explicit=e(node.var_kind))
            
            if node.effective_kind == VarKind.member:
                member_uses[node.name] += 1

            elif node.effective_kind == VarKind.global_:
                global_uses[node.name] += 1

            elif node.effective_kind == VarKind.local:
                # should in theory help, but doesn't...
                #if node.new:
                #    local_uses[node.var] += 0
                #else:
                local_uses[node.var] += 1
                    
            # add to the scope based on real kind, to avoid conflicts (e.g. between builtins and globals)
            if node.kind == VarKind.global_:
                for scope in scopes:
                    scope.used_globals.add(node.name)

            elif node.kind == VarKind.local:
                if node.var.scope in scopes:
                    i = scopes.index(node.var.scope)
                    for scope in scopes[i:]:
                        scope.used_locals.add(node.var)
                        
        elif node.type == NodeType.sublang:
            # slight dup of compute_effective_kind logic

            for name, count in node.lang.get_global_usages().items():
                if name not in global_knowns and is_identifier(name):
                    if name in all_globals:
                        global_knowns.add(name)
                    else:
                        global_uses[name] += count

            for name, count in node.lang.get_member_usages().items():
                if name not in member_knowns and is_identifier(name):
                    member_uses[name] += count

            for var, count in node.lang.get_local_usages().items():
                if not var.implicit:
                    local_uses[var] += count

    def collect_idents_post(node):
        for scope in node.end_scopes:
            assert scopes.pop() == scope

    root.traverse_nodes(collect_idents_pre, collect_idents_post, extra=True)

    # assign idents

    def get_next_ident_char(ch, first):
        nextch = ident_char_order_map.get(ch) if ch else ident_chars[0]
        while first and nextch and (nextch.isdigit() or nextch == '_'): # note: we avoid leading underscores too
            nextch = ident_char_order_map.get(nextch)
        if nextch:
            return nextch, True
        else:
            return ident_chars[0], False

    def create_ident_stream():
        next_ident = ""

        def get_next_ident():
            nonlocal next_ident
            for i in range(len(next_ident)-1, -1, -1):
                next_ch, found = get_next_ident_char(next_ident[i], i==0)
                next_ident = str_replace_at(next_ident, i, 1, next_ch)
                if found:
                    break
            else:
                next_ident = str_insert(next_ident, 0, get_next_ident_char(None, True)[0])
            return next_ident

        return get_next_ident

    def assign_idents(uses, excludes, skip=0):
        ident_stream = create_ident_stream()
        rename_map = {}

        for i in range(skip):
            ident_stream()

        for value in sorted(uses, key=lambda k: uses[k], reverse=True):
            while True:
                ident = ident_stream()
                if ident not in excludes and ident not in keywords:
                    break

            rename_map[value] = ident

        return rename_map

    member_renames = assign_idents(member_uses, member_knowns)
    global_renames = assign_idents(global_uses, global_knowns)
    rev_global_renames = {v: k for k, v in global_renames.items()}
    
    local_ident_stream = create_ident_stream()
    local_renames = {}

    remaining_local_uses = list(sorted(local_uses, key=lambda k: local_uses[k], reverse=True))
    while remaining_local_uses:
        ident = local_ident_stream()
        ident_global = rev_global_renames.get(ident)
        if not ident_global and ident in global_knowns:
            ident_global = ident
        ident_locals = []
        
        for i, var in enumerate(remaining_local_uses):
            if ident_global in var.scope.used_globals:
                continue
            
            for _, ident_local in ident_locals:
                if ident_local in var.scope.used_locals:
                    break
                if var in ident_local.scope.used_locals:
                    break

            else:
                local_renames[var] = ident
                ident_locals.append((i, var))

        for i, ident_local in reversed(ident_locals):
            assert remaining_local_uses.pop(i) == ident_local

    # output

    def update_srcmap(mapping, kind):
        for old, new in mapping.items():
            old_name = old.name if isinstance(old, Local) else old

            ctxt.srcmap.append("%s %s <- %s" % (kind, from_pico_chars(new), old_name))

    if e(ctxt.srcmap):
        update_srcmap(member_renames, "member")
        update_srcmap(global_renames, "global")
        update_srcmap(local_renames, "local")

    def update_idents(node):
        if node.type == NodeType.var:
            orig_name = node.name

            if node.effective_kind == VarKind.member:
                node.name = member_renames[node.name]
            elif node.effective_kind == VarKind.global_:
                node.name = global_renames[node.name]
            elif node.effective_kind == VarKind.local:
                node.name = local_renames[node.var]
            else:
                return

            if node.parent.type == NodeType.const: # const string interpreted as identifier case
                assert len(node.parent.children) == 1 and node.parent.extra_names[node.extra_i] == orig_name
                node.parent.extra_names[node.extra_i] = node.name
                node.parent.children[0].value = format_string_literal("".join(node.parent.extra_names))
            else:
                assert len(node.children) == 1 and node.children[0].value == orig_name
                node.children[0].value = node.name
                node.children[0].modified = True
                
        elif node.type == NodeType.sublang:
            node.lang.rename(globals=global_renames, members=member_renames, locals=local_renames)
            
    root.traverse_nodes(update_idents, extra=True)
