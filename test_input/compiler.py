from pico_process import CustomCompilerBase

def preprocess_main(args, **_):
    global g_script_args
    g_script_args = args.script_args

# An example of a compiler which converts pico8 to some fictive readable representation
# of bytecode. (A real compiler would probably convert directly to bytecode, or something else)
# This example shows how to handle the various syntax nodes
class BytecodeCompiler(CustomCompilerBase):
    # Called with the args (if any) that we receive on the --use-compiler line
    def __init__(self, args, **_):
        # args is a string and can be parsed via shlex + argparse
        split_args = args.split() # (or we could be lazy and do this)
        self.minimal = "--minimal-interpreter" in split_args
        self.desugar = "--desugar" in split_args or "--desugar" in g_script_args
        
        # the idea is that the args can specify the variant of the interpreter to use,
        # which is important to know both when constructing the interpreter and when
        # compiling the code.

        # You can request "desugarring" of some syntax, meaning instead of receiving those
        # syntax nodes, you will receive an equivalent representation using simpler nodes
        # If setting these to True, you don't need to handle the corresponding case in the visitor below.
        self.desugar_function_stmt = True # you probably always want this
        self.desugar_repeat = self.desugar
        self.desugar_for = self.desugar
        self.desugar_for_in = self.desugar
        self.desugar_op_assign = self.desugar

        self.next_anon_i = 0
        self.anon_names = {}
    
    # Optional - only needed if you want to construct the interpreter dynamically based on the args
    # If defined, should return the interpreter pico8 code - which'll be prepended to the cart's code
    # TODO: how to handle multiple identical compilers in the same cart? (src param on __init__ may help)
    # TODO: support placing the code elsewhere?
    def get_prepend_code(self, **_):
        if self.minimal:
            return "function interp(code) --[[not relevant for example]] end"
        else:
            return "function interp(code) --[[still not relevant for example, but larger]] end"

    # Should return pico8 code that will execute a compiled string
    # The returned code must mark the string that will eventually contain the compiled code 
    # with a dummy --[[preserve]] marker (the string will be filled by Shrinko8)
    # (You could have it compile instead of execute the code, depending on the (above) args)
    # TODO: what if you want to put the compiled code in the ROM instead?
    def get_execute_code(self, **_):
        # NOTE - you probably want "" instead of [[]], only using [[]] for easier test updates
        return 'interp(--[[preserve]][[]])'
    
    # Receives an AST, should output the compiled string (as a p8str)
    # (Should output string content, not string literal)
    # Should output an error via on_error(msg,node) if it fails compiling
    # Can output a warning via on_warn(msg,node) if needed
    def compile(self, root, on_error, on_warn, **_):
        bytecodes = [] # a real compiler would put bytes here. We'd put readable strings

        from pico_tokenize import TokenType, parse_fixnum, parse_string_literal
        from pico_parse import Node, NodeType, VarKind
        from pico_minify import format_fixnum, format_string_literal
        from itertools import zip_longest

        k_unary_bytecodes = {
            "-": "minus", "~": "bnot", "not": "not", "#": "length",
            "@": "peek", "%": "peek2", "$": "peek4"
        }
        k_binary_bytecodes = {
            "+": "add", "-": "sub", "*": "mul", "/": "div",
            "\\": "idiv", "%": "mod", "^": "pow",
            "&": "band", "|": "bor", "^^": "bxor",
            "<<": "shl", ">>": "sar", ">>>": "shr", "<<>": "rol", ">><": "ror",
            "..": "cat",
            "<": "lt", "<=": "le", ">": "gt", ">=": "ge",
            "==": "eq", "~=": "ne"
        }

        next_branch_target = 0
        def create_branch_target():
            nonlocal next_branch_target
            next_branch_target += 1
            return str(next_branch_target)

        # note - here we adhere to strict varargs behaviour as specified by lua
        # (up to the fact that this code wasn't tested and have bugs!)
        # nothing prevents your own compiler from not doing so (or doing so just under an arg)

        # our expression visitor function.
        # allow_vararg is True if we're allowed to write a vararg to the stack
        # if we do write a vararg, we return True as well.
        # otherwise, we add one value in the stack
        def visit_expr(node, allow_vararg=False):

            if node.type == NodeType.const: # a literal
                const = node.token
                if const.value in ("true", "false", "nil"): # these 3 literals
                    bytecodes.append(const.value)
                
                elif const.type == TokenType.number: # number literal
                    # a fixnum is a 32bit unsigned integer representing a pico8 number
                    fixnum = parse_fixnum(const.value)
                    # you can encode it in the bytecode, or minify it as a string via format_fixnum
                    bytecodes.append("num:" + format_fixnum(fixnum, allow_minus=True))
                
                elif const.type == TokenType.string: # string literal
                    # strval is the actual string value
                    strval = parse_string_literal(const.value)
                    # you can encode it as you wish, or minify it back to a literal via format_string_literal
                    bytecodes.append("str:" + format_string_literal(strval, long=False, quote="'"))

                else:
                    on_error(f"unknown const type {const.type}", node)
            
            elif node.type == NodeType.var: # a variable reference
                # use node.name for the variable name (do NOT use node.var.name)
                # for locals & upvalues:
                #   node.var.scope is the Scope where the variable is defined
                #   node.scope is the Scope where the variable is used
                #   see Scope in pico_parse

                if node.kind == VarKind.local and not node.upvalue: # a local reference
                    bytecodes.append("local:" + node.name)
                elif node.kind == VarKind.anon: # only occurs when desugaring op_assign/for/for_in. may get replaced with proper locals in the future.
                    if node.var not in self.anon_names:
                        self.anon_names[node.var] = str(self.next_anon_i)
                        self.next_anon_i += 1
                    bytecodes.append("anon:" + self.anon_names[node.var])
                elif node.kind == VarKind.local and node.upvalue: # an upvalue reference
                    bytecodes.append("upval:" + node.name)
                elif node.kind == VarKind.global_: # a global reference
                    bytecodes.append("global:" + node.name)
                else:
                    on_error(f"unknown var kind {node.kind}", node)
                    
            elif node.type == NodeType.varargs: # ...
                bytecodes.append("varargs")
                if allow_vararg:
                    return True # returning a vararg
                else:
                    bytecodes.append("unpack:1") # only one return value needed
            
            elif node.type == NodeType.group: # ( node.child )
                visit_expr(node.child)
                # (parentheses disable varargs behaviour, in our case this happens
                #  automatically since allow_vararg is not forwarded to node.child)

            elif node.type == NodeType.member: # node.child . node.key.name
                visit_expr(node.child)
                bytecodes.append("member:" + node.key.name)
            
            elif node.type == NodeType.index: # node.child [ node.key ]
                visit_expr(node.child)
                visit_expr(node.key)
                bytecodes.append("index")
            
            elif node.type == NodeType.unary_op: # node.op node.child
                visit_expr(node.child)
                bytecode = k_unary_bytecodes.get(node.op)
                if bytecode:
                    bytecodes.append(bytecode)
                else:
                    on_error(f"unknown unary op {node.op}", node)
            
            elif node.type == NodeType.binary_op: # node.left node.op node.right
                if node.op in ("and", "or"): # short-circuiting ops
                    visit_expr(node.left)
                    short_circ_branch = create_branch_target()
                    bytecodes.append(node.op + ":" + short_circ_branch)
                    visit_expr(node.right)
                    bytecodes.append("target:" + short_circ_branch)
                
                else: # regular binary ops
                    visit_expr(node.left)
                    visit_expr(node.right)
                    bytecode = k_binary_bytecodes.get(node.op)
                    if bytecode:
                        bytecodes.append(bytecode)
                    else:
                        on_error(f"unknown binary op {node.op}", node)

            elif node.type == NodeType.call: # node.func ( node.args )
                if node.func.type == NodeType.member and node.func.method:
                    # method call:    node.func.child : node.func.key.name ( node.args[1:] )
                    visit_expr(node.func.child)
                    bytecodes.append("method:" + node.func.key.name)
                    args = node.args[1:] # node.args[0] is just node.func.child again

                else:
                    # normal function call
                    visit_expr(node.func)
                    args = node.args
                
                # visit the args, the last one may be varargs
                args_vararg = False
                for i, arg in enumerate(args):
                    args_vararg = visit_expr(arg, allow_vararg=(i == len(args) - 1))
                
                nargs = str(len(node.args)) + ("&va" if args_vararg else "")
                if allow_vararg: # can we return vararg?
                    bytecodes.append("vacall:" + nargs)
                    return True # we return vararg
                else:
                    bytecodes.append("call:" + nargs)
            
            elif node.type == NodeType.table: # { node.items }
                bytecodes.append("table")

                for i, item in enumerate(node.items):
                    bytecodes.append("dup") # the table created above (just for the sake of example)

                    if item.type == NodeType.table_member: # item.key.name = item.value
                        visit_expr(item.value)
                        bytecodes.append("setmember:" + item.key.name)

                    elif item.type == NodeType.table_index: # [item.key] = item.value
                        visit_expr(item.key)
                        visit_expr(item.value)
                        bytecodes.append("setindex")
                    
                    else: # item
                        item_varargs = visit_expr(item, allow_vararg=(i == len(node.items) - 1))
                        if item_varargs:
                            bytecodes.append("extend")
                        else:
                            bytecodes.append("append")
            
            elif node.type == NodeType.function: # function ( node.params ) { node.body }
                func_def_end = create_branch_target()
                bytecodes.append("func:" + func_def_end)

                # let's put the function body inline:

                # first set the params
                for param in reversed(node.params):
                    if param.type == NodeType.var: # regular param
                        bytecodes.append("setlocal:" + param.name)
                    elif param.type == NodeType.varargs: # varargs param (...)
                        bytecodes.append("setvarargs:-" + str(len(node.params) - 1))
                    else:
                        on_error(f"unknown param type {param.type}", param)
                
                visit_stmt(node.body)
                bytecodes.append("target:" + func_def_end)

                # we ignore node.target here, we handle it in visit_stmt
                
            else:
                on_error(f"unknown expr type {node.type}", node)

        break_target = None

        # our statement visitor function
        # adds nothing to the stack
        def visit_stmt(node):
            nonlocal break_target
            bytecodes.append("\n")

            if node.type in (NodeType.assign, NodeType.local): # node.targets = node.sources
                # easiest way to do this for a stack machine (which we purport to compile to) is 
                # to prepare everything in the stack first and assign everything second
                
                pairs = list(zip_longest(node.targets, node.sources))
                assign_varargs = False

                for i, (target, source) in enumerate(pairs):
                    if target is None: # assign to nowhere
                        pass
                    elif target.type == NodeType.var: # assign to var
                        pass
                    elif target.type == NodeType.member: # assign to member
                        visit_expr(target.child)
                    elif target.type == NodeType.index: # assign to index
                        visit_expr(target.child)
                        visit_expr(target.key)
                    else:
                        on_error(f"unknown assign target {target.type}", target)
                
                    if source is None:
                        if not assign_varargs:
                            bytecodes.append("nil")
                    else:
                        varargs_needed = max(len(node.targets) - i, 1)
                        assign_varargs = visit_expr(source, allow_vararg=(i == len(node.sources) - 1 and varargs_needed != 1))
                        if assign_varargs:
                            bytecodes.append("unpack:" + str(varargs_needed))

                for target, _ in reversed(pairs):
                    if target is None: # assign to nowhere
                        bytecodes.append("pop")
                    
                    elif target.type == NodeType.var: # assign to var
                        # normally, the logic here would be similar to the logic of
                        # the node.type == NodeType.var condition above. but let's cheat
                        visit_expr(target)
                        bytecodes[-1] = "set" + bytecodes[-1]
                    
                    elif target.type == NodeType.member: # assign to member
                        bytecodes.append("setmember:" + target.key.name)
                    
                    elif target.type == NodeType.index: # assign to index
                        bytecodes.append("setindex")

                    #else - already checked above
            
            elif node.type == NodeType.op_assign and not self.desugar_op_assign : # node.target node.op= node.src
                # we do a bit of work here to evaluate the target only once
                def do_op():
                    visit_expr(node.src)
                    bytecode = k_binary_bytecodes.get(node.op)
                    if bytecode:
                        bytecodes.append(bytecode)
                    else:
                        on_error(f"unknown binary op {node.op}", node)
                
                target = node.target
                if target.type == NodeType.var: # op-assign to var
                    visit_expr(target)
                    do_op()
                    visit_expr(target)
                    bytecodes[-1] = "set" + bytecodes[-1]

                elif target.type == NodeType.member: # op-assign to member
                    visit_expr(target.child)
                    bytecodes.append("dup")
                    bytecodes.append("member:" + target.key.name)
                    do_op()
                    bytecodes.append("setmember:" + target.key.name)

                elif target.type == NodeType.index: # op-assign to index
                    visit_expr(target.child)
                    visit_expr(target.key)
                    bytecodes.append("dup2")
                    bytecodes.append("index")
                    do_op()
                    bytecodes.append("setindex")

                else:
                    on_error(f"unknown op-assign target {target.type}", target)

            elif node.type in (NodeType.if_, NodeType.elseif): # if node.cond then node.then else node.else_ end
                visit_expr(node.cond)
                post_then = create_branch_target()
                bytecodes.append("ifnot:" + post_then)
                visit_stmt(node.then)

                if node.else_: # type: elseif or else_
                    post_if = create_branch_target()
                    bytecodes.append("goto:" + post_if)
                    bytecodes.append("target:" + post_then)
                    visit_stmt(node.else_)
                    bytecodes.append("target:" + post_if)
                else:
                    bytecodes.append("target:" + post_then)

            elif node.type in (NodeType.do, NodeType.else_): # just a block
                visit_stmt(node.body)

            elif node.type == NodeType.while_: # while node.cond do node.body end
                pre_loop = create_branch_target()
                post_loop = create_branch_target()
                old_break, break_target = break_target, post_loop
                
                bytecodes.append("target:" + pre_loop)
                visit_expr(node.cond)
                bytecodes.append("ifnot:" + post_loop)
                visit_stmt(node.body)
                bytecodes.append("goto:" + pre_loop)

                bytecodes.append("target:" + post_loop)
                break_target = old_break
            
            elif node.type == NodeType.repeat and not self.desugar_repeat: # repeat node.body until node.until.cond
                pre_loop = create_branch_target()
                post_loop = create_branch_target()
                old_break, break_target = break_target, post_loop
                
                bytecodes.append("target:" + pre_loop)
                visit_stmt(node.body)
                visit_expr(node.until.cond)
                bytecodes.append("ifnot:" + pre_loop)

                bytecodes.append("target:" + post_loop)
                break_target = old_break
            
            elif node.type == NodeType.for_ and not self.desugar_for: # for node.target = node.min , node.max [, node.step] do node.body end                
                pre_loop = create_branch_target()
                post_loop = create_branch_target()
                old_break, break_target = break_target, post_loop
                
                # for our simplicity, we'll write a high level loop
                # NOTE: for 100% accuracy, we'd want to call tonum on the below, though that's probably excessive
                visit_expr(node.min)
                visit_expr(node.max)
                if node.step:
                    visit_expr(node.step)
                else:
                    bytecodes.append("num:1")
                
                bytecodes.append("forinit:" + post_loop)
                bytecodes.append("target:" + pre_loop)
                bytecodes.append("setlocal:" + node.target.name)
                visit_stmt(node.body)
                bytecodes.append("fornext:" + pre_loop)

                bytecodes.append("target:" + post_loop)
                break_target = old_break
                
            elif node.type == NodeType.for_in and not self.desugar_for_in: # for node.targets in node.sources do node.body end
                pre_loop = create_branch_target()
                post_loop = create_branch_target()
                old_break, break_target = break_target, post_loop
                
                src_vararg = False
                for i, source in enumerate(node.sources):
                    src_vararg = visit_expr(source, allow_vararg=(i == len(node.sources) - 1))
                
                # we want exactly 3 vars
                needed_vars = 3
                if src_vararg:
                    bytecodes.append("unpack:" + str(max(needed_vars - len(node.sources) + 1, 0)))
                else:
                    for _ in range(len(node.sources), needed_vars):
                        bytecodes.append("nil")

                for _ in range(needed_vars, len(node.sources)):
                    bytecodes.append("pop")
                
                bytecodes.append("gforinit:" + post_loop)
                bytecodes.append("target:" + pre_loop)

                bytecodes.append("unpack:" + str(len(node.targets)))
                for target in reversed(node.targets):
                    bytecodes.append("setlocal:" + target.name)

                visit_stmt(node.body)
                bytecodes.append("gfornext:" + pre_loop)

                bytecodes.append("target:" + post_loop)
                break_target = old_break
                
            elif node.type == NodeType.break_: # break
                bytecodes.append("goto:" + break_target)

            elif node.type == NodeType.goto: # goto node.label
                bytecodes.append("goto:" + node.label.name)
                
            elif node.type == NodeType.label: # :: node.label ::
                bytecodes.append("target:" + node.label.name)
            
            elif node.type == NodeType.return_: # return node.items
                if len(node.items) == 1 and node.items[0].type == NodeType.call:
                    # a tail call
                    visit_expr(node.items[0])
                    bytecodes[-1] = "tail" + bytecodes[-1] # cheating again

                else: # a regular return
                    ret_vararg = False
                    for i, item in enumerate(node.items):
                        ret_vararg = visit_expr(item, allow_vararg=(i == len(node.items) - 1))
                    
                    nrets = str(len(node.items)) + ("&va" if ret_vararg else "")
                    bytecodes.append("ret:" + nrets)
                
            elif node.type == NodeType.function and node.target and not self.desugar_function_stmt: # function node.target ( node.params ) { node.body }
                # leaving this case here just for completion's sake, as we always set desugar_function_stmt
                on_error(f"not supported")

            elif node.type == NodeType.block: # a block of multiple statements
                for stmt in node.stmts:
                    visit_stmt(stmt)

            elif node.type == NodeType.call: # call expression as statement
                visit_expr(node)
                bytecodes.append("pop") # drop return value
            
            else:
                on_error(f"unknown stmt type {node.type}", node)

        # We should traverse manually, NOT via traverse_nodes
        # This allows us full control over the traverse order, etc.
        visit_stmt(root)

        return ",".join(bytecodes)
        # a real compiler would return:
        #return "".join(chr(x) for x in bytecodes)

# A (probably useless) example of a "compiler" that simply leaves the code as-is
# (well, it minifies it the same way as the toplevel code),
# leaving it up to a repl to parse it at runtime (NOT a good idea in real carts)
class ReplCompiler(CustomCompilerBase):
    def __init__(self, ctxt, **_):
        self.ctxt = ctxt

    def get_prepend_code(self, **_):
        return "function repl(str) --[[margins too short for implementation]] end"
    
    def get_execute_code(self, **_):
        return 'repl(--[[preserve]]"")'
    
    def compile(self, root, minify_opts, **_):
        from pico_minify import minify_code
        return minify_code(self.ctxt, root, minify_opts)

# this is called to get a custom compiler class by name
def compiler_main(lang, **_):
    if lang == "bytecode":
        return BytecodeCompiler
    elif lang == "repl":
        return ReplCompiler

