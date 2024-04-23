from utils import *
from pico_tokenize import TokenNodeBase, Token, TokenType
from pico_tokenize import is_identifier, parse_string_literal, k_identifier_split_re

k_nested = object()

class VarKind(Enum):
    local = global_ = member = label = ...
    
class VarBase():
    def __init__(m, kind, name):
        m.kind = kind
        m.name = name
        m.is_const = None
        m.implicit = False # has implicit *access*?
        m.reassigned = 0

    keys_kind = None
    rename = None
    constval = None
        
    def __repr__(m):
        return f"{m.kind} {m.name}"

class Local(VarBase):
    def __init__(m, name, scope, builtin=False):
        super().__init__(VarKind.local, name)
        m.scope = scope
        m.builtin = builtin
        m.captured = False

class Global(VarBase):
    def __init__(m, name):
        super().__init__(VarKind.global_, name)

class Member(VarBase):
    def __init__(m, name):
        super().__init__(VarKind.member, name)

class Label(VarBase):
    def __init__(m, name, scope):
        super().__init__(VarKind.label, name)
        m.scope = scope

class Scope:
    def __init__(m, parent=None, depth=0, funcdepth=0):
        m.parent = parent
        m.depth = depth
        m.funcdepth = funcdepth
        m.items = {}

    def add(m, var):
        m.items[var.name] = var

    def find(m, name):
        var = m.items.get(name)
        if var:
            return var
        elif m.parent:
            return m.parent.find(name)
    
    def chain(m):
        curr = m
        while curr:
            yield curr
            curr = curr.parent
    
    @lazy_property
    def used_locals(m): # set of Local or Label objs
        return set()
    
    @lazy_property
    def used_globals(m): # set of names, not of Global objs
        return set()
    @property
    def has_used_globals(m):
        return lazy_property.is_set(m, "used_globals")
    
    @lazy_property
    def used_members(m): # set of names, not of Member objs
        # note - only for members used as if they were globals,
        # NOT for normally used members! (very rare)
        return set()
    @property
    def has_used_members(m):
        return lazy_property.is_set(m, "used_members")

class LabelScope:
    def __init__(m, parent=None, funcdepth=0):
        m.parent = parent
        m.funcdepth = funcdepth
        m.labels = None
    
    def add(m, var):
        if m.labels is None:
            m.labels = {}
        m.labels[var.name] = var
    
    def find(m, name, crossfunc=False):
        var = m.labels.get(name) if m.labels else None
        if var:
            return var
        elif m.parent and (crossfunc or m.parent.funcdepth == m.funcdepth):
            return m.parent.find(name)
    
    def chain(m, crossfunc=False):
        curr = m
        while curr:
            yield curr
            curr = curr.parent if (crossfunc or curr.parent.funcdepth == curr.funcdepth) else None
    
    # for implementation reuse with locals, we stored used labels in used_locals
        
    @lazy_property
    def used_locals(m):
        return set()
    @property
    def has_used_locals(m):
        return lazy_property.is_set(m, "used_locals")
    
    @property
    def has_used_globals(m):
        return False
    @property
    def has_used_members(m):
        return False

class NodeType(Enum):
    var = index = member = const = group = unary_op = binary_op = call = ...
    table = table_index = table_member = varargs = assign = op_assign = ...
    local = function = if_ = elseif = else_ = while_ = repeat = until = ...
    for_ = for_in = return_ = break_ = goto = label = block = do = ...
    sublang = ... # special

