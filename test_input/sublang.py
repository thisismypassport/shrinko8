from pico_process import SubLanguageBase, is_identifier, Local, Scope
from collections import Counter

class MySubLanguage(SubLanguageBase):
    # called to parse the sub-language from a string
    # (strings consist of raw pico-8 chars ('\0' to '\xff') - not real unicode)
    def __init__(self, str, on_error, **_):
        # our trivial language consists of space-separated tokens in newline-separated statements
        self.stmts = [stmt.split() for stmt in str.splitlines()]
        # we can report parsing errors:
        #on_error("Example")

    # these are utility functions for our own use:

    def is_global(self, token):
        # is the token a global in our language? e.g. sin / rectfill / g_my_global
        return is_identifier(token)

    def is_member(self, token):
        # is the token a member in our language? e.g. .my_member / .x
        return token.startswith(".") and self.is_global(token[1:])
        
    # for --lint:

    # called to get globals defined within the sub-language's code
    def get_defined_globals(self, **_):
        for stmt in self.stmts:
            if len(stmt) > 1 and stmt[1] == "<-": # our lang's assignment token
                yield stmt[0]

    # called to lint the sub-language's code
    def lint(self, builtins, globals, on_error, **_):
        for stmt in self.stmts:
            for token in stmt:
                if self.is_global(token) and token not in builtins and token not in globals:
                    on_error("Identifier '%s' not found" % token)
        # could do custom lints too

    # for --minify:

    # called to get all characters that won't get removed or renamed by the minifier
    # (aka, all characters other than whitespace and identifiers)
    # this is optional and doesn't affect correctness, but can slightly improve compressed size
    def get_unminified_chars(self, **_):
        for stmt in self.stmts:
            for token in stmt:
                if not self.is_global(token) and not self.is_member(token):
                    yield from token

    # called to get all uses of globals in the language's code
    def get_global_usages(self, **_):
        usages = Counter()
        for stmt in self.stmts:
            for token in stmt:
                if self.is_global(token):
                    usages[token] += 1
        return usages
        
    # called to get all uses of members (table keys) in the language's code
    def get_member_usages(self, **_):
        usages = Counter()
        for stmt in self.stmts:
            for token in stmt:
                if self.is_member(token):
                    usages[token[1:]] += 1
        return usages

    # only needed if your language supports locals:
    # called to get all uses of locals in the language's code.
    # should return a Counter dict similar to above, except the keys are 
    # Local objects, and their scope (Scope objects) have 2 extra fields:
    #   used_globals - a set of all global names used in that scope
    #                  or in any of its child scopes
    #   used_locals - a set of all locals (Local objects) that are both:
    #                 a) delcared in that scope or its parent scopes
    #                 b) used in that scope or any of its child scopes
    def get_local_usages(self, **_):
        # fake test, just to see that the code is accepted
        # (may be nice to have real test for this?)
        fake_scope = Scope()
        fake_local = Local("test", fake_scope)
        fake_scope.used_globals = self.get_global_usages().keys()
        fake_scope.used_locals = {fake_local}
        return {fake_local: 1}

    # called to rename all uses of globals/members/locals
    def rename(self, globals, members, locals, **_):
        for stmt in self.stmts:
            for i, token in enumerate(stmt):
                if self.is_global(token) and token in globals:
                    stmt[i] = globals[token]
                elif self.is_member(token) and token[1:] in members:
                    stmt[i] = members[token[1:]]

    # called (after rename) to return a minified string
    def minify(self, **_):
        return "\n".join(" ".join(stmt) for stmt in self.stmts)

class SplitKeysSubLang(SubLanguageBase):
    # parses the string
    def __init__(self, str, **_):
        self.data = [item.split("=") for item in str.split(",")]

    # counts usage of keys
    # (returned keys are ignored if they're not identifiers)
    def get_member_usages(self, **_):
        return Counter(item[0] for item in self.data if len(item) > 1)

    # renames the keys
    def rename(self, members, **_):
        for item in self.data:
            if len(item) > 1:
                item[0] = members.get(item[0], item[0])

    # formats back to string
    def minify(self, **_):
        return ",".join("=".join(item) for item in self.data)

# this is called to get a sub-languge class by name
def sublanguage_main(lang, **_):
    if lang == "evally":
        return MySubLanguage
    elif lang == "splitkeys":
        return SplitKeysSubLang
    elif lang == "empty":
        return SubLanguageBase
