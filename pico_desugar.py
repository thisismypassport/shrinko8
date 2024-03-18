from utils import *
from pico_defs import fixnum_is_negative, k_fixnum_mask
from pico_tokenize import Token, TokenType
from pico_parse import Node, NodeType, Scope, Local, VarKind
from pico_output import format_fixnum

def synthesize_const_node(strval, type, src):
    node = Node.synthetic(src, NodeType.const, (type, strval))
    node.token = node.children[0]
    return node

def synthesize_binary_op_node(op, left, right):
    return Node.synthetic(left, NodeType.binary_op, left, op, right, left=left, right=right, op=op)

def synthesize_call_node(func, *args):
    joined_args = []
    for arg in args:
        if joined_args:
            joined_args.append(",")
        joined_args.append(arg)
    
    return Node.synthetic(func, NodeType.call, func, "(", *joined_args, ")", func=func, args=args)

def synthesize_assign_node(targets, sources, type=NodeType.assign):
    if not isinstance(targets, list): targets = [targets]
    if not isinstance(sources, list): sources = [sources]

    any_node = targets[0] if targets else sources[0]
    return Node.synthetic(any_node, type, *targets, "=", *sources, targets=targets, sources=sources)

def synthesize_new_anon_var_node(scope, src):
    var = Local("", scope)
    return Node.synthetic(src, NodeType.var, var.name, name=var.name, kind=VarKind.anon, var_kind=VarKind.anon, var=var, upvalue=False, new=True, scope=scope)

def synthesize_var_node(local, scope):
    return Node.synthetic(local, NodeType.var, local.name, name=local.name, kind=local.kind, var_kind=local.kind, var=local.var, upvalue=False, new=False, scope=scope)

def synthesize_local_node(targets, sources):
    return synthesize_assign_node(targets, sources, type=NodeType.local)

def synthesize_break_node(src):
    return Node.synthetic(src, NodeType.break_, "break")

def synthesize_if_node(cond, then): # TODO: else
    return Node.synthetic(cond, NodeType.if_, "if", cond, "then", then, "end",
                          cond=cond, then=then, else_=None, short=False)

def synthesize_while_node(cond, body):
    return Node.synthetic(cond, NodeType.while_, "while", cond, "do", body, "end",
                          cond=cond, body=body, short=False)

def synthesize_do_block_node(*stmts):
    any_node = stmts[0]
    body = Node.synthetic(any_node, NodeType.block, *stmts, stmts=stmts)
    return Node.synthetic(any_node, NodeType.do, "do", body, "end", body=body)

def desugar_unary_const(node): # TEMP, until proper constfold
    if node.op in ("-", "~") and node.child.type == NodeType.const and node.child.token.type == TokenType.number:
        value = node.child.token.fixnum_value
        value = (~value if node.op == "~" else -value) & k_fixnum_mask
        node = synthesize_const_node(format_fixnum(value, allow_minus=True), TokenType.number, src=node)
        # hopefully not needed:
        #node = Node.synthetic(node, NodeType.group, "(", node, ")", child=node)
    return node

def desugar_function_stmt(node):
    assign_type = NodeType.local if node.local else NodeType.assign

    target = node.target.copy_and_erase()
    node.target = None

    return synthesize_assign_node(target, node, type=assign_type)

def desugar_repeat(body, until):
    if_node = synthesize_if_node(until.cond, synthesize_break_node(src=until))

    true_node = synthesize_const_node("true", TokenType.keyword, src=body)
    while_body = synthesize_do_block_node(body, if_node)
    return synthesize_while_node(true_node, while_body)

def args_to_locals_if_needed(args, scope, force=(), safe=False, count=None, replace=False):
    needed = []
    for i, arg in enumerate(args):
        # WARNING: skipping globals changes semantics if there's an _ENV metatable (TODO: avoid under 'accurate' flag)
        # and, conversely, not skipping locals under 'safe' is quite wasteful...
        if i not in force and (arg.type == NodeType.const or (not safe and arg.type == NodeType.var)):
            continue
        needed.append(i)

    max_force = max(force, default=None)
    if e(max_force) and max_force >= len(args): # needed due to varargs case
        for i in range(len(args), max_force + 1):
            needed.append(i)
    
    if not needed:
        return None, args
    
    # for now, we won't create proper renamable locals here (would require way more work to get scope/etc right)
    #new_scope = Scope(scope, scope.depth + 1, scope.funcdepth)
    locals = []
    local_sources = []
    for i in needed:
        arg = list_get(args, i)
        if count is None or i < count:
            locals.append(synthesize_new_anon_var_node(scope, src=(arg or args[0])))
        if arg:
            if replace:
                local_sources.append(arg.copy_and_erase())
            else:
                local_sources.append(arg)
    
    new_args = []
    for i, arg in enumerate(args):
        needed_i = list_find(needed, i)
        if needed_i >= 0:
            local = list_get(locals, needed_i)
            if local:
                new_arg = synthesize_var_node(local, scope)
                new_args.append(new_arg)
                if replace:
                    arg.replace_with(new_arg)
            else:
                new_args.append(arg)
        else:
            new_args.append(arg)

    if e(count):
        while len(new_args) < count:
            local_i = len(locals) - (count - len(new_args))
            new_arg = synthesize_var_node(locals[local_i], scope)
            new_args.append(new_arg)

    return synthesize_local_node(locals, local_sources), new_args