class Node(TokenNodeBase):
    """A pico8 syntax tree node, spanning 'source'.text['idx':'endidx']. Its 'type' is a NodeType
    Its 'children' is a list of the Tokens and Nodes that comprise it (for traversal purposes),
    while each node type has additional properties specifying the relevant children (search for the NodeType below to find out which)."""

    def __init__(m, type, children, **kwargs):
        super().__init__()

        m.type, m.children = type, children
        m.__dict__.update(kwargs)

        for child in children:
            child.parent = m
    
    def get_tokens(m): # (not including erased tokens, whereas traverse includes them)
        tokens = []
        def on_token(token):
            if token.value != None:
                tokens.append(token)
        m.traverse_tokens(on_token)
        return tokens
    
    short = False # default property
    assignment = False # default proprerty
    value = None # default proprty (TODO: bad, for consistency with Token)

    @property
    def source(m):
        return m.first_token().source
    @property
    def idx(m):
        return m.first_token().idx
    @property
    def endidx(m):
        return m.last_token().endidx

    def _create_for_insert(m, i, type, value, near_next):
        if near_next:
            if i < len(m.children):
                return Token.synthetic(type, value, m.children[i], prepend=True)
            else:
                return Token.synthetic(type, value, m.next_token(), prepend=True)
        else:
            if i > 0:
                return Token.synthetic(type, value, m.children[i - 1], append=True)
            else:
                return Token.synthetic(type, value, m.prev_token(), append=True)

    def insert_token(m, i, type, value, near_next=False):
        m.children.insert(i, m._create_for_insert(i, type, value, near_next))
        m.children[i].parent = m

    def append_token(m, type, value, near_next=False):
        m.children.append(m._create_for_insert(len(m.children), type, value, near_next))
        m.children[-1].parent = m

    def modify_token(m, i, value, expected=None):
        m.children[i].modify(value, expected)
    
    def erase_token(m, i, expected=None):
        m.children[i].erase(expected)

    def remove_token(m, i, expected=None):
        if expected != None:
            m.children[i].check(expected)
        del m.children[i]

    def insert_existing(m, i, existing, near_next=False):
        src = m._create_for_insert(i, None, None, near_next)
        def reset_location(token):
            token.idx, token.endidx = src.idx, src.endidx
            token.vline, token.modified = None, True

        existing.traverse_tokens(reset_location)
        m.children.insert(i, existing)
        m.children[i].parent = m

    def append_existing(m, existing, near_next=False):
        m.insert_existing(len(m.children), existing, near_next)

    def remove_child(m, i):
        del m.children[i]

    def replace_with(m, target): # target must not reference m, but may reference m.copy() or m.move()
        old_parent = m.parent
        m.__dict__ = target.__dict__
        m.parent = old_parent
        for child in m.children:
            child.parent = m
    
    def erase(m):
        m.replace_with(Node(None, []))

class ParseError(Exception):
    pass

k_unary_ops = {
    "-", "~", "not", "#", "@", "%", "$",
}

k_unary_ops_prec = 11

k_binary_op_precs = {
    "or": 1, "and": 2,
    "!=": 3, "~=": 3, "==": 3, "<": 3, "<=": 3, ">": 3, ">=": 3,
    "|": 4, "^^": 5, "~": 5, "&": 6,
    "<<": 7, ">>": 7, ">>>": 7, ">><": 7, "<<>": 7,
    "..": 8,
    "+": 9, "-": 9,
    "*": 10, "/": 10, "\\": 10, "%": 10,
    "^": 12,
}

k_right_binary_ops = {
    "^", ".."
}

k_block_ends = ("end", "else", "elseif", "until")

k_prefix_types = (NodeType.var, NodeType.member, NodeType.index, NodeType.call, NodeType.group)

