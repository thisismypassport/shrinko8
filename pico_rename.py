from utils import *
from pico_defs import from_p8str
from pico_tokenize import TokenType, is_identifier, keywords, CommentHint
from pico_output import format_string_literal
from pico_parse import VarKind, NodeType, VarBase
from pico_minify import Focus
import fnmatch

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

class IncludeExcludeMapping:
    """Defines which strings are included or excluded, through dicts & regexes"""

    def __init__(m, keys=None):
        m.dict = dict.fromkeys(keys, True) if e(keys) else {}
        m.default = None
        m.regexs = None

    def set(m, key, value):
        if key == "*":
            m.default = value
        elif "*" not in key:
            m.dict[key] = value
        else:
            if not m.regexs:
                m.regexs = []
            m.regexs.append((re.compile(fnmatch.translate(key)), value))
            
    def __contains__(m, key):
        value = m.dict.get(key, m.default)
        if value is False:
            return False

        if m.regexs:
            for regex, re_value in m.regexs:
                if regex.match(key):
                    value = re_value
                    if value is False:
                        return False
        
        return bool(value)
    
class TableMemberPairIncludeExcludeMapping:
    """Defines which string-pairs are included or excluded, through dicts & regexes"""

    def __init__(m, tables=None, members=None, pairs=None):
        m.table_dict = dict.fromkeys(tables, True) if e(tables) else {}
        m.member_dict = dict.fromkeys(members, True) if e(members) else {}
        m.pair_dict = dict.fromkeys(pairs, True) if e(pairs) else {}
        m.default = None
        m.regexs = None

    def set(m, key, value):
        table, member = key
        if table == "*" and member == "*":
            m.default = value
        elif "*" not in table and member == "*":
            m.table_dict[table] = value
        elif table == "*" and "*" not in member:
            m.member_dict[member] = value
        elif "*" not in table and "*" not in member:
            m.pair_dict[(table, member)] = value
        else:
            if not m.regexs:
                m.regexs = []
            m.regexs.append((re.compile(fnmatch.translate(table)),
                             re.compile(fnmatch.translate(member)), value))
        
    def __contains__(m, key):
        if isinstance(key, tuple):
            table, member = key
        else:
            table, member = "", key

        value = m.pair_dict.get(key, m.table_dict.get(table, m.member_dict.get(member, m.default)))
        if value is False:
            return False

        if m.regexs:
            for table_regex, member_regex, re_value in m.regexs:
                if table_regex.match(table) and member_regex.match(member):
                    value = re_value
                    if value is False:
                        return False
        
        return bool(value)

