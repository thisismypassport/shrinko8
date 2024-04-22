from utils import *
from pico_defs import fixnum_is_negative, k_fixnum_mask, to_p8str
from pico_tokenize import Token, TokenType, ConstToken, k_skip_children, tokenize
from pico_parse import Node, NodeType, VarKind, is_global_or_builtin_local, is_vararg_expr
from pico_output import format_fixnum

class LuaType(Enum):
    nil = boolean = number = string = ...

class LuaValue:
    def __init__(m, type, value):
        m.type, m.value = type, value

    def is_number(m):
        return m.type == LuaType.number
    def is_string(m):
        return m.type == LuaType.string
    def is_truthy(m):
        return not (m.type == LuaType.nil or (m.type == LuaType.boolean and not m.value))

class LuaNil(LuaValue):
    def __init__(m):
        super().__init__(LuaType.nil, None)

class LuaBoolean(LuaValue):
    def __init__(m, value):
        super().__init__(LuaType.boolean, bool(value))

class LuaNumber(LuaValue):
    # (value must be a fixnum)
    def __init__(m, value):
        super().__init__(LuaType.number, value & k_fixnum_mask)
        
class LuaString(LuaValue):
    # (value must be a string)
    def __init__(m, value):
        super().__init__(LuaType.string, value)

k_lua_nil = LuaNil()
k_lua_true = LuaBoolean(True)
k_lua_false = LuaBoolean(False)
k_lua_maxint = 0x7fff

def fixnum_is_whole(value):
    return (value & 0xffff) == 0

def fixnum_to_whole(value):
    return value >> 16

def fixnum_to_signed(value):
    if value & 0x80000000:
        value -= 0x100000000
    return value

# no need for fixnum_from_signed - LuaNumber's masking does the job

def is_signed_fixnum_in_range(value):
    if value >= 0:
        return value < 0x80000000
    else:
        return value >= -0x80000000

# ops

def lua_neg(a):
    if a.is_number():
        return LuaNumber(-a.value)

def lua_abs(a):
    if a.is_number() and a.value != 0x80000000: # avoid relying on clamping overflow behavior
        return LuaNumber(abs(fixnum_to_signed(a.value)))

def lua_floor(a):
    if a.is_number():
        return LuaNumber(a.value & 0xffff0000)

def lua_ceil(a):
    if a.is_number():
        if a.value & 0xffff:
            a.value = (a.value & 0xffff0000) + 0x10000
            if a.value == 0x80000000: # avoid relying on wrapping overflow behavior
                return
        return LuaNumber(a.value)

def lua_add(a, b):
    if a.is_number() and b.is_number():
        return LuaNumber(a.value + b.value)

def lua_sub(a, b):
    if a.is_number() and b.is_number():
        return LuaNumber(a.value - b.value)

def lua_mul(a, b):
    if a.is_number() and b.is_number():
        result = (fixnum_to_signed(a.value) * fixnum_to_signed(b.value)) >> 16
        if is_signed_fixnum_in_range(result): # avoid relying on wrapping overflow behavior (or should we?)
            return LuaNumber(result)