def parse(source, tokens, ctxt=None):
    idx = 0
    depth = -1 # incremented in parse_block
    funcdepth = -1 # incremented in parse_root
    scope = Scope(None, depth, funcdepth)
    labelscope = LabelScope(None, funcdepth)
    unresolved_labels = None
    errors = []
    globals = LazyDict(lambda key: Global(key))
    members = LazyDict(lambda key: Member(key))
    has_env = False
    
    scope.add(Local("_ENV", scope))

    if ctxt and ctxt.local_builtins:
        for local in ctxt.local_builtins:
            scope.add(Local(local, scope, builtin=True))
   
    def peek(off=0):
        i = idx + off
        return tokens[i] if 0 <= i < len(tokens) else Token.dummy(source)
    
    def take():
        nonlocal idx
        token = peek()
        idx += 1
        return token
    
    def accept(value, tokens=None):
        nonlocal idx
        if peek().value == value:
            if e(tokens):
                tokens.append(peek())
            idx += 1
            return True
        return False

    def add_error_at(msg, token, fail=False):
        errors.append(Error(msg, token))
        if fail:
            raise ParseError()

    def add_error(msg, off=0, fail=False):
        add_error_at(msg, peek(off), fail)

    def require(value, tokens=None):
        if not accept(value, tokens):
            add_error(f"expected '{value}'", fail=True)
        return peek(-1)

    def require_ident(tokens=None):
        nonlocal idx
        if peek().type == TokenType.ident:
            if e(tokens):
                tokens.append(peek())
            idx += 1
            return peek(-1)
        add_error("identifier expected", fail=True)

    def parse_var(token=None, new=None, member=False, label=False, implicit=False, const=None):
        token = token or require_ident()
        name = token.value

        var = None
        search_scope = None
        
        if member:
            kind = VarKind.member
            var = members[name]

        elif label:
            kind = VarKind.label
            search_scope = labelscope

            if new:
                var = Label(name, labelscope)
            # else, can't resolve until func ends

        else:
            kind = VarKind.local
            search_scope = new or scope

            if new:
                assert isinstance(new, Scope)
                var = Local(name, new)
            else:
                var = scope.find(name)
                if var and var.scope.funcdepth != scope.funcdepth:
                    var.captured = True
            
            if not var:
                kind = VarKind.global_
                var = globals[name]
                if ctxt and ctxt.consts and name in ctxt.consts:
                    var.is_const = True
                    var.constval = ctxt.consts[name]
            
            if name == "_ENV" and not implicit:
                nonlocal has_env
                has_env = True

        if implicit and var:
            var.implicit = True

        var_kind = getattr(token, "var_kind", None)

        if var:
            if hasattr(token, "keys_kind"):
                var.keys_kind = token.keys_kind
            if hasattr(token, "rename"):
                var.rename = token.rename
            
            const = getattr(token, "is_const", const)
            if const != None:
                var.is_const = const

        node = Node(NodeType.var, [token], name=name, kind=kind, var_kind=var_kind, var=var, new=bool(new), scope=search_scope)

        if label and not new:
            nonlocal unresolved_labels
            if unresolved_labels is None:
                unresolved_labels = []
            unresolved_labels.append(node)
        
        if kind == VarKind.global_:
            env_token = Token.synthetic(TokenType.ident, "_ENV", token)
            node.add_extra_child(parse_var(token=env_token, implicit=True))

        return node
    
    def parse_function(stmt=False, local=False):
        nonlocal scope, funcdepth, unresolved_labels
        if local:
            tokens = [peek(-2), peek(-1)]
        else:
            tokens = [peek(-1)]
        self_param = None
        func_kind = getattr(tokens[0], "func_kind", None)

        if local:
            scope = Scope(scope, depth, funcdepth)
        
        target, name = None, None
        funcscope = Scope(scope, depth + 1, funcdepth + 1)

        params = []
        if stmt:
            if local:
                target = parse_var(new=scope)
                scope.add(target.var)
                name = target.name
                
            else:
                target = parse_var()
                name = target.name

                while accept("."):
                    token = peek(-1)
                    key = parse_var(member=True)
                    target = Node(NodeType.member, [target, token, key], key=key, child=target, method=False)
                    name += "." + key.name

                if accept(":"):
                    token = peek(-1)
                    key = parse_var(member=True)
                    target = Node(NodeType.member, [target, token, key], key=key, child=target, method=True)
                    name += ":" + key.name

                    self_token = Token.synthetic(TokenType.ident, "self", target, append=True)
                    self_param = parse_var(token=self_token, new=funcscope, implicit=True)
                    params.append(self_param)
                
                mark_reassign(target)

            tokens.append(target)

        require("(", tokens)
        if not accept(")", tokens):
            while True:
                if accept("..."):
                    params.append(Node(NodeType.varargs, [peek(-1)]))
                else:
                    params.append(parse_var(new=funcscope))
                tokens.append(params[-1])

                if accept(")", tokens):
                    break
                require(",", tokens)

        for param in params:
            if param.type == NodeType.var:
                funcscope.add(param.var)
                
        old_unresolved = unresolved_labels
        unresolved_labels = None

        funcdepth += 1
        scope = funcscope
        body = parse_block()
        tokens.append(body)
        require("end", tokens)
        scope = scope.parent
        funcdepth -= 1
        
        late_resolve_labels()
        unresolved_labels = old_unresolved

        funcnode = Node(NodeType.function, tokens, target=target, params=params, body=body, name=name, kind=func_kind)
        if self_param:
            funcnode.add_extra_child(self_param)
        return funcnode

    def parse_table():
        tokens = [peek(-1)]
        keys_kind = getattr(tokens[0], "keys_kind", None)
        
        items = []
        while not accept("}", tokens):
            if accept("["):
                open = peek(-1)
                key = parse_expr()
                close = require("]")
                eq = require("=")
                value = parse_expr()
                items.append(Node(NodeType.table_index, [open, key, close, eq, value], key=key, value=value))

            elif peek(1).value == "=":
                key = parse_var(member=True)
                eq = require("=")
                value = parse_expr()
                items.append(Node(NodeType.table_member, [key, eq, value], key=key, value=value))
                
            else:
                items.append(parse_expr())
                
            tokens.append(items[-1])

            if accept("}", tokens):
                break

            if not accept(";", tokens):
                require(",", tokens)

        return Node(NodeType.table, tokens, items=items, keys_kind=keys_kind)

    def parse_call(expr, extra_arg=None):
        tokens = [expr, peek(-1)]
        args = []

        if extra_arg:
            args.append(extra_arg) # not a direct token

        if not accept(")", tokens):
            while True:
                args.append(parse_expr())
                tokens.append(args[-1])

                if accept(")", tokens):
                    break
                require(",", tokens)
        
        return Node(NodeType.call, tokens, func=expr, args=args)

    def parse_const(token):
        node = Node(NodeType.const, [token], token=token)

        if getattr(token, "var_kind", None):
            node.extra_names = k_identifier_split_re.split(parse_string_literal(token.value))
            for i, value in enumerate(node.extra_names):
                if is_identifier(value):
                    subtoken = Token.synthetic(TokenType.ident, value, token)
                    subtoken.var_kind = token.var_kind
                    node.add_extra_child(parse_var(token=subtoken, member=True))
                else:
                    subtoken = Token.synthetic(TokenType.string, value, token)
                    node.add_extra_child(parse_const(subtoken))

        if hasattr(token, "sublang"):
            sublang_token = Token.synthetic(TokenType.string, "", token)
            node.add_extra_child(Node(NodeType.sublang, (sublang_token,), name=token.sublang_name, lang=token.sublang))

        return node

    def parse_core_expr():
        token = take()
        value = token.value
        if value == None:
            add_error("unexpected end of input", fail=True)
        elif value in ("nil", "true", "false") or token.type in (TokenType.number, TokenType.string):
            return parse_const(token)
        elif value == "{":
            return parse_table()
        elif value == "(":
            expr = parse_expr()
            close = require(")")
            return Node(NodeType.group, [token, expr, close], child=expr)
        elif value in k_unary_ops:
            expr = parse_expr(k_unary_ops_prec)
            return Node(NodeType.unary_op, [token, expr], child=expr, op=value)
        elif value == "?":
            return parse_print()
        elif value == "function":
            return parse_function()
        elif value == "...":
            return Node(NodeType.varargs, [token])
        elif token.type == TokenType.ident:
            return parse_var(token=token)
        else:
            add_error("unknown expression", fail=True)

    def compare_prec(op, prec):
        return (prec == None) or ((prec <= k_binary_op_precs[op]) if op in k_right_binary_ops else (prec < k_binary_op_precs[op]))

    def parse_expr(prec=None):
        expr = parse_core_expr()
        while True:
            nonlocal idx
            token = take()
            value = token.value
            if value == "." and expr.type in k_prefix_types:
                var = parse_var(member=True)
                expr = Node(NodeType.member, [expr, token, var], key=var, child=expr, method=False)
            elif value == "[" and expr.type in k_prefix_types:
                index = parse_expr()
                close = require("]")
                expr = Node(NodeType.index, [expr, token, index, close], key=index, child=expr)
            elif value == "(" and expr.type in k_prefix_types:
                expr = parse_call(expr)
            elif (value == "{" or peek(-1).type == TokenType.string) and expr.type in k_prefix_types:
                idx -= 1
                arg = parse_core_expr()
                expr = Node(NodeType.call, [expr, arg], func=expr, args=[arg])
            elif value == ":" and expr.type in k_prefix_types:
                var = parse_var(member=True)
                expr = Node(NodeType.member, [expr, token, var], key=var, child=expr, method=True)
                if peek().value == "{" or peek().type == TokenType.string:
                    arg = parse_core_expr()
                    expr = Node(NodeType.call, [expr, arg], func=expr, args=[var, arg])
                else:
                    require("(")
                    expr = parse_call(expr, extra_arg=var)
            elif value in k_binary_op_precs and compare_prec(value, prec):
                other = parse_expr(k_binary_op_precs[value])
                expr = Node(NodeType.binary_op, [expr, token, other], left=expr, right=other, op=value)
            else:
                idx -= 1
                return expr

    def parse_list(tokens, func):
        list = [func()]
        tokens.append(list[-1])
        while accept(",", tokens):
            list.append(func())
            tokens.append(list[-1])
        return list
    
    def short_state(vline):
        return k_nested if peek().vline == vline else True

    def parse_if(type=NodeType.if_):
        tokens = [peek(-1)]
        cond = parse_expr()
        tokens.append(cond)
        else_ = None
        short = False

        if accept("then", tokens) or accept("do", tokens):
            then = parse_block()
            tokens.append(then)

            if accept("else"):
                else_tokens = [peek(-1)]
                else_body = parse_block()
                else_tokens.append(else_body)
                require("end", else_tokens)
                else_ = Node(NodeType.else_, else_tokens, body=else_body, short=False)
                tokens.append(else_)

            elif accept("elseif"):
                else_ = parse_if(NodeType.elseif)
                tokens.append(else_)

            else:
                require("end", tokens)
                
        elif peek(-1).value == ")":
            vline = peek(-1).vline
            then = parse_block(vline=vline)
            tokens.append(then)

            if peek().vline == vline and accept("else"):
                else_tokens = [peek(-1)]
                else_body = parse_block(vline=vline)
                else_tokens.append(else_body)
                else_ = Node(NodeType.else_, else_tokens, body=else_body, short=short_state(vline))
                tokens.append(else_)
                
            short = short_state(vline)

        else:
            add_error("then or shorthand required", fail=True)
            
        return Node(type, tokens, cond=cond, then=then, else_=else_, short=short)

    def parse_while():
        tokens = [peek(-1)]
        cond = parse_expr()
        tokens.append(cond)
        short = False

        if accept("do", tokens):
            body = parse_block()
            tokens.append(body)
            require("end", tokens)
        elif peek(-1).value == ")":
            vline = peek(-1).vline
            body = parse_block(vline=vline)
            tokens.append(body)
            short = short_state(vline)
        else:
            add_error("do or shorthand required", fail=True)

        return Node(NodeType.while_, tokens, cond=cond, body=body, short=short)

    def parse_repeat():
        tokens = [peek(-1)]
        body, until = parse_block(with_until=True)
        tokens.append(body)
        tokens.append(until)
        repeat = Node(NodeType.repeat, tokens, body=body, until=until)
        return repeat

    def parse_until():
        tokens = []
        require("until", tokens)
        cond = parse_expr()
        tokens.append(cond)
        return Node(NodeType.until, tokens, cond=cond)
        
    def parse_for():
        nonlocal scope
        tokens = [peek(-1)]

        if peek(1).value == "=":
            newscope = Scope(scope, depth + 1, funcdepth)
            target = parse_var(new=newscope)
            tokens.append(target)
            require("=", tokens)
            min = parse_expr()
            tokens.append(min)
            require(",", tokens)
            max = parse_expr()
            tokens.append(max)
            step = None
            if accept(",", tokens):
                step = parse_expr()
                tokens.append(step)

            require("do", tokens)
            newscope.add(target.var)

            scope = newscope
            body = parse_block()
            tokens.append(body)
            require("end", tokens)
            scope = scope.parent

            return Node(NodeType.for_, tokens, target=target, min=min, max=max, step=step, body=body)

        else:
            newscope = Scope(scope, depth + 1, funcdepth)
            targets = parse_list(tokens, lambda: parse_var(new=newscope))
            require("in", tokens)
            sources = parse_list(tokens, parse_expr)
            require("do", tokens)

            for target in targets:
                newscope.add(target.var)

            scope = newscope
            body = parse_block()
            tokens.append(body)
            require("end", tokens)
            scope = scope.parent

            return Node(NodeType.for_in, tokens, targets=targets, sources=sources, body=body)

    def parse_return(vline):
        tokens = [peek(-1)]
        if peek().value in k_block_ends + (";",) or (e(vline) and peek().vline > vline):
            return Node(NodeType.return_, tokens, items=[])
        else:
            rets = parse_list(tokens, parse_expr)
            return Node(NodeType.return_, tokens, items=rets)
        
    def parse_print():
        tokens = [peek(-1)]
        args = parse_list(tokens, parse_expr)
        # explicitly represent the implicit use of print
        print_token = Token.synthetic(TokenType.ident, "print", tokens[0])
        func = parse_var(token=print_token, implicit=True)
        node = Node(NodeType.call, tokens, func=func, args=args, short=True)
        node.add_extra_child(func)
        return node

    def parse_local():
        nonlocal scope
        tokens = [peek(-1)]
        newscope = Scope(scope, depth, funcdepth)

        const = getattr(tokens[0], "is_const", None)
        targets = parse_list(tokens, lambda: parse_var(new=newscope, const=const))
        sources = []
        if accept("=", tokens):
            sources = parse_list(tokens, parse_expr)
            
        for target in targets:
            newscope.add(target.var)
        scope = newscope

        return Node(NodeType.local, tokens, targets=targets, sources=sources)

    def mark_reassign(target):
        target.assignment = True
        if target.type == NodeType.var and target.var:
            target.var.reassigned += 1

    def parse_assign(first):
        tokens = [first]
        if accept(",", tokens):
            targets = [first] + parse_list(tokens, parse_expr)
        else:
            targets = [first]

        require("=", tokens)
        sources = parse_list(tokens, parse_expr)

        for target in targets:
            mark_reassign(target)

        return Node(NodeType.assign, tokens, targets=targets, sources=sources)

    def parse_opassign(first):
        nonlocal idx
        token = peek()
        op = token.value[:-1]
        idx += 1
        source = parse_expr()
        mark_reassign(first)
        return Node(NodeType.op_assign, [first, token, source], target=first, source=source, op=op)

    def parse_misc_stmt():
        nonlocal idx
        idx -= 1
        first = parse_expr()
        if peek().value in (",", "="):
            return parse_assign(first)
        elif peek().value and peek().value.endswith("="):
            return parse_opassign(first)
        elif first.type == NodeType.call:
            return first
        else:
            add_error("expression has no side-effect")

    def parse_stmt(vline):
        token = take()
        value = token.value
        if value == ";":
            return None
        elif value == "do":
            body = parse_block()
            end = require("end")
            return Node(NodeType.do, [token, body, end], body=body)
        elif value == "if":
            return parse_if()
        elif value == "while":
            return parse_while()
        elif value == "repeat":
            return parse_repeat()
        elif value == "for":
            return parse_for()
        elif value == "break":
            return Node(NodeType.break_, [token])
        elif value == "return":
            return parse_return(vline)
        elif value == "local":
            if accept("function"):
                return parse_function(stmt=True, local=True)
            else:
                return parse_local()
        elif value == "goto":
            label = parse_var(label=True)
            return Node(NodeType.goto, [token, label], label=label)
        elif value == "::":
            label = parse_var(label=True, new=True)
            labelscope.add(label.var)
            end = require("::")
            return Node(NodeType.label, [token, label, end], label=label)
        elif value == "function":
            return parse_function(stmt=True)
        else:
            return parse_misc_stmt()

    def parse_block(vline=None, with_until=False):
        nonlocal scope, labelscope, depth
        oldscope = scope
        labelscope = LabelScope(labelscope, funcdepth)
        depth += 1

        stmts = []
        tokens = []
        while e(peek().type):
            if e(vline) and peek().vline > vline:
                break

            if peek().value in k_block_ends:
                break
            
            stmt = parse_stmt(vline)
            if stmt:
                stmts.append(stmt)
                tokens.append(stmt)
            else:
                tokens.append(peek(-1))

        if with_until:
            until = parse_until()

        depth -= 1
        labelscope = labelscope.parent
        while scope != oldscope:
            scope = scope.parent
        
        node = Node(NodeType.block, tokens, stmts=stmts)
        if with_until:
            return node, until
        else:
            return node
    
    def late_resolve_labels():
        if unresolved_labels:
            for node in unresolved_labels:
                node.var = node.scope.find(node.name)
                if not node.var:
                    add_error_at(f"Unknown label {node.name}", node.children[0])

    def parse_root():
        nonlocal funcdepth
        funcdepth += 1

        root = parse_block()
        root.globals = globals
        root.members = members
        root.has_env = has_env

        funcdepth -= 1

        late_resolve_labels()
        if peek().type != None:
            add_error("Expected end of input")
        if idx < len(tokens):
            root.children.append(take()) # extra comments/etc
        assert scope.parent is None
        #verify_parse(root) # DEBUG
        return root

    def verify_parse(root):
        def visitor(token):
            nonlocal idx
            assert token == tokens[idx]
            idx += 1

        nonlocal idx
        idx = 0
        root.traverse_tokens(visitor)
        assert idx == len(tokens)

    try:
        return parse_root(), errors
    except ParseError:
        return None, errors