def desugar_op_assign(target, source, op, scope):
    if target.type == NodeType.member:
        local_stmt, _ = args_to_locals_if_needed([target.child], scope, replace=True)
    elif target.type == NodeType.index:
        local_stmt, _ = args_to_locals_if_needed([target.child, target.key], scope, replace=True)
    else:
        local_stmt = None

    op_node = synthesize_binary_op_node(op, target, source)
    assign_node = synthesize_assign_node(target.copy(), op_node)

    if local_stmt:
        return synthesize_do_block_node(local_stmt, assign_node)
    else:
        return assign_node
    
def desugar_for(target, min, max, step, body, scope): # WARNING: does not include tonum calls (TODO: include under 'accurate' flag)
    for_args = [min, max]
    if step:
        for_args.append(step)
    
    local_stmt, for_args = args_to_locals_if_needed(for_args, scope, force=(0,), safe=True)
    i_var, limit_arg, step_arg = list_unpack(for_args, 3)

    if not step_arg:
        step_arg = synthesize_const_node("1", TokenType.number, src=target)
    
    if step and step.type == NodeType.const and step.token.type == TokenType.number:
        step_neg = fixnum_is_negative(step.token.fixnum_value)
    else:
        step_neg = None if step else False

    if step_neg == False:
        while_cond = synthesize_binary_op_node("<=", i_var, limit_arg)
    elif step_neg == True:
        while_cond = synthesize_binary_op_node(">=", i_var, limit_arg)
    else:
        zero = synthesize_const_node("0", TokenType.number, src=target)
        pos_check = synthesize_binary_op_node(">", step_arg.copy(), zero)
        pos_cond = synthesize_binary_op_node("and", pos_check, synthesize_binary_op_node("<=", i_var, limit_arg))
        neg_check = synthesize_binary_op_node("<=", step_arg.copy(), zero.copy())
        neg_cond = synthesize_binary_op_node("and", neg_check, synthesize_binary_op_node(">=", i_var.copy(), limit_arg.copy()))
        while_cond = synthesize_binary_op_node("or", pos_cond, neg_cond)

    inner_local = synthesize_local_node(target, i_var.copy())
    update_local = synthesize_assign_node(i_var.copy(), synthesize_binary_op_node("+", i_var.copy(), step_arg))
    while_body = synthesize_do_block_node(inner_local, body, update_local)
    
    while_stmt = synthesize_while_node(while_cond, while_body)
    return synthesize_do_block_node(local_stmt, while_stmt)
        
def desugar_for_in(targets, sources, body, scope):
    local_stmt, for_args = args_to_locals_if_needed(sources, scope, force=(2,), safe=True, count=3)
    func_arg, state_arg, iter_arg = list_unpack(for_args, 3)

    if not state_arg:
        state_arg = synthesize_const_node("nil", TokenType.keyword, src=body)

    nil_node = synthesize_const_node("nil", TokenType.keyword, src=body)
    if_cond = synthesize_binary_op_node("==", targets[0], nil_node)
    if_node = synthesize_if_node(if_cond, synthesize_break_node(src=body))

    call_node = synthesize_call_node(func_arg, state_arg, iter_arg)
    inner_local = synthesize_local_node(targets, call_node)
    update_local = synthesize_assign_node(iter_arg.copy(), targets[0])
    while_body = synthesize_do_block_node(inner_local, if_node, update_local, body)

    true_node = synthesize_const_node("true", TokenType.keyword, src=body)
    while_stmt = synthesize_while_node(true_node, while_body)
    return synthesize_do_block_node(local_stmt, while_stmt)
    

