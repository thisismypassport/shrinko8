from utils import *
from pico_tokenize import CommentHint, is_identifier
from pico_parse import VarKind, NodeType
from pico_parse import is_assign_target, is_function_target, is_any_assign_target

def lint_code(ctxt, root, lint_opts):
    errors = []
    builtin_globals = ctxt.builtins

    lint_undefined = lint_opts.get("undefined", True)
    lint_unused = lint_opts.get("unused", True)
    lint_duplicate = lint_opts.get("duplicate", True)
    custom_globals = set(lint_opts.get("globals", ()))

    def add_error(msg, node):
        err = Error(msg, node)
        errors.append(err)

    # find global assignment, and check for uses

    used_locals = set()
    used_labels = set()
    assigned_locals = set()

    def preprocess_tokens(token):
        if token.children:
            for comment in token.children:
                if comment.hint == CommentHint.lint:
                    for value in comment.hintdata:
                        if "::" not in value:
                            custom_globals.add(value)

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

            if node.kind == VarKind.local and not node.new:
                if is_any_assign_target(node):
                    assigned_locals.add(node.var)
                else:
                    used_locals.add(node.var)
            
            if node.kind == VarKind.label and not node.new:
                used_labels.add(node.var)

        elif node.type == NodeType.sublang:
            for glob in node.lang.get_defined_globals():
                if glob not in custom_globals and is_identifier(glob):
                    custom_globals.add(glob)

    root.traverse_nodes(preprocess_vars, tokens=preprocess_tokens, extra=True)

    # check for issues

    def lint_pre(node):
        if node.type == NodeType.var:
            if node.kind == VarKind.local and node.new:
                if lint_duplicate and node.name not in ('_', '_ENV'):
                    prev_var = node.scope.parent.find(node.name)
                    if prev_var is None:
                        if node.name in custom_globals:
                            add_error("Local '%s' has the same name as a global" % node.name, node)
                    elif prev_var.scope.funcdepth < node.var.scope.funcdepth:
                        if prev_var.scope.funcdepth < 0:
                            pass # local builtin
                        elif prev_var.scope.funcdepth == 0:
                            add_error("Local '%s' has the same name as a local declared at the top level" % node.name, node)
                        else:
                            add_error("Local '%s' has the same name as a local declared in a parent function" % node.name, node)
                    elif prev_var.scope.depth < node.var.scope.depth:
                        add_error("Local '%s' has the same name as a local declared in a parent scope" % node.name, node)
                    else:
                        add_error("Local '%s' has the same name as a local declared in the same scope" % node.name, node)
                
                if lint_unused and node.var not in used_locals and not node.name.startswith("_"):
                    if node.var in assigned_locals:
                        add_error("Local '%s' is only ever assigned to, never used" % node.name, node)
                    elif not (node.parent.type == NodeType.function and node in node.parent.params and 
                              (node != node.parent.params[-1] or node not in node.parent.children)): # don't warn for non-last or implicit params
                        add_error("Local '%s' isn't used" % node.name, node)

            elif node.kind == VarKind.label and node.new:
                if lint_duplicate and node.name != '_':
                    prev_var = node.scope.parent.find(node.name, crossfunc=True)
                    if prev_var != None:
                        if prev_var.scope.funcdepth < node.var.scope.funcdepth:
                            if prev_var.scope.funcdepth <= 0:
                                add_error("Label '%s' has the same name as a label declared at the top level" % node.name, node)
                            else:
                                add_error("Label '%s' has the same name as a label declared in a parent function" % node.name, node)
                        else:
                            add_error("Label '%s' has the same name as a label declared in a parent scope" % node.name, node)
                
                if lint_unused and node.var not in used_labels and not node.name.startswith("_"):
                    add_error("Label '%s' isn't used" % node.name, node)

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

    root.traverse_nodes(lint_pre, extra=True)
    return errors

from pico_process import Error