# node utils

def is_assign_target(node):
    return node.parent.type == NodeType.assign and node in node.parent.targets
def is_op_assign_target(node):
    return node.parent.type == NodeType.op_assign and node == node.parent.target
def is_function_target(node):
    return node.parent.type == NodeType.function and node == node.parent.target
def is_any_assign_target(node):
    return is_assign_target(node) or is_op_assign_target(node) or is_function_target(node)

def is_global_or_builtin_local(node):
    return node.kind == VarKind.global_ or (node.kind == VarKind.local and node.var.builtin)

def is_vararg_expr(node):
    return node.type in (NodeType.call, NodeType.varargs)
def is_short_block_stmt(node):
    return node.short and node.type in (NodeType.if_, NodeType.else_, NodeType.while_)
def is_function_stmt(node):
    return node.type == NodeType.function and node.target

def get_precedence(node):
    if node.type == NodeType.binary_op:
        return k_binary_op_precs[node.op]
    elif node.type == NodeType.unary_op:
        return k_unary_ops_prec

def is_right_assoc(node):
    if node.type == NodeType.binary_op:
        return node.op in k_right_binary_ops
    else:
        return False

def can_replace_with_unary(node):
    parent = node.parent
    if not parent or (parent.type == NodeType.binary_op and parent.right is node):
        return True
    else:
        prec = get_precedence(parent)
        return prec is None or prec < k_unary_ops_prec

from pico_process import Error
