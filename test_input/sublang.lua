local pico_process = python.import("pico_process")
local SubLanguageBase = pico_process.SubLanguageBase
local module = {}

-- helper function like split, but ignores empties
function split_nonempty(str, ch)
    local res = split(str, ch, false)
    while (del (res, "")); -- (or copy to new table)
    return res
end

MySubLanguage = python.class(SubLanguageBase)

-- called to parse the sub-language from a string
-- (strings consist of raw pico-8 chars ('\0' to '\xff') - not real unicode)
function MySubLanguage:__init(str, opts)
    -- we may have received args that can be used to customize the language (not used here)
    self.args = opts.args
    -- our trivial language consists of space-separated tokens in newline-separated statements
    local lines = split_nonempty(str, "\n")
    self.stmts = {}
    for line in all(lines) do
        add(self.stmts, split_nonempty(line, " "))
    end
    -- we can report parsing errors:
    -- opts.on_error("Example")
end

-- these are utility functions for our own use:

function MySubLanguage:is_global(token)
    -- is the token a global in our language? e.g. sin / rectfill / g_my_global
    return pico_process.is_identifier(token)
end

function MySubLanguage:is_member(token)
    -- is the token a member in our language? e.g. .my_member / .x
    return token[1] == "." and self:is_global(sub(token, 2))
end
    
function MySubLanguage:is_assignment(stmt)
    return #stmt > 1 and stmt[2] == "<-" -- our lang's assignment token
end

-- for --lint:

-- called to get globals defined (aka assigned to) within the sub-language's code
function MySubLanguage:get_defined_globals()
    local globals = {}
    for stmt in all(self.stmts) do
        if self:is_assignment(stmt) then
            add(globals, stmt[1])
        end
    end
    return globals
end

-- called to get globals used (aka read from) within the sub-language's code
function MySubLanguage:get_used_globals()
    local globals = {}
    for stmt in all(self.stmts) do
        local start = 1
        if (self:is_assignment(stmt)) start = 3 -- ignore assigned to globals

        for i=start,#stmt do
            local token = stmt[i]
            if (self:is_global(token)) add(globals, token)
        end
    end
    return globals
end

-- called to lint the sub-language's code
function MySubLanguage:lint(opts)
    local builtins = python.table(opts.builtins)
    local globals = python.table(opts.globals)

    for stmt in all(self.stmts) do
        for token in all(stmt) do
            if self:is_global(token) and not builtins[token] and not globals[token] then
                opts.on_error("Identifier '" .. token .. "' not found")
            end
        end
    end
    -- could do custom lints too
end

-- for --minify:

-- called to get all characters that won't get removed or renamed by the minifier
-- (aka, all characters other than whitespace and identifiers)
-- this is optional and doesn't affect correctness, but can slightly improve compressed size
function MySubLanguage:get_unminified_chars()
    local chars = {}
    for stmt in all(self.stmts) do
        for token in all(stmt) do
            if not self:is_global(token) and not self:is_member(token) then
                for ch in all(token) do
                    add(chars, ch) -- if this overflows, could also use python.list directly...
                end
            end
        end
    end
    return python.list(chars)
end

-- called to get all uses of globals in the language's code
function MySubLanguage:get_global_usages()
    local usages = {}
    for stmt in all(self.stmts) do
        for token in all(stmt) do
            if self:is_global(token) then
                usages[token] = (usages[token] or 0) + 1
            end
        end
    end
    return python.dict(usages)
end
    
-- called to get all uses of members (table keys) in the language's code
function MySubLanguage:get_member_usages()
    local usages = {}
    for stmt in all(self.stmts) do
        for token in all(stmt) do
            if self:is_member(token) then
                local member = sub(token, 2)
                usages[member] = (usages[member] or 0) + 1
            end
        end
    end
    return python.dict(usages)
end

-- local usages is too much for picoscript

-- called to rename all uses of globals/members/locals
function MySubLanguage:rename(opts)
    local globals = python.table(opts.globals)
    local members = python.table(opts.members)

    for stmt in all(self.stmts) do
        for i, token in ipairs(stmt) do
            if self:is_global(token) and globals[token] then
                stmt[i] = globals[token]
            elseif self:is_member(token) and members[sub(token, 2)] then
                stmt[i] = members[sub(token, 2)]
            end
        end
    end
end

-- called (after rename) to return a minified string
function MySubLanguage:minify()
    local lines = {}
    for stmt in all(self.stmts) do
        add(lines, table.concat(stmt, " ")) -- can just use table.concat
    end
    return table.concat(lines, "\n")
end

-----------

SplitKeysSubLang = python.class(SubLanguageBase)

-- parses the string
function SplitKeysSubLang:__init(str)
    self.data = {}
    for item in all(split(str, ",", false)) do
        add(self.data, split(item, "=", false))
    end
end

-- counts usage of keys
-- (returned keys are ignored if they're not identifiers)
function SplitKeysSubLang:get_member_usages()
    local usages = {}
    for item in all(self.data) do
        if #item > 1 then
            local ident = item[1]
            usages[ident] = (usages[ident] or 0) + 1
        end
    end
    return python.dict(usages)
end

-- renames the keys
function SplitKeysSubLang:rename(opts)
    local members = python.table(opts.members)

    for item in all(self.data) do
        if #item > 1 then
            local member = members[item[1]]
            if (member) item[1] = member
        end
    end
end

-- formats back to string
function SplitKeysSubLang:minify(opts)
    local lines = {}
    for item in all(self.data) do
        add(lines, table.concat(item, "="))
    end
    return table.concat(lines, ",")
end

-----------

ArgsSubLang = python.class(SubLanguageBase)

function ArgsSubLang:__init(str, opts)
    if (opts.args != "arg1 arg2") opts.on_error("wrong arg!")
end

-----------

-- this is called to get a sub-languge class by name
function module.sublanguage_main(lang)
    if (lang == "evally") return MySubLanguage
    if (lang == "splitkeys") return SplitKeysSubLang
    if (lang == "empty") return SubLanguageBase
    if (lang == "args") return ArgsSubLang
end

return module