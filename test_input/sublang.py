from pico_process import SubLanguageBase, is_ident_char
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
        return all(is_ident_char(ch) for ch in token) and not token[:1].isdigit()

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

    # called to rename all uses of globals and members
    def rename(self, globals, members, **_):
        for stmt in self.stmts:
            for i, token in enumerate(stmt):
                if self.is_global(token) and token in globals:
                    stmt[i] = globals[token]
                elif self.is_member(token) and token[1:] in members:
                    stmt[i] = members[token[1:]]

    # called (after rename) to return a minified string
    def minify(self, **_):
        return "\n".join(" ".join(stmt) for stmt in self.stmts)

# this is called to get a sub-languge class by name
def sublanguage_main(lang, **_):
    if lang == "evally":
        return MySubLanguage
    elif lang == "empty":
        return SubLanguageBase