def quot(a, b):
    if (a < 0) != (b < 0):
        return -(a // -b)
    else:
        return a // b

def lua_div(a, b):
    if a.is_number() and b.is_number() and b.value != 0: # avoid relying on div-by-0 behavior
        result = quot(fixnum_to_signed(a.value) << 16, fixnum_to_signed(b.value))
        if is_signed_fixnum_in_range(result): # avoid relying on clamping overflow behavior
            return LuaNumber(result)

def lua_idiv(a, b):
    c = lua_div(a, b)
    if c:
        return lua_floor(c)

def lua_mod(a, b):
    if a.is_number() and b.is_number() and b.value != 0 and not fixnum_is_negative(b.value): # avoid relying on mod-by-0 behavior, or on non-standard mod-by-neg behavior
        result = fixnum_to_signed(a.value) % fixnum_to_signed(b.value)
        if is_signed_fixnum_in_range(result): # probably always true, but just in case
            return LuaNumber(result)

def lua_eq(a, b):
    return LuaBoolean(a.type == b.type and a.value == b.value)
    
def lua_not_eq(a, b):
    return LuaBoolean(a.type != b.type or a.value != b.value)

def lua_less(a, b):
    if a.is_number() and b.is_number():
        return LuaBoolean(fixnum_to_signed(a.value) < fixnum_to_signed(b.value))
    elif a.is_string() and b.is_string():
        return LuaBoolean(a.value < b.value)

def lua_less_eq(a, b):
    if a.is_number() and b.is_number():
        return LuaBoolean(fixnum_to_signed(a.value) <= fixnum_to_signed(b.value))
    elif a.is_string() and b.is_string():
        return LuaBoolean(a.value <= b.value)

def lua_greater(a, b):
    if a.is_number() and b.is_number():
        return LuaBoolean(fixnum_to_signed(a.value) > fixnum_to_signed(b.value))
    elif a.is_string() and b.is_string():
        return LuaBoolean(a.value > b.value)

def lua_greater_eq(a, b):
    if a.is_number() and b.is_number():
        return LuaBoolean(fixnum_to_signed(a.value) >= fixnum_to_signed(b.value))
    elif a.is_string() and b.is_string():
        return LuaBoolean(a.value >= b.value)

def lua_max(a, b):
    if a.is_number() and b.is_number():
        return LuaNumber(max(fixnum_to_signed(a.value), fixnum_to_signed(b.value)))

def lua_min(a, b):
    if a.is_number() and b.is_number():
        return LuaNumber(min(fixnum_to_signed(a.value), fixnum_to_signed(b.value)))

def _mid(n1, n2, n3):
    b12, b23, b13 = n1 <= n2, n2 <= n3, n1 <= n3
    return n2 if b12 == b23 else n1 if b12 != b13 else n3

def lua_mid(a, b, c):
    if a.is_number() and b.is_number() and c.is_number():
        return LuaNumber(_mid(fixnum_to_signed(a.value), fixnum_to_signed(b.value), fixnum_to_signed(c.value)))

def lua_bin_not(a):
    if a.is_number():
        return LuaNumber(~a.value)

def lua_bin_and(a, b):
    if a.is_number() and b.is_number():
        return LuaNumber(a.value & b.value)

def lua_bin_or(a, b):
    if a.is_number() and b.is_number():
        return LuaNumber(a.value | b.value)

def lua_bin_xor(a, b):
    if a.is_number() and b.is_number():
        return LuaNumber(a.value ^ b.value)

def lua_shl(a, b):
    if a.is_number() and b.is_number():
        if fixnum_is_negative(b.value):
            if not fixnum_is_negative(a.value): # avoid relying on questionable shift-left-neg-by-neg behaviour
                return lua_lshr(a, lua_neg(b))
        elif fixnum_is_whole(b.value): # avoid relying on shift-by-fract behaviour
            return LuaNumber(a.value << fixnum_to_whole(b.value))

def lua_shr(a, b):
    if a.is_number() and b.is_number():
        if fixnum_is_negative(b.value):
            return lua_shl(a, lua_neg(b))
        elif fixnum_is_whole(b.value):
            return LuaNumber(fixnum_to_signed(a.value) >> fixnum_to_whole(b.value))

def lua_lshr(a, b):
    if a.is_number() and b.is_number():
        if fixnum_is_negative(b.value):
            return lua_shl(a, lua_neg(b))
        elif fixnum_is_whole(b.value):
            return LuaNumber(a.value >> fixnum_to_whole(b.value))

def lua_rotl(a, b):
    if a.is_number() and b.is_number():
        if fixnum_is_negative(b.value):
            return lua_rotr(a, lua_neg(b))
        elif fixnum_is_whole(b.value):
            return LuaNumber(rotate_left(a.value, fixnum_to_whole(b.value), 32))

def lua_rotr(a, b):
    if a.is_number() and b.is_number():
        if fixnum_is_negative(b.value):
            return lua_rotl(a, lua_neg(b))
        elif fixnum_is_whole(b.value):
            return LuaNumber(rotate_right(a.value, fixnum_to_whole(b.value), 32))

def lua_not(a):
    return LuaBoolean(not a.is_truthy())

def lua_and(a, b):
    return b if a.is_truthy() else a
    
def lua_or(a, b):
    return a if a.is_truthy() else b

def lua_len(a):
    if a.is_string() and len(a.value) <= k_lua_maxint: # avoid relying on long string behavior
        return LuaNumber(len(a.value) << 16)

def _lua_tostr(a):
    if a.is_string():
        return a
    elif a.is_number() and fixnum_is_whole(a.value): # avoid relying on fract. tostr
        return LuaString(format_fixnum(a.value, base=10, sign='-' if fixnum_is_negative(a.value) else ''))

def lua_cat(a, b):
    a, b = _lua_tostr(a), _lua_tostr(b)
    if a and b:
        return LuaString(a.value + b.value)

k_const_unary_ops = {
    "-": lua_neg,
    "~": lua_bin_not,
    "not": lua_not,
    "#": lua_len,
}

k_const_binary_ops = {
    "or": lua_or,
    "and": lua_and,
    "!=": lua_not_eq,
    "~=": lua_not_eq,
    "==": lua_eq,
    "<": lua_less,
    "<=": lua_less_eq,
    ">": lua_greater,
    ">=": lua_greater_eq,
    "|": lua_bin_or,
    "^^": lua_bin_xor,
    "~": lua_bin_xor,
    "&": lua_bin_and,
    "<<": lua_shl,
    ">>": lua_shr,
    ">>>": lua_lshr,
    "<<>": lua_rotl,
    ">><": lua_rotr,
    "..": lua_cat,
    "+": lua_add,
    "-": lua_sub,
    "*": lua_mul,
    "/": lua_div,
    "\\": lua_idiv,
    "%": lua_mod,
}

k_const_globals = {
    "abs": (lua_abs, 1),
    "band": (lua_bin_and, 2),
    "bnot": (lua_bin_not, 1),
    "bor": (lua_bin_or, 2),
    "bxor": (lua_bin_xor, 2),
    "ceil": (lua_ceil, 1),
    "flr": (lua_floor, 1),
    "lshr": (lua_lshr, 2),
    "max": (lua_max, 2),
    "mid": (lua_mid, 3),
    "min": (lua_min, 2),
    "rotl": (lua_rotl, 2),
    "rotr": (lua_rotr, 2),
    "shl": (lua_shl, 2),
    "shr": (lua_shr, 2),
}

def const_from_token(token):
    if token.type == TokenType.number:
        return LuaNumber(token.fixnum_value)
    elif token.type == TokenType.string:
        return LuaString(token.string_value)
    elif token.value == "nil":
        return k_lua_nil
    elif token.value == "true":
        return k_lua_true
    elif token.value == "false":
        return k_lua_false
    else:
        return None

def get_const(node):
    if node.type == NodeType.const:
        # compute & cache const value
        token = node.token
        constval = const_from_token(token)
        assert constval, "unexpected const token: %s" % token
        return constval
    elif node.type == NodeType.group:
        return get_const(node.child)
    else:
        return None

def set_const(node, value):
    if value.type == LuaType.number:
        token = ConstToken(TokenType.number, node, fixnum_value=value.value)
    elif value.type == LuaType.string:
        token = ConstToken(TokenType.string, node, string_value=value.value)
    elif value.type == LuaType.boolean:
        token = ConstToken(TokenType.keyword, node, value="true" if value.value else "false")
    elif value.type == LuaType.nil:
        token = ConstToken(TokenType.keyword, node, value="nil")
    else:
        assert False, "unexpected const value: %s" % value
    
    node.replace_with(create_const_node(token))

def fixup_syntax_between(parent, prev, next):
    nextt = next.first_token()
    if nextt and nextt.value == "(":
        prevt = prev.last_token()
        if prevt.value in (")", "]") or prevt.type == TokenType.ident:
            i = parent.children.index(prev)
            parent.insert_token(i+1, TokenType.punct, ";", near_next=True)

def fixup_syntax_after_remove(stmt):
    # after removing stmt (or even just part of stmt), extra semicolons may need to be inserted
    parent = stmt.parent
    if parent.type == NodeType.block:
        stmt_n = len(parent.stmts)
        stmt_i = parent.stmts.index(stmt)
        if stmt.type is None:
            if 0 < stmt_i < stmt_n - 1:
                fixup_syntax_between(parent, parent.stmts[stmt_i-1], parent.stmts[stmt_i+1])
        else:
            if stmt_i > 0:
                fixup_syntax_between(parent, parent.stmts[stmt_i-1], stmt)
            if stmt_i < stmt_n - 1:
                fixup_syntax_between(parent, stmt, parent.stmts[stmt_i+1])

def erase_assign_targets(node, indices):
    if len(node.targets) < len(node.sources) and len(indices) == len(node.targets):
        indices.pop() # can't deal with this easily otherwise

    def delete_array_item(node, array, i):
        child_i = node.children.index(array[i])
        node.remove_child(child_i)
        
        # need to delete comma too
        if i > 0:
            node.remove_token(child_i - 1, ",")
        elif len(array) > 1:
            node.remove_token(child_i, ",")
        elif node.type == NodeType.local and array is node.sources:
            node.remove_token(child_i - 1, "=")
        
        del array[i]

    for i in reversed(indices):
        delete_array_item(node, node.targets, i)
        if i < len(node.sources):
            delete_array_item(node, node.sources, i)
    
    if not node.targets and not node.sources:
        node.erase()
    elif not node.sources and node.type != NodeType.local:
        nil_token = Token.synthetic(TokenType.keyword, "nil", node, append=True)
        node.sources.append(create_const_node(nil_token))
        node.append_existing(node.sources[-1])
    else:
        assert node.targets # due to the pop above
    
    fixup_syntax_after_remove(node)

def create_const_node(token):
    return Node(NodeType.const, [token], token=token)

def create_do_node_if_needed(node):
    needed = False

    def check_do_needed(node):
        nonlocal needed
        if node.type == NodeType.var and node.new:
            needed = True
        elif node.type in (NodeType.return_, NodeType.break_, NodeType.goto):
            needed = True
        elif node.type in (NodeType.if_, NodeType.elseif, NodeType.while_, NodeType.repeat, NodeType.for_, NodeType.for_in, NodeType.do):
            return k_skip_children
        elif node.type == NodeType.function:
            if node.target:
                node.target.traverse_nodes(pre=check_do_needed)
            return k_skip_children

    node.traverse_nodes(pre=check_do_needed)
    if needed:
        do_token = Token.synthetic(TokenType.keyword, "do", node, prepend=True)
        end_token = Token.synthetic(TokenType.keyword, "end", node, append=True)
        node = Node(NodeType.do, [do_token, node, end_token], body=node)
    return node

def create_else_node(node, short=False):
    else_token = Token.synthetic(TokenType.keyword, "else", node, prepend=True)
    end_token = Token.synthetic(TokenType.keyword, "end", node, append=True)
    return Node(NodeType.else_, [else_token, node, end_token], body=node, short=short)

def remove_else_node(node):
    assert node.children[-1] is node.else_
    node.remove_child(-1)
    node.else_ = None
    end_token = Token.synthetic(TokenType.keyword, "end", node, append=True)
    node.append_existing(end_token)

def fold_consts(ctxt, root, errors):

    def add_error(msg, node):
        errors.append(Error(msg, node))

    in_const_ctxt = 0
    const_ctxt_fail = None

    def skip_special(node):
        if node.type in (NodeType.local, NodeType.assign):
            # we traverse these specially in update_node_constval
            return k_skip_children

    def update_node_constval(node):
        nonlocal in_const_ctxt, const_ctxt_fail
        # we don't check NodeType.const/group until needed (in get_const)

        if node.type == NodeType.unary_op:
            func = k_const_unary_ops.get(node.op, None)
            if func:
                child_const = get_const(node.child)
                if child_const:
                    constval = func(child_const)
                    if constval:
                        set_const(node, constval)

        elif node.type == NodeType.binary_op:
            func = k_const_binary_ops.get(node.op, None)
            if func:
                left_const = get_const(node.left)
                if left_const: # (optimization)
                    right_const = get_const(node.right)
                    if right_const:
                        constval = func(left_const, right_const)
                    elif func in (lua_and, lua_or): # short-circuit
                        constval = func(left_const, node.right)
                    else:
                        constval = None
                    
                    if constval:
                        if constval is node.right:
                            node.replace_with(node.right)
                        else:
                            set_const(node, constval)

        elif node.type == NodeType.var and node.var and not node.new and not node.assignment:
            if node.var.constval:
                set_const(node, node.var.constval)
            elif node.var.is_const:
                add_error(f"'{node.name}' is marked as constant but is used above where it is assigned to", node)
                node.var.is_const = False

        elif node.type in (NodeType.local, NodeType.assign):
            visit_assign(node)
        
        # we assume that in a const context, calls are always to builtins
        # TODO: can we be smarter in the non-safe-only case?
        elif node.type == NodeType.call and node.func.type == NodeType.var and is_global_or_builtin_local(node.func) \
                and not node.func.var.reassigned and (not root.has_env or in_const_ctxt):
            func, num_args = k_const_globals.get(node.func.name, (None, None))
            if func and (num_args is None or num_args == len(node.args)):
                arg_consts = []
                for arg in node.args:
                    arg_const = get_const(arg)
                    if arg_const:
                        arg_consts.append(arg_const)
                    else:
                        break # (optimization)
                else:
                    constval = func(*arg_consts)
                    if constval:
                        set_const(node, constval)
        
        elif node.type == NodeType.if_:
            constval = get_const(node.cond)
            if constval:
                if constval.is_truthy():
                    node.replace_with(create_do_node_if_needed(node.then))
                elif not node.else_:
                    node.erase()
                elif node.else_.type == NodeType.else_:
                    node.replace_with(create_do_node_if_needed(node.else_.body))
                else: # elseif
                    node.replace_with(node.else_)
                    node.modify_token(0, "if", expected="elseif")
                    node.type = NodeType.if_
                    
        elif node.type == NodeType.elseif:
            constval = get_const(node.cond)
            if constval:
                if constval.is_truthy():
                    node.replace_with(create_else_node(node.then, node.short))
                elif not node.else_:
                    remove_else_node(node.parent)
                else:
                    node.replace_with(node.else_)

        # store which node was expected to be const but isn't
        if in_const_ctxt and node.type != NodeType.const and const_ctxt_fail is None:
            if node.parent.type == NodeType.call and node == node.parent.func:
                pass
            else:
                const_ctxt_fail = node

    def visit_assign(node):
        nonlocal in_const_ctxt, const_ctxt_fail
        erasable = []

        for i, target in enumerate(node.targets):
            target.traverse_nodes(pre=skip_special, post=update_node_constval)

            if target.type == NodeType.var:
                is_const_ctxt = target.var.is_const
                # (even if a global is assigned once, it's hard to tell if all its uses are after the assignment, so we close globals under --[[const]])
                is_const = (target.kind == VarKind.local and not target.var.reassigned) or \
                           (is_const_ctxt and target.kind == VarKind.global_ and target.var.reassigned <= 1 and target.name not in ctxt.builtins)
            else:
                is_const = is_const_ctxt = False

            if is_const_ctxt:
                in_const_ctxt += 1
                const_ctxt_fail = None
                
            constval = None
            if is_const and is_const_ctxt != False:
                if i < len(node.sources):
                    source = node.sources[i]
                    source.traverse_nodes(pre=skip_special, post=update_node_constval)
                    constval = get_const(source)
                elif not (node.sources and is_vararg_expr(node.sources[-1])):
                    constval = k_lua_nil
            else:
                if i < len(node.sources):
                    node.sources[i].traverse_nodes(pre=skip_special, post=update_node_constval)
            
            if constval:
                if is_const_ctxt or not isinstance(constval, LuaString): # string const folding may balloon total char count
                    erasable.append(i)
                    if not target.var.constval: # may've been set to something else through ctxt.consts
                        target.var.constval = constval
            else:
                if is_const_ctxt:
                    reason = ""
                    if const_ctxt_fail:
                        reason = f" due to '{const_ctxt_fail.source_text}'"
                    elif not is_const:
                        reason = f" due to being reassigned"
                    add_error(f"Local '{target.name}' is marked as const but its value cannot be determined" + reason, target)
                    target.var.is_const = False
                    
            if is_const_ctxt:
                in_const_ctxt -= 1
                const_ctxt_fail = None
        
        for i, source in enumerate(node.sources):
            if i >= len(node.targets): # else, traversed above
                source.traverse_nodes(pre=skip_special, post=update_node_constval)
        
        if erasable:
            erase_assign_targets(node, erasable)

    root.traverse_nodes(pre=skip_special, post=update_node_constval)

def parse_constant(value, as_str=False):
    if as_str:
        return LuaString(to_p8str(value))

    tokens, errors = tokenize(Source(None, to_p8str(value)))
    if not errors:
        token = None
        if len(tokens) == 1:
            token = tokens[0]
        elif len(tokens) == 2 and tokens[0].value in ("-", "~") and tokens[1].type == TokenType.number:
            token = tokens[1]
            token.value = tokens[0].value + token.value
                    
        if token:
            constval = const_from_token(token)
            if constval:
                return constval

from pico_process import Error, Source
