from utils import *
from pico_tokenize import TokenType, is_identifier
from pico_parse import VarKind, NodeType, Global

def lint_code(ctxt, tokens, root, lint_rules):
    errors = []
    vars = defaultdict(list)
    builtin_globals = ctxt.globals
    custom_globals = set()

    lint_undefined = lint_unused = lint_duplicate = True
    if isinstance(lint_rules, dict):
        lint_undefined = lint_rules.get("undefined", True)
        lint_unused = lint_rules.get("unused", True)
        lint_duplicate = lint_rules.get("duplicate", True)

    for token in tokens:
        if token.type == TokenType.lint:
            for value in token.value:
                custom_globals.add(value)

    def add_error(msg, node):
        err = Error(msg, node)
        errors.append(err)

    # find global assignment, and check for uses

    used_locals = set()
    assigned_locals = set()

    def is_assign_target(node):
        return node.parent.type == NodeType.assign and node in node.parent.targets
    def is_op_assign_target(node):
        return node.parent.type == NodeType.op_assign and node == node.parent.target
    def is_function_target(node):
        return node.parent.type == NodeType.function and node == node.parent.target

    def preprocess_vars(node):        
        if node.type == NodeType.var:
            if node.kind == VarKind.global_ and node.name not in custom_globals:
                assign = False
                if is_assign_target(node):
                    func = node.find_parent(NodeType.function)
                    assign = True
                elif is_function_target(node):
                    func = node.parent.find_parent(NodeType.function)
                    assign = True

                if assign and (func == None or func.kind == "_init" or (func.kind is None and func.name == "_init" and func.find_parent(NodeType.function) == None)):
                    custom_globals.add(node.name)
                    vars[node.name].append(node.var)

            if node.kind == VarKind.local and not node.new:
                if is_assign_target(node) or is_op_assign_target(node) or is_function_target(node):
                    assigned_locals.add(node.var)
                else:
                    used_locals.add(node.var)

        elif node.type == NodeType.sublang:
            for glob in node.lang.get_defined_globals():
                if glob not in custom_globals and is_identifier(glob):
                    custom_globals.add(glob)
                    vars[glob].append(root.globals[glob])

    root.traverse_nodes(preprocess_vars, extra=True)

    # check for issues

    def lint_pre(node):
        if node.type == NodeType.var:
            if node.kind == VarKind.local and node.new:
                if lint_duplicate and vars[node.name] and node.name not in ('_', '_ENV'):
                    prev_var = vars[node.name][-1]
                    if isinstance(prev_var, Global):
                        add_error("Local '%s' has the same name as a global" % node.name, node)
                    elif prev_var.scope.funcdepth < node.var.scope.funcdepth:
                        if prev_var.scope.funcdepth == 0:
                            add_error("Local '%s' has the same name as a local declared at the top level" % node.name, node)
                        else:
                            add_error("Local '%s' has the same name as a local declared in a parent function" % node.name, node)
                    elif prev_var.scope.depth < node.var.scope.depth:
                        add_error("Local '%s' has the same name as a local declared in a parent scope" % node.name, node)
                    else:
                        add_error("Local '%s' has the same name as a local declared in the same scope" % node.name, node)
                
                vars[node.name].append(node.var)

                if lint_unused and node.var not in used_locals and not node.name.startswith("_"):
                    if node.var in assigned_locals:
                        add_error("Local '%s' is only ever assigned to, never used" % node.name, node)
                    elif not (node.parent.type == NodeType.function and node in node.parent.params and 
                              (node != node.parent.params[-1] or node not in node.parent.children)): # don't warn for non-last or implicit params
                        add_error("Local '%s' isn't used" % node.name, node)

            elif node.kind == VarKind.global_:
                if lint_undefined and node.name not in custom_globals:
                    if node.name in builtin_globals:
                        if is_assign_target(node):
                            add_error("Built-in global '%s' assigned outside _init - did you mean to use 'local'?" % node.name, node)
                        elif is_function_target(node):
                            add_error("Built-in global '%s' assigned outside _init - did you mean to use 'local function'?" % node.name, node)
                    else:
                        if is_assign_target(node):
                            add_error("Identifier '%s' not found - did you mean to use 'local' to define it?" % node.name, node)
                        elif is_function_target(node):
                            add_error("Identifier '%s' not found - did you mean to use 'local function' to define it?" % node.name, node)
                        else:
                            add_error("Identifier '%s' not found" % node.name, node)
                            
        elif node.type == NodeType.sublang:
            add_lang_error = lambda msg: add_error("%s: %s" % (node.name, msg), node)
            node.lang.lint(on_error=add_lang_error, builtins=builtin_globals, globals=custom_globals)

    def lint_post(node):
        for scope in node.end_scopes:
            for item in scope.items:
                vars[item].pop()

    root.traverse_nodes(lint_pre, lint_post, extra=True)
    return errors

from pico_process import Error
