from utils import *
from pico_defs import from_p8str
from pico_tokenize import TokenType, is_identifier, keywords
from pico_parse import VarKind, NodeType, VarBase
from pico_minify import format_string_literal, Focus
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

def rename_tokens(ctxt, root, rename):
    global_strings_cpy = ctxt.builtins | global_callbacks
    preserved_globals = IncludeExcludeMapping(global_strings_cpy)
    preserved_members = TableMemberPairIncludeExcludeMapping(members=member_strings)
    members_as_globals = safe_only = False
    focus = Focus.none

    # read rename options (e.g. what to preserve)

    if isinstance(rename, dict):
        members_as_globals = rename.get("members=globals", False)
        safe_only = rename.get("safe-only", False)
        focus = Focus(rename.get("focus", "none"))
        rules_input = rename.get("rules")
        if rules_input:
            for key, value in rules_input.items():
                if "." in key:
                    preserved_members.set(key.split(".", 1), not value)
                else:
                    preserved_globals.set(key, not value)

    # detect which renames are safe to do, if requested
    # (note - this assumes a "pure" cart with no hints for shrinko8)

    if safe_only:
        preserved_members.default = True # can't reasonably guarantee safety of this
        
        def check_safety(node):
            if node.type == NodeType.var and node.kind != VarKind.member and node.name == "_ENV":
                preserved_globals.default = True

        root.traverse_nodes(check_safety)

    # collect char histogram
    # (reusing commonly used chars in our new identifiers lowers compressed size)

    char_uses = CounterDictionary()
    def collect_chars(token):
        if token.type != TokenType.ident:# (TODO: beneficial but maybe more can be done) or \
                #token.value in (preserved_members if token.parent.type in (NodeType.member, NodeType.table_member) else preserved_globals):
            sublang = getattr(token, "sublang", None)
            if sublang and sublang.get_unminified_chars:
                for ch in sublang.get_unminified_chars():
                    char_uses[ch] += 1
            else:
                for ch in token.value:
                    char_uses[ch] += 1

    root.traverse_tokens(collect_chars)

    # TODO: something must still be unoptimal with char_uses collection, as hardcoding k_identifier_chars is more helpful than going by uses...
    if focus == Focus.chars:
        k_identifier_chars = string.ascii_letters + string.digits + "_\x1e\x1f" + "".join(chr(x) for x in range(0x80,0x100))
    elif focus == Focus.none:
        k_identifier_chars = string.ascii_letters + string.digits + "_"
    else:
        k_identifier_chars = string.ascii_lowercase + string.digits + "_"
    
    ident_chars = []
    for ch in sorted(char_uses, key=lambda k: char_uses[k], reverse=True):
        if ch in k_identifier_chars:
            ident_chars.append(ch)
    
    for ch in k_identifier_chars:
        if ch not in ident_chars:
            ident_chars.append(ch)

    ident_char_order_map = {ch1: ch2 for ch1, ch2 in zip(ident_chars, ident_chars[1:])}

    # collect uses of identifier
    # (e.g. to give priority to more frequently used ones)

    global_uses = CounterDictionary()
    member_uses = CounterDictionary()
    local_uses = CounterDictionary()
    label_uses = CounterDictionary()
    
    # we avoid renaming into any names used by pico8/lua, as otherwise renamed variables may have a non-nill initial value
    global_excludes = global_strings_cpy
    member_excludes = member_strings.copy()
    global_excludes.add("_ENV")
    member_excludes.add("_ENV")

    def compute_effective_kind(node, kind, explicit):
        """get the identifier kind (global/member/etc) of a node, taking into account hints in the code"""
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
            elif table_name == "_ENV":
                return compute_effective_kind(node, VarKind.global_, explicit=True)
            
            if members_as_globals:
                kind = VarKind.global_

        elif kind == VarKind.global_:
            if not explicit:
                env_var = node.scope.find("_ENV")
                if env_var and env_var.keys_kind != None:
                    return compute_effective_kind(node, env_var.keys_kind, explicit=True)

            if node.name in preserved_globals:
                global_excludes.add(node.name)
                return None

        elif kind == VarKind.local:
            if node.var.implicit:
                return None
            elif node.name == "_ENV": # e.g. new locals named it
                return None

        return kind

    def collect_idents_pre(node):            
        if node.type == NodeType.var:
            node.effective_kind = compute_effective_kind(node, default(node.var_kind, node.kind), explicit=e(node.var_kind))
            
            if node.effective_kind == VarKind.member:
                member_uses[node.name] += 1
            elif node.effective_kind == VarKind.global_:
                global_uses[node.name] += 1
            elif node.effective_kind == VarKind.local:
                local_uses[node.var] += 1
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
        while first and nextch and (nextch.isdigit() or nextch == '_'): # note: we avoid leading underscores too
            nextch = ident_char_order_map.get(nextch)
        if nextch:
            return nextch, True
        else:
            return ident_chars[0], False

    def create_ident_stream():
        """returns a function that can be called to return new identifiers, in the ideal order"""
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

    def assign_idents(uses, excludes):
        """assign new names to the given identifiers, in usage frequency order, and ignoring unwanted names"""
        ident_stream = create_ident_stream()
        rename_map = {}

        for value in sorted(uses, key=lambda k: uses[k], reverse=True):
            while True:
                ident = ident_stream()
                if ident not in excludes and ident not in keywords:
                    break

            rename_map[value] = ident

        return rename_map

    member_renames = assign_idents(member_uses, member_excludes)
    global_renames = assign_idents(global_uses, global_excludes)

    class ReverseRenameMap:
        def __init__(m, map):
            m.map = map
            m.revmap = None
        
        def get(m, ident):
            if m.revmap is None:
                m.revmap = {v: k for k, v in m.map.items()}
            
            orig_ident = m.revmap.get(ident)
            if orig_ident is None and ident not in m.map:
                orig_ident = ident # could be one we didn't rename
            return orig_ident

    rev_member_renames = ReverseRenameMap(member_renames)
    rev_global_renames = ReverseRenameMap(global_renames)    
    
    def assign_locals_idents(uses, excludes):
        """assign new names to the locals' identifiers, like assign_idents but trickier as it takes scopes into account"""
        ident_stream = create_ident_stream()
        rename_map = {}

        remaining_uses = list(sorted(uses, key=lambda k: uses[k], reverse=True))
        while remaining_uses:
            ident = ident_stream()
            ident_global, ident_member = None, None
            ident_locals = []

            if ident in excludes or ident in keywords:
                continue
            
            for i, var in enumerate(remaining_uses):
                if var.scope.has_used_globals:
                    if ident_global is None:
                        ident_global = rev_global_renames.get(ident)
                    if ident_global in var.scope.used_globals:
                        continue
                
                if var.scope.has_used_members:
                    if ident_member is None:
                        ident_member = rev_member_renames.get(ident)
                    if ident_member in var.scope.used_members:
                        continue
                
                for _, ident_local in ident_locals:
                    if ident_local in var.scope.used_locals:
                        break
                    if var in ident_local.scope.used_locals:
                        break

                else:
                    rename_map[var] = ident
                    ident_locals.append((i, var))

            for i, ident_local in reversed(ident_locals):
                assert remaining_uses.pop(i) == ident_local

        return rename_map
        
    local_renames = assign_locals_idents(local_uses, ("_ENV",))
    label_renames = assign_locals_idents(label_uses, ())

    # output the identifier mapping, if needed

    def update_srcmap(mapping, kind):
        for old, new in mapping.items():
            old_name = old.name if isinstance(old, VarBase) else old

            ctxt.srcmap.append("%s %s <- %s" % (kind, from_p8str(new), from_p8str(old_name)))

    if e(ctxt.srcmap):
        update_srcmap(member_renames, "member")
        update_srcmap(global_renames, "global")
        update_srcmap(local_renames, "local")
        update_srcmap(label_renames, "label")

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