def rename_tokens(ctxt, root, rename_opts):
    global_strings_cpy = ctxt.builtins | global_callbacks
    preserved_globals = IncludeExcludeMapping(global_strings_cpy)
    preserved_members = TableMemberPairIncludeExcludeMapping(members=member_strings)
    
    # read rename options (e.g. what to preserve)

    def add_rule(rule):
        value = True
        if rule.startswith("!"):
            value = False
            rule = rule[1:]
        
        if "=" in rule:
            nonlocal members_as_globals
            if rule in ("*=*.*", "*.*=*"):
                members_as_globals = True
        
        if "." in rule:
            preserved_members.set(rule.split(".", 1), value)
        else:
            preserved_globals.set(rule, value)

    members_as_globals = False
    safe_only = rename_opts.get("safe-only", False)
    focus = Focus(rename_opts.get("focus"))
    for rule in rename_opts.get("rules", ()):
        add_rule(rule)

    # collect char histogram
    # (reusing commonly used chars in our new identifiers lowers compressed size)
    #
    # also takes the opportunity to find global preserve hints in code

    char_uses = CounterDictionary()
    def collect_chars(token):
        if token.children:
            for comment in token.children:
                if comment.hint == CommentHint.preserve:
                    for value in comment.hintdata:
                        add_rule(value)

        if token.value is None:
            return

        if token.type != TokenType.ident: # including preserved idents would help a tiny bit, but isn't a clear win
                                          # (plus, it's now too early to check for preserved idents here)
            sublang = getattr(token, "sublang", None)
            if sublang and sublang.get_unminified_chars:
                for ch in sublang.get_unminified_chars():
                    char_uses[ch] += 1
            else:
                if token.type == TokenType.string and len(token.value) >= 0x80 and len(set(token.value)) >= 0x80: # ignore compressed strings (heuristic)
                    return

                for ch in token.value:
                    char_uses[ch] += 1

    root.traverse_tokens(collect_chars)

    # TODO: something must still be unoptimal with char_uses collection, as hardcoding k_identifier_chars is more helpful than going by uses...
    if focus.chars:
        k_identifier_chars = string.ascii_letters + string.digits + "_\x1e\x1f" + "".join(chr(x) for x in range(0x80,0x100))
    elif focus.compressed:
        k_identifier_chars = string.ascii_lowercase + string.digits + "_"
    else:
        k_identifier_chars = string.ascii_letters + string.digits + "_"
    
    ident_chars = []
    for ch in sorted(char_uses, key=lambda k: char_uses[k], reverse=True):
        if ch in k_identifier_chars:
            ident_chars.append(ch)
    
    for ch in k_identifier_chars:
        if ch not in ident_chars:
            ident_chars.append(ch)

    ident_char_order_map = {ch1: ch2 for ch1, ch2 in zip(ident_chars, ident_chars[1:])}

    # detect which renames are safe to do, if requested
    # (note - this assumes a "pure" cart with no hints for shrinko8)

    if safe_only:
        preserved_members.default = True # can't reasonably guarantee safety of this
        preserved_globals.default = root.has_env

    # collect uses of identifier
    # (e.g. to give priority to more frequently used ones)

    global_uses = CounterDictionary()
    member_uses = CounterDictionary()
    local_uses = CounterDictionary()
    label_uses = CounterDictionary()
    
    # we avoid renaming into any names used by pico8/lua, as otherwise renamed variables may have a non-nill initial value
    global_excludes = global_strings_cpy
    member_excludes = member_strings.copy()
    local_excludes = defaultdict(set)
    label_excludes = defaultdict(set)

    globals_after_zero = set()
    members_after_zero = set()
    locals_after_zero = set()

    renamed_vars = set()

    def compute_effective_kind(node, kind, explicit):
        """get the identifier kind (global/member/etc) of a node, taking into account hints in the code"""

        if node.var.rename:
            node.name = node.var.rename
            renamed_vars.add(node.var)
            if kind == VarKind.member:
                member_excludes.add(node.name)
            elif kind == VarKind.global_:
                global_excludes.add(node.name)
            elif kind == VarKind.local:
                local_excludes[node.name].add(node.var)
            elif kind == VarKind.label:
                label_excludes[node.name].add(node.var)
            return None

        if kind == VarKind.member:
            table_name = ""
            
            if node.parent.type == NodeType.member and node.parent.key == node and node.parent.child.type == NodeType.var:
                var_node = node.parent.child
                table_name = var_node.name

                if not explicit and var_node.var and var_node.var.keys_kind != None:
                    return compute_effective_kind(node, var_node.var.keys_kind, explicit=True)

            elif node.parent.type == NodeType.table_member and node.parent.key == node:
                table_node = node.parent.parent
                if not explicit and table_node.keys_kind != None:
                    return compute_effective_kind(node, table_node.keys_kind, explicit=True)

                if table_node.parent.type in (NodeType.assign, NodeType.local) and table_node in table_node.parent.sources:
                    assign_i = table_node.parent.sources.index(table_node)
                    target_node = list_get(table_node.parent.targets, assign_i)
                    if target_node and target_node.type == NodeType.var:
                        table_name = target_node.name

                        if not explicit and target_node.var and target_node.var.keys_kind != None:
                            return compute_effective_kind(node, target_node.var.keys_kind, explicit=True)
            
            if (table_name, node.name) in preserved_members:
                member_excludes.add(node.name)
                return None
            elif table_name == "_ENV" or members_as_globals:
                return compute_effective_kind(node, VarKind.global_, explicit=True)

        elif kind == VarKind.global_:
            if not explicit:
                env_var = node.extra_children[0].var
                if env_var and env_var.keys_kind != None:
                    return compute_effective_kind(node, env_var.keys_kind, explicit=True)

            if node.var.implicit or node.name in preserved_globals:
                global_excludes.add(node.name)
                return None

        elif kind == VarKind.local:
            if node.var.builtin and node.name not in preserved_globals:
                # special case for when we wish to unpreserve a builtin local - turn it into a global
                node.var = root.globals[node.name]
                node.kind = VarKind.global_
                return compute_effective_kind(node, node.kind, explicit=True)

            if node.var.implicit or node.var.builtin:
                local_excludes[node.name].add(node.var)
                return None
            # best to keep this check, e.g. to avoid renaming _ENV locals that are unused unless local builtins are disabled
            elif node.name == "_ENV":
                return None

        return kind

    def is_after_zero(node):
        if not node.is_extra_child():
            prev = node.prev_token()
            # TODO: would be good to rename after minify?
            if prev.type == TokenType.number and prev.value.endswith("0"):
                return True

    def collect_idents_pre(node):            
        if node.type == NodeType.var:
            node.effective_kind = compute_effective_kind(node, default(node.var_kind, node.kind), explicit=e(node.var_kind))
            
            if node.effective_kind == VarKind.member:
                member_uses[node.name] += 1
                if is_after_zero(node):
                    members_after_zero.add(node.name)
            
            elif node.effective_kind == VarKind.global_:
                global_uses[node.name] += 1
                if is_after_zero(node):
                    globals_after_zero.add(node.name)
            
            elif node.effective_kind == VarKind.local:
                local_uses[node.var] += 1
                if is_after_zero(node):
                    locals_after_zero.add(node.var)
            
            elif node.effective_kind == VarKind.label:
                label_uses[node.var] += 1
                    
            # add to the scope based on real kind, as we need to avoid conflicts with preserved vars too
            if node.kind == VarKind.global_:
                for scope in node.scope.chain():
                    if node.effective_kind == VarKind.member: # rare, e.g. see --[[member-keys]] example
                        scope.used_members.add(node.name)
                    else:
                        scope.used_globals.add(node.name)

            elif node.kind in (VarKind.local, VarKind.label):
                for scope in node.scope.chain():
                    scope.used_locals.add(node.var)
                    if scope == node.var.scope:
                        break
                        
        elif node.type == NodeType.sublang:
            for name, count in node.lang.get_global_usages().items():
                if is_identifier(name):
                    if name in preserved_globals:
                        global_excludes.add(name)
                    else:
                        global_uses[name] += count

            for name, count in node.lang.get_member_usages().items():
                if is_identifier(name):
                    if name in preserved_members:
                        member_excludes.add(name)
                    else:
                        member_uses[name] += count

            for var, count in node.lang.get_local_usages().items():
                if not var.implicit:
                    local_uses[var] += count

    root.traverse_nodes(collect_idents_pre, extra=True)

    # assign new names to identifiers

    def get_next_ident_char(ch, first):
        nextch = ident_char_order_map.get(ch) if ch else ident_chars[0]
        while first and nextch and nextch.isdigit():
            nextch = ident_char_order_map.get(nextch)
        if nextch:
            return nextch, True
        else:
            return ident_chars[0], False

    def get_idents():
        """a generator of new identifiers, in the ideal order"""
        next_ident = ""

        while True:
            for i in range(len(next_ident)-1, -1, -1):
                next_ch, found = get_next_ident_char(next_ident[i], i==0)
                next_ident = str_replace_at(next_ident, i, 1, next_ch)
                if found:
                    break
            else:
                next_ident = str_insert(next_ident, 0, get_next_ident_char(None, True)[0])
            if next_ident not in keywords:
                yield next_ident

    def are_vars_compatible(var1, var2):
        is_global1 = var1.kind in (VarKind.global_, VarKind.member)
        is_global2 = var2.kind in (VarKind.global_, VarKind.member)

        if is_global1 and is_global2: # both globals/members
            return var1.kind != var2.kind
        
        elif is_global1 or is_global2:
            gvar, lvar = (var1, var2) if is_global1 else (var2, var1)
            if lvar.kind == VarKind.label:
                return True
            
            if gvar.kind == VarKind.global_ and lvar.scope.has_used_globals and gvar.name in lvar.scope.used_globals:
                return False
            if gvar.kind == VarKind.member and lvar.scope.has_used_members and gvar.name in lvar.scope.used_members:
                return False
            return True

        else: # both locals/labels
            if var1.kind == var2.kind:
                return var1 not in var2.scope.used_locals and var2 not in var1.scope.used_locals
            else:
                return True
    
    remaining_locals = list(sorted(local_uses, key=lambda k: local_uses[k], reverse=True))
    remaining_globals = list(sorted(global_uses, key=lambda k: global_uses[k], reverse=True))
    remaining_members = list(sorted(member_uses, key=lambda k: member_uses[k], reverse=True))
    remaining_labels = list(sorted(label_uses, key=lambda k: label_uses[k], reverse=True))

    local_renames, global_renames, member_renames, label_renames = {}, {}, {}, {}

    def try_select_var(sel, excluded, renames, avoids, ident, var_map=None):
        sel_var = var_map[sel] if var_map else sel
        
        if sel in avoids:
            return False

        for exclude in excluded:
            if not are_vars_compatible(sel_var, exclude):
                return False

        excluded.append(sel_var)
        renames[sel] = ident
        return True

    def select_var(remaining, excluded, renames, avoids, ident, var_map=None, i=0):
        while i < len(remaining):
            if try_select_var(remaining[i], excluded, renames, avoids, ident, var_map):
                del remaining[i]
                return i
            i += 1

    def select_vars(remaining, excluded, renames, avoids, ident):
        i = 0
        while i != None:
            i = select_var(remaining, excluded, renames, avoids, ident, i=i)

    for ident in get_idents():
        if not remaining_locals and not remaining_globals and not remaining_members and not remaining_labels:
            break

        avoid_locals = avoid_globals = avoid_members = ()
        for ch in "bxBX": # these chars cause extra space if placed after 0
            if ident.startswith(ch):
                avoid_locals, avoid_globals, avoid_members = locals_after_zero, globals_after_zero, members_after_zero

        if ident != "_ENV":
            excluded = []
            if ident in global_excludes:
                excluded.append(root.globals[ident])
            if ident in member_excludes:
                excluded.append(root.members[ident])
            if ident in local_excludes:
                excluded.extend(local_excludes[ident])

            if not focus.chars: # going over locals first seems to usually increase compression (TODO...)
                select_vars(remaining_locals, excluded, local_renames, avoid_locals, ident)
                select_var(remaining_globals, excluded, global_renames, avoid_globals, ident, root.globals)
                select_var(remaining_members, excluded, member_renames, avoid_members, ident, root.members)
            else:
                select_var(remaining_globals, excluded, global_renames, avoid_globals, ident, root.globals)
                select_var(remaining_members, excluded, member_renames, avoid_members, ident, root.members)
                select_vars(remaining_locals, excluded, local_renames, avoid_locals, ident)

        if remaining_labels:
            excluded = list(label_excludes[ident])
            select_vars(remaining_labels, excluded, label_renames, (), ident)

    if renamed_vars:
        for var1, var2 in itertools.product(renamed_vars, renamed_vars):
            if var1 != var2 and var1.rename == var2.rename and not are_vars_compatible(var1, var2):
                throw(f"rename hint of {var1.name} to {var1.rename} conflicts with that of {var2.name} to {var2.rename}")

    # output the identifier mapping, if needed

    def update_srcmap(mapping, kind=None):
        for old, new in mapping.items():
            old_name = old.name if isinstance(old, VarBase) else old

            ctxt.srcmap.append(f"{kind or old.kind} {from_p8str(new)} <- {from_p8str(old_name)}")

    if e(ctxt.srcmap):
        update_srcmap(member_renames, VarKind.member)
        update_srcmap(global_renames, VarKind.global_)
        update_srcmap(local_renames)
        update_srcmap(label_renames)
        update_srcmap({var: var.rename for var in renamed_vars})

    # write the new names into the syntax tree

    def update_idents(node):
        if node.type == NodeType.var:
            orig_name = node.name

            if node.effective_kind == VarKind.member:
                node.name = member_renames[node.name]
            elif node.effective_kind == VarKind.global_:
                node.name = global_renames[node.name]
            elif node.effective_kind == VarKind.local:
                node.name = local_renames[node.var]
            elif node.effective_kind == VarKind.label:
                node.name = label_renames[node.var]
            elif node.var.rename:
                orig_name = node.var.name # (node.name already renamed)
            else:
                return

            # need to update the tokens as well...
            if node.parent.type == NodeType.const: # const string interpreted as identifier case
                assert len(node.parent.children) == 1 and node.parent.extra_names[node.extra_i] == orig_name
                node.parent.extra_names[node.extra_i] = node.name
                node.parent.children[0].modify(format_string_literal("".join(node.parent.extra_names)))
            else:
                assert len(node.children) == 1 and node.children[0].value == orig_name
                node.children[0].modify(node.name)
                
        elif node.type == NodeType.sublang:
            node.lang.rename(globals=global_renames, members=member_renames, locals=local_renames)
            
    root.traverse_nodes(update_idents, extra=True)
