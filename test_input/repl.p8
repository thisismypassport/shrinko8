__lua__
--keep:------------------------------------
--keep: Please see 'Commented Source Code' section in the BBS
--keep: for the original commented source code
--keep: (The below had the comments stripped due to cart size limits)
--keep:------------------------------------

--preserve: env.*, g_ENV.*, *._ENV, *._env, *._

------------------------
-- Prepare globals
------------------------

local g_ENV, my_ENV, globfuncs = _ENV, {}, {}
for k,v in pairs(_ENV) do
    my_ENV[k] = v
    if (type(v) == "function") globfuncs[k] = true
end

local _ENV = my_ENV -- with this, we segregate ourselves from the running code (all global accesses below use _ENV automagically)

g_enable_repl, g_last_value = true


------------------------
-- Utils
------------------------

-- is ch inside str? (if so, returns index)
function isoneof(ch, str)
    for i=1,#str do
        if (sub(str,i,i) == ch) return i
    end
end

-- get char i of string s (saves tokens)
function sub1(s, i) return sub(s,i,i) end

------------------------
-- Tokenize
------------------------

-- escape sequences in strings (e.g. \n -> new line)
local esc_keys, esc_values = split "a,b,f,n,r,t,v,\\,\",',\n,*,#,-,|,+,^", split "\a,\b,\f,\n,\r,\t,\v,\\,\",',\n,\*,\#,\-,\|,\+,\^"
local escapes = {}
for i=1,#esc_keys do escapes[esc_keys[i]] = esc_values[i] end

-- is ch a digit char?
function isdigit(ch)
    return ch >= '0' and ch <= '9'
end
-- is ch a valid identifier char?
function isalnum(ch)
    return ch >= 'A' and ch <= 'Z' or ch >= 'a' and ch <= 'z' or ch == '_' or ch >= '\x80' or isdigit(ch)
end

-- extarct string value from quoted string
-- returns value, end index
function dequote(str, i, quote, fail)
    local rawstr = ''
    while i <= #str do
        local ch = sub1(str,i)
        if (ch == quote) break
        if ch == '\\' then -- handle escape sequences
            i += 1
            local esch = sub1(str,i)
            ch = escapes[esch] -- handle normal escapes
            -- hex escape (e.g. \xff)
            if esch == 'x' then
                esch = tonum('0x'..sub(str,i+1,i+2))
                if (esch) i += 2 else fail "bad hex escape"
                ch = chr(esch)
            -- decimal escape (e.g. \014)
            elseif isdigit(esch) then
                local start = i
                while isdigit(esch) and i < start + 3 do i += 1; esch = sub1(str,i) end
                i -= 1
                esch = tonum(sub(str,start,i))
                if (not esch or esch >= 256) fail "bad decimal escape"
                ch = chr(esch)
            -- ignore subsequent whitespace
            elseif esch == 'z' then
                repeat i += 1; esch = sub1(str,i) until not isoneof(esch, ' \r\t\f\v\n')
                if (esch == '') fail()
                ch = ''
                i -= 1
            elseif esch == '' then fail() ch='' end
            if (not ch) fail("bad escape: " .. esch) ch=''
        elseif ch == '\n' then
            fail "unterminated string"
            break
        end
        rawstr ..= ch
        i += 1
    end
    if (i > #str) fail("unterminated string", true)
    return rawstr, i+1
end

-- extracts string value from long bracketed string (e.g. [[string]])
-- returns value, end index
function delongbracket(str, i, fail, strict)
    if sub1(str,i) == '[' then
        i += 1
        local eq_start = i
        while (sub1(str,i) == '=') i += 1
        local end_delim = ']' .. sub(str,eq_start,i-1) .. ']'
        local j = #end_delim

        if sub1(str,i) == '[' then
            i += 1
            if (sub1(str,i) == '\n') i += 1
            local start = i
            while (i <= #str and sub(str,i,i+j-1) != end_delim) i += 1
            if (i >= #str) fail()
            return sub(str,start,i-1), i+j
        end
    end
    if (strict) fail "invalid long brackets"
    return nil, i
end

-- converts a string into token.
--   if strict is set, errors are thrown if invalid, and comments are ignored
-- returns:
--   array of tokens
--   array of the line each token is found at (for if/while shorthand parsing only)
--   array of token start indices
--   array of token end indices
function tokenize(str, strict)
    local i, line, start = 1, 1
    local tokens, tlines, tstarts, tends, err = {}, {}, {}, {}

    local function fail(v, ok)
        if (strict) on_compile_fail(v, start)
        err = v and not ok
    end

    while i <= #str do
        start = i
        local ch = sub1(str,i)
        local ws, token
        -- whitespace
        if isoneof(ch, ' \r\t\f\v\n') then
            i += 1; ws = true
            if (ch == '\n') line += 1
        -- comment
        elseif ch == '-' and sub1(str,i+1) == '-' then
            i += 2
            if (sub1(str,i) == '[') token, i = delongbracket(str, i, fail)
            if not token then
                while (i <= #str and sub1(str,i) != '\n') i += 1
            end
            if (strict) ws = true else add(tokens, true)
        -- number
        elseif isdigit(ch) or (ch == '.' and isdigit(sub1(str,i+1))) then
            local digits, dot = "0123456789", true
            -- hex. number (0x...)
            if ch == '0' and isoneof(sub1(str,i+1), 'xX') then digits ..= "AaBbCcDdEeFf"; i += 2
            -- binary number (0b...)
            elseif ch == '0' and isoneof(sub1(str,i+1), 'bB') then digits = "01"; i += 2
            end
            while true do
                ch = sub1(str,i)
                if ch == '.' and dot then dot = false
                elseif not isoneof(ch, digits) then break end
                i += 1
            end
            token = sub(str,start,i-1)
            if (not tonum(token)) fail "bad number"; token="0"
            add(tokens, tonum(token))
        -- identifier
        elseif isalnum(ch) then
            while isalnum(sub1(str,i)) do i += 1 end
            add(tokens, sub(str,start,i-1))
        -- string
        elseif ch == "'" or ch == '"' then
            token, i = dequote(str, i+1, ch, fail)
            add(tokens, {str=token})
        -- long-bracket string
        elseif ch == '[' and isoneof(sub1(str,i+1), "=[") then
            token, i = delongbracket(str, i, fail, true)
            add(tokens, {str=token})
        -- punctuation
        else
            i += 1
            local ch2,ch3,ch4 = unpack(split(sub(str,i,i+2),""))
            if ch2 == ch and ch3 == ch and isoneof(ch,'.>') then
                i += 2
                if (ch4 == "=" and isoneof(ch,'>')) i += 1
            elseif ch2 == ch and ch3 != ch and isoneof(ch,'<>') and isoneof(ch3,'<>') then
                i += 2
                if (ch4 == "=") i += 1
            elseif ch2 == ch and isoneof(ch,'.:^<>') then
                i += 1
                if (ch3 == "=" and isoneof(ch,'.^<>')) i += 1
            elseif ch2 == '=' and isoneof(ch,'+-*/\\%^&|<>=~!') then i += 1
            elseif isoneof(ch,'+-*/\\%^&|<>=~#(){}[];,?@$.:') then
            else fail("bad char: " .. ch) end
            add(tokens, sub(str,start,i-1))
        end
        if (not ws) add(tlines, line); add(tstarts, start); add(tends, i-1)
        if (err) tokens[#tokens], err = false, false
    end
    return tokens, tlines, tstarts, tends
end

------------------------
-- More Utils
------------------------

-- is obj inside table?
function isin(obj, tab)
    for i=1,#tab do
        if (tab[i] == obj) return i
    end
end

-- similar to unpack, except depack(pack(...)) is always ...
function depack(t)
    return unpack(t,1,t.n) -- (unpack defaults to t,1,#t instead)
end

-- copy a table
function copy(t)
    local ct = {}
    for k, v in next, t do ct[k] = v end
    return ct
end

------------------------
-- Parse & Eval
------------------------

-- General information:
-- As we parse lua's grammar, we build nodes, which are merely
-- functions that take e (an environment) as the first arg.
-- Parent nodes call their children nodes, thus forming a sort of tree.

-- An environment (e) is an array of scope tables
-- the scope table at index 0 contains top-level upvalues like _ENV
-- other scope tables contain locals defined within a local statement (*)
-- Thus, upvalues and locals are accessed the same way

-- Expression (expr) parsing returns a (node, setnode, tailcallnode) tuple.
-- node returns the expression's value
-- setnode returns a tuple of the table and key to use for the assignment (**)
-- tailcallnode returns a tuple of the function and args to use for a tail-call
-- setnode and/or tailcallnode are nil if assignment/call is not available

-- Note that functions called from within parse_expr instead return a
-- (node, is_prefix, setnode, tailcallnode) tuple, where is_prefix
-- says whether the node can be used as a prefix for calls/etc.

-- Statement (stmt) parsing returns a (node, is_end) tuple
-- node returns either:
--   nil to continue execution
--   true to break from loop
--   (0, label object) to goto the label object
--   table to return its depack() from the function
--   function to tail-call it as we return from the function
-- node may also be nil for empty statements
-- is_end is true if the statement must end the block

-- (*) We create a table per local statement, instead of per block
--     because by using goto, you can execute a local statement multiple
--     times without leaving a block, each time resulting in a different
--     local (that can be independently captured)

-- (**) It would be much simpler for setnode to do the assignment itself,
--      but it would prevent us from mimicking lua's observable left-to-right
--      evaluation behaviour,  where the assignment targets are evaluated
--      before the assignment values.

-- On that note, we generally mimic lua's observable left-to-right evaluation
-- behaviour, except that we do true left-to-right evaluation, while lua
-- usually evaluates locals (only!) right before the operation that uses them.
-- This difference can be observed if the local is captured by a closure,
--  e.g: local a=1; print(a + (function() a = 3; return 0 end)())

-- anyway:

-- identifiers to treat as keywords instead
local keywords = split "and,break,do,else,elseif,end,false,for,function,goto,if,in,local,nil,not,or,repeat,return,then,true,until,while"

keyword_map = {}
for kw in all(keywords) do keyword_map[kw] = true end

-- is token an assign op (e.g. +=)?
local function is_op_assign(token)
    return type(token) == "string" and sub1(token,#token) == '='
end

-- tokens that terminate a block
end_tokens = split 'end,else,elseif,until'



-- parses a string, returning a function
-- that receives a global environment (e.g. _ENV) and executes the code
function parse(str  , allow_return )
    -- tokenize the string first
    local tokens, tlines, tstarts = tokenize(str, true)
    -- ti: the token index we're at
    -- e_len: how many environments deep we are
    -- depth: how many blocks deep we are
    local ti, e_len, depth, loop_depth, func_depth, func_e_len = 1, 0, 0
    local parse_expr, parse_block
    -- gotos: array of functions to evaluate in order to finalize gotos
    -- locals: maps names of locals to the environment array index where
    --         they're defined
    -- labels: maps names of labels to label objects
    --
    -- both locals and labels use a metatable to simulate a sort-of stack
    -- where pushed maps inherit from all previous maps in the stack and
    -- can be easily popped.
    --
    -- endcb: specifies when to stop shorthand parsing
    local gotos, locals, labels, endcb = {}

    local function fail(err)
        on_compile_fail(err, tstarts[ti-1] or 1)
    end

    -- return a node that returns a constant
    local function const_node(value)
        return function() return value end
    end
    -- return a node that returns the value of a variable
    local function var_node(name)
        local e_i = locals[name]
        if e_i then return function(e) return e[e_i][name] end -- local/upvalue
        else e_i = locals._ENV return function(e) return e[e_i]._ENV[name] end -- global
        end
    end
    -- return a node that returns the values of the vararg arguments
    -- of the current function.
    local function vararg_node()
        local e_i = locals['...']
        if (not e_i or e_i != func_e_len) fail "unexpected '...'"
        return function(e) return depack(e[e_i]["..."]) end
    end
    -- return a setnode that allows assigning to the value of a variable
    local function assign_node(name)
        local e_i = locals[name]
        if e_i then return function(e) return e[e_i], name end -- local/upvalue
        else e_i = locals._ENV return function(e) return e[e_i]._ENV, name end -- global
        end
    end

    -- consume the next token, requiring it to be 'expect'
    local function require(expect)
        local token = tokens[ti]; ti += 1
        if (token == expect) return
        if (token == nil) fail()
        fail("expected: " .. expect)
    end

    -- consume the next token, requiring it to be an identifier
    -- returns the identifier
    local function require_ident(token)
        if (not token) token = tokens[ti]; ti += 1
        if (token == nil) fail()
        if (type(token) == 'string' and isalnum(sub1(token,1)) and not keyword_map[token]) return token
        if (type(token) == 'string') fail("invalid identifier: " .. token)
        fail "identifier expected"
    end

    -- if the next token is 'expect', consumes it and returns true
    local function accept(expect)
        if (tokens[ti] == expect) ti += 1; return true
    end

    -- push a new locals map to the locals 'stack'
    local function push_locals()
        locals = setmetatable({}, {__index=locals})
        e_len += 1
    end

    -- pop a locals map from the 'stack'
    local function pop_locals()
        locals = getmetatable(locals).__index
        e_len -= 1
    end

    -- evaluate an array of nodes, returning a pack of results
    -- the last node in the array may return an arbitrary number of results,
    -- all of which are packed.
    local function eval_nodes(e, nodes)
        local results = {}
        local n = #nodes
        for i=1,n-1 do
            results[i] = nodes[i](e)
        end
        if n > 0 then
            local values = pack(nodes[n](e))
            if values.n != 1 then
                for i=1,values.n do
                    results[n + i - 1] = values[i]
                end
                n += values.n - 1
            else
                results[n] = values[1]
            end
        end
        results.n = n
        return results
    end

    -- parses a comma-separated list of elements, each parsed via 'parser'
    local function parse_list(parser)
        local list = {}
        add(list, (parser()))
        while accept ',' do
            add(list, (parser()))
        end
        return list
    end

    -- parse a call expression
    --   node : call target node
    --   method : method to call for method call expression (e.g. a:b())
    --   arg : single argument node (e.g. for a"b" and a{b})
    -- returns (node, is_prefix (true), setnode (nil), tailcallnode)
    local function parse_call(node, method, arg)
        -- parse the arguments
        local args = {}
        if arg then
            add(args, arg)
        elseif not accept ')' then
            while true do
                add(args, (parse_expr()))
                if (accept ')') break
                require ','
            end
        end

        if method then
            return function(e)
                -- call method
                local obj = node(e)
                return obj[method](obj, depack(eval_nodes(e, args)))
            end, true, nil, function(e)
                -- return ingredients for a method tail-call
                local obj = node(e)
                return obj[method], pack(obj, depack(eval_nodes(e, args)))
            end
        else
            return function(e)
                -- call function
                return node(e)(depack(eval_nodes(e, args)))
            end, true, nil, function(e)
                -- return ingredients for a function tail-call
                return node(e), eval_nodes(e, args)
            end
        end
    end

    -- parse a table construction expression (e.g. {1,2,3})
    local function parse_table()
        -- key/value nodes
        local keys, values = {}, {}
        -- splat_i : either #keys if the last item in the table is array-style
        --   (and thus may fill multiple array values), or nil otherwise
        local index, splat_i = 1
        while not accept '}' do
            splat_i = nil

            local key, value
            -- e.g. [a]=b
            if accept '[' then
                key = parse_expr(); require ']'; require '='; value = parse_expr()
            -- e.g. a=b
            elseif tokens[ti+1] == '=' then
                key = const_node(require_ident()); require '='; value = parse_expr()
            -- e.g. b
            else
                key = const_node(index); value = parse_expr(); index += 1; splat_i = #keys + 1
            end

            add(keys, key); add(values, value)

            if (accept '}') break
            if (not accept ';') require ','
        end

        return function(e)
            -- constuct table
            -- note: exact behaviour of # may differ from natively created tables
            local table = {}
            for i=1,#keys do
                if i == splat_i then
                    -- set multiple table elements (e.g. {f()})
                    local key, value = keys[i](e), pack(values[i](e))
                    for j=1,value.n do
                        table[key + j - 1] = value[j]
                    end
                else
                    -- set table element
                    table[keys[i](e)] = values[i](e)
                end
            end
            return table
        end
    end

    -- parse a function expression or statement
    -- is_stmt : true if statement
    -- is_local: true if local function statement
    local function parse_function(is_stmt, is_local)
        
        -- has_self : function has implicit self arg
        -- setnode : for statements, how to assign the function to a variable
        local name, has_self, setnode

        if is_stmt then
            if is_local then
                -- local function statement
                push_locals()
                name = require_ident()
                locals[name] = e_len
                setnode = assign_node(name)
                
            else
                -- function statement
                name = {require_ident()}
                -- function name may include multiple .-seprated parts
                while (accept '.') add(name, require_ident())
                -- and may include a final :-separated part
                if (accept ':') add(name, require_ident()); has_self = true

                if #name == 1 then setnode = assign_node(name[1])
                else
                    local node = var_node(name[1])
                    for i=2,#name-1 do
                        local node_i = node -- capture
                        node = function(e) return node_i(e)[name[i]] end
                    end
                    setnode = function(e) return node(e), name[#name] end
                end
                
            end
        end

        -- parse function params
        local params, vararg = {}
        if (has_self) add(params, 'self')
        require "("
        if not accept ')' then
            while true do
                if (accept '...') vararg = true; else add(params, require_ident())
                if (accept ')') break
                require ','
                if (vararg) fail "unexpected param after '...'"
            end
        end

        -- add function params as locals
        push_locals()
        for param in all(params) do locals[param] = e_len end
        if (vararg) locals['...'] = e_len

        -- parse function's body
        local old_gotos, old_depth, old_e_len = gotos, func_depth, func_e_len
        gotos, func_depth, func_e_len = {}, depth + 1, e_len
        local body = parse_block()
        for g in all(gotos) do g() end -- handle gotos
        gotos, func_depth, func_e_len = old_gotos, old_depth, old_e_len
        require 'end'
        pop_locals()

        return function(e)
            if (is_local) add(e, {})

            -- create the function's environment
            -- note: this is a shallow copy of the environment array,
            --   not of the tables within.
            local func_e = copy(e)
            local expected_e_len = #func_e

            -- this is the actual function created
            local func = function(...)
                local args = pack(...) -- pack args
                
                

                -- normally, when a function exits, its environment
                -- ends up the same as it started, so it can be reused
                -- however, if the function didn't exit yet (e.g. recursion)
                -- we create a copy of the environment to use for this call
                local my_e = func_e
                if #my_e != expected_e_len then
                    local new_e = {}
                    for i=0, expected_e_len do new_e[i] = my_e[i] end
                    my_e = new_e
                end

                -- add scope for params 
                local scope = {}
                for i=1,#params do scope[params[i]] = args[i] end

                if (vararg) scope['...'] = pack(unpack(args, #params+1, args.n))

                -- evaluate function body
                add(my_e, scope)
                local retval = body(my_e)
                deli(my_e)

                
                
                -- return function result
                if retval then
                    if (type(retval) == "table") return depack(retval) -- return
                    return retval() -- tailcall
                end
            end

            -- assign or return the function
            if (is_stmt) local d,k = setnode(e); d[k] = func else return func
        end
    end

    -- parse a core expression, aka an expression without any suffixes
    -- returns (node, is_prefix, setnode, tailcallnode)
    local function parse_core()
        local token = tokens[ti]; ti += 1
        local arg
        if (token == nil) fail()
        -- nil constant
        if (token == "nil") return const_node()
        -- true constant
        if (token == "true") return const_node(true)
        -- false constant
        if (token == "false") return const_node(false)
        -- number constant
        if (type(token) == "number") return const_node(token)
        -- string constant
        if (type(token) == "table") return const_node(token.str)
        -- table
        if (token == "{") return parse_table()
        -- parentheses (this is NOT an no-op, unlike in most
        --   languages - as it forces the expression to return 1 result)
        if (token == "(") arg = parse_expr(); require ')'; return function(e) return (arg(e)) end, true
        -- unary ops
        if (token == "-") arg = parse_expr(11); return function(e) return -arg(e) end
        if (token == "~") arg = parse_expr(11); return function(e) return ~arg(e) end
        if (token == "not") arg = parse_expr(11); return function(e) return not arg(e) end
        if (token == "#") arg = parse_expr(11); return function(e) return #arg(e) end
        if (token == "@") arg = parse_expr(11); return function(e) return @arg(e) end
        if (token == "%") arg = parse_expr(11); return function(e) return %arg(e) end
        if (token == "$") arg = parse_expr(11); return function(e) return $arg(e) end
        -- function creation
        if (token == 'function') return parse_function()
        -- vararg
        if (token == "...") return vararg_node()
        -- special repl-specific commands
        if (token == "\\") arg = require_ident() return function() return cmd_exec(arg) end, true, function() return cmd_assign(arg) end
        -- identifiers
        if (require_ident(token)) return var_node(token), true, assign_node(token)
        fail("unexpected token: " .. token)
    end

    -- parse a binary operation expression
    local function parse_binary_op(token, prec, left, right_expr)
        local right
        if (token == "^" and prec <= 12) right = right_expr(12); return function(e) return left(e) ^ right(e) end
        if (token == "*" and prec < 10) right = right_expr(10); return function(e) return left(e) * right(e) end
        if (token == "/" and prec < 10) right = right_expr(10); return function(e) return left(e) / right(e) end
        if (token == "\\" and prec < 10) right = right_expr(10); return function(e) return left(e) \ right(e) end
        if (token == "%" and prec < 10) right = right_expr(10); return function(e) return left(e) % right(e) end
        if (token == "+" and prec < 9) right = right_expr(9); return function(e) return left(e) + right(e) end
        if (token == "-" and prec < 9) right = right_expr(9); return function(e) return left(e) - right(e) end
        if (token == ".." and prec <= 8) right = right_expr(8); return function(e) return left(e) .. right(e) end
        if (token == "<<" and prec < 7) right = right_expr(7); return function(e) return left(e) << right(e) end
        if (token == ">>" and prec < 7) right = right_expr(7); return function(e) return left(e) >> right(e) end
        if (token == ">>>" and prec < 7) right = right_expr(7); return function(e) return left(e) >>> right(e) end
        if (token == "<<>" and prec < 7) right = right_expr(7); return function(e) return left(e) <<> right(e) end
        if (token == ">><" and prec < 7) right = right_expr(7); return function(e) return left(e) >>< right(e) end
        if (token == "&" and prec < 6) right = right_expr(6); return function(e) return left(e) & right(e) end
        if (token == "^^" and prec < 5) right = right_expr(5); return function(e) return left(e) ^^ right(e) end
        if (token == "|" and prec < 4) right = right_expr(4); return function(e) return left(e) | right(e) end
        if (token == "<" and prec < 3) right = right_expr(3); return function(e) return left(e) < right(e) end
        if (token == ">" and prec < 3) right = right_expr(3); return function(e) return left(e) > right(e) end
        if (token == "<=" and prec < 3) right = right_expr(3); return function(e) return left(e) <= right(e) end
        if (token == ">=" and prec < 3) right = right_expr(3); return function(e) return left(e) >= right(e) end
        if (token == "==" and prec < 3) right = right_expr(3); return function(e) return left(e) == right(e) end
        if ((token == "~=" or token == "!=") and prec < 3) right = right_expr(3); return function(e) return left(e) ~= right(e) end
        if (token == "and" and prec < 2) right = right_expr(2); return function(e) return left(e) and right(e) end
        if (token == "or" and prec < 1) right = right_expr(1); return function(e) return left(e) or right(e) end
    end

    -- given an expression, parses a suffix for this expression, if possible
    -- prec : precedence to not go beyond when parsing
    -- isprefix : true to allow calls/etc. (lua disallows it for certain
    --            expression unless parentheses are used, not sure why)
    -- returns (node, is_prefix, setnode, tailcallnode)
    local function parse_expr_more(prec, left, isprefix)
        local token = tokens[ti]; ti += 1
        local right, arg
        if isprefix then
            -- table index by name
            if (token == '.') right = require_ident(); return function(e) return left(e)[right] end, true, function(e) return left(e), right end
            -- table index
            if (token == '[') right = parse_expr(); require ']'; return function(e) return left(e)[right(e)] end, true, function(e) return left(e), right(e) end
            -- call
            if (token == "(") return parse_call(left)
            -- call with table or string argument
            if (token == "{" or type(token) == "table") ti -= 1; arg = parse_core(); return parse_call(left, nil, arg)
            -- method call
            if token == ":" then 
                right = require_ident();
                -- ... with table or string argument
                if (tokens[ti] == "{" or type(tokens[ti]) == "table") arg = parse_core(); return parse_call(left, right, arg)
                require '('; return parse_call(left, right)
            end
        end
        
        -- binary op
        local node = parse_binary_op(token, prec, left, parse_expr)
        if (not node) ti -= 1
        return node
    end

    -- parse an arbitrary expression
    -- prec : precedence to not go beyond when parsing
    -- returns (node, setnode, tailcallnode)
    parse_expr = function(prec)
        local node, isprefix, setnode, callnode = parse_core()
        while true do
            local newnode, newisprefix, newsetnode, newcallnode = parse_expr_more(prec or 0, node, isprefix)
            if (not newnode) break
            node, isprefix, setnode, callnode = newnode, newisprefix, newsetnode, newcallnode
        end
        return node, setnode, callnode
    end

    -- parse an assignment expression, returning its setnode
    local function parse_assign_expr()
        local _, assign_expr = parse_expr()
        if (not assign_expr) fail "cannot assign to value"
        return assign_expr
    end

    -- parse assignment statement
    local function parse_assign()
        local targets = parse_list(parse_assign_expr)
        require "="
        local sources = parse_list(parse_expr)

        if #targets == 1 and #sources == 1 then return function(e)
            -- single assignment (for performance)
            local d,k = targets[1](e); d[k] = sources[1](e)
        end else return function(e)
            -- multiple assignment (e.g. a,b=c,d)
            local dests, keys = {}, {}
            for i=1,#targets do local d,k = targets[i](e); add(dests,d) add(keys,k) end
            local values = eval_nodes(e, sources)
            -- assign from last to first, per observable lua behaviour
            for i=#targets,1,-1 do dests[i][keys[i]] = values[i] end
        end end
    end

    -- parse op-assignment statement (e.g. +=)
    -- receives the node and setnode of the assignment target
    -- this double evaluation of the assignment target is as per pico-8
    local function parse_op_assign(node, setnode)
        local token = tokens[ti]; ti += 1
        local op = sub(token,1,-2)
        local op_node = parse_binary_op(op, 0, node, function() return parse_expr() end) -- ignore precedence
        if (not op_node) fail "invalid compound assignment"
        return function(e) local d,k = setnode(e); d[k] = op_node(e) end
    end

    -- parse local statement
    local function parse_local()
        if accept 'function' then
            -- local function statement
            return parse_function(true, true)
        else
            local targets = parse_list(require_ident)
            local sources = accept '=' and parse_list(parse_expr) or {}

            push_locals()
            for i=1,#targets do locals[targets[i]] = e_len end

            if #targets == 1 and #sources == 1 then return function(e)
                -- single local (for performance)
                add(e, {[targets[1]] = sources[1](e)})
            end else return function(e)
                -- multiple locals
                local scope = {}
                local values = eval_nodes(e, sources)
                for i=1,#targets do scope[targets[i]] = values[i] end
                add(e, scope)
            end end
        end
    end

    -- set-up endcb for if/while shorthand parsing
    -- allows terminating the parsing of a block at the end of the line
    local function setup_endcb(allowed)
        local line = tlines[ti-1]
        endcb = function() return line != tlines[ti] end
        if (not allowed or endcb()) fail(ti <= #tokens and "bad shorthand" or nil)
    end

    -- parse an 'if' statement
    local function parse_ifstmt()
        local short = tokens[ti] == '('
        local cond = parse_expr()
        local then_b, else_b
        if accept 'then' then
            -- normal if statement
            then_b, else_b = parse_block()
            if accept 'else' then else_b = parse_block(); require "end" -- else
            elseif accept 'elseif' then else_b = parse_ifstmt() -- elseif
            else require "end" end
        else
            -- shorthand if
            setup_endcb(short)
            then_b = parse_block()
            if (not endcb() and accept 'else') else_b = parse_block() -- shorhand if/else
            endcb = nil
        end

        return function(e)
            -- execute the if
            if cond(e) then return then_b(e)
            elseif else_b then return else_b(e)
            end
        end
    end

    -- parse a loop block, updating loop_depth (for break purposes)
    local function parse_loop_block(...)
        local old_depth = loop_depth
        loop_depth = depth + 1
        local result = parse_block(...)
        loop_depth = old_depth
        return result
    end

    -- if retval denotes a break, do not propagate it further
    -- useful when returning from loop blocks
    local function handle_break(retval, label)
        if (retval == true) return -- break
        return retval, label
    end

    -- parse a 'while' block
    local function parse_while()
        local short = tokens[ti] == '('
        local cond = parse_expr()
        local body
        if accept 'do' then
            -- normal while statement
            body = parse_loop_block()
            require 'end'
        else
            -- shorthand while statement
            setup_endcb(short)
            body = parse_loop_block()
            endcb = nil
        end

        return function(e)
            -- execute the while
            while cond(e) do
                if (stat(1)>=1) yield_execute()
                local retval, label = body(e)
                if (retval) return handle_break(retval, label)
            end
        end
    end

    -- parse a repeat/until statement
    local function parse_repeat()
        -- note that the until part can reference
        -- locals declared inside the repeat body, thus
        -- we pop the locals/scopes ourselves
        local block_e_len = e_len
        local body = parse_loop_block(true)
        require 'until'
        local cond = parse_expr()
        while (e_len > block_e_len) pop_locals()

        return function(e)
            -- execute the repeat/until
            repeat
                if (stat(1)>=1) yield_execute()
                local retval, label = body(e)
                if (not retval) label = cond(e) -- reuse label as the end cond

                while (#e > block_e_len) deli(e) -- pop scopes ourselves
                if (retval) return handle_break(retval, label)
            until label -- actually the end cond
        end
    end

    -- parse a 'for' statement
    local function parse_for()
        if tokens[ti + 1] == '=' then
            -- numeric for statement
            local varb = require_ident()
            require '='
            local min = parse_expr()
            require ','
            local max = parse_expr()
            local step = accept ',' and parse_expr() or const_node(1)
            require 'do'

            -- push 'for' local, and parse the body
            push_locals()
            locals[varb] = e_len
            local body = parse_loop_block()
            require 'end'
            pop_locals()

            return function(e)
                -- execute the numeric 'for'
                for i=min(e),max(e),step(e) do
                    if (stat(1)>=1) yield_execute()
                    add(e, {[varb]=i})
                    local retval, label = body(e)
                    deli(e)
                    if (retval) return handle_break(retval, label)
                end
            end
        else
            -- generic 'for' block
            local targets = parse_list(require_ident)
            require "in"
            local sources = parse_list(parse_expr)
            require 'do'

            -- push 'for' locals, and parse the body
            push_locals()
            for target in all(targets) do locals[target] = e_len end

            local body = parse_loop_block()
            require 'end'
            pop_locals()

            return function(e)
                -- execute the generic 'for'
                -- (must synthesize it ourselves, as a generic for's
                --  number of vars is fixed)
                local exps = eval_nodes(e, sources)
                while true do
                    local scope = {}

                    local vars = {exps[1](exps[2], exps[3])}
                    if (vars[1] == nil) break
                    exps[3] = vars[1]
                    for i=1,#targets do scope[targets[i]] = vars[i] end

                    if (stat(1)>=1) yield_execute()
                    add(e, scope)
                    local retval, label = body(e)
                    deli(e)
                    if (retval) return handle_break(retval, label)
                end
            end
        end
    end

    -- parse a break statement
    local function parse_break()
        if (not loop_depth or func_depth and loop_depth < func_depth) fail "break outside of loop"
        return function() return true end
    end

    -- parse a return statement
    -- N.B. lua actually allows return (and vararg) in top-level
    --      this sort-of breaks repuzzle and is confusing/useless in pico,
    --      so we disallow it.
    local function parse_return()
        if (not func_depth  and not allow_return) fail "return outside of function"

        if tokens[ti] == ';' or isin(tokens[ti], end_tokens) or (endcb and endcb()) then
            -- return no values (represented by us as an empty pack)
            return function() return pack() end
        else
            local node, _, callnode = parse_expr()
            local nodes = {node}
            while (accept ',') add(nodes, (parse_expr()))

            if #nodes == 1 and callnode and func_depth then
                -- tail-call (aka jump into other function instead of returning)
                return function(e) local func, args = callnode(e);
                    if (stat(1)>=1) yield_execute()
                    return function() return func(depack(args)) end
                end
            else
                -- normal return
                return function(e) return eval_nodes(e, nodes) end
            end
        end
    end

    -- parse label statement
    local function parse_label(parent)
        local label = require_ident()
        require '::'
        if (labels[label] and labels[label].depth == depth) fail "label already defined"
        -- store label object
        labels[label] = {e_len=e_len, depth=depth, block=parent, i=#parent}
    end

    -- parse goto statement
    local function parse_goto()
        local label = require_ident()
        local labels_c, e_len_c, value = labels, e_len -- capture labels

        -- the label may be defined after the goto, so process the goto
        -- at function end
        add(gotos, function ()
            value = labels_c[label]
            if (not value) fail "label not found"
            if (func_depth and value.depth < func_depth) fail "goto outside of function"
            -- goto cannot enter a scope
            -- (empty statements at the end of a scope aren't considered a
            --  part of the scope for this purpose)
            local goto_e_len = labels_c[value.depth] or e_len_c
            if (value.e_len > goto_e_len and value.i < #value.block) fail "goto past local"
        end)

        return function()
            if (stat(1)>=1) yield_execute()
            return 0, value
        end
    end

    -- parse any statement
    local function parse_stmt(parent)
        local token = tokens[ti]; ti += 1
        -- empty semicolon
        if (token == ';') return
        -- do-end block
        if (token == 'do') local node = parse_block(); require 'end'; return node
        -- if
        if (token == 'if') return parse_ifstmt()
        -- while loop
        if (token == 'while') return parse_while()
        -- repeat/until loop
        if (token == 'repeat') return parse_repeat()
        -- for loop
        if (token == 'for') return parse_for()
        -- break
        if (token == 'break') return parse_break()
        -- return
        if (token == 'return') return parse_return(), true
        -- local
        if (token == 'local') return parse_local()
        -- goto
        if (token == 'goto') return parse_goto()
        -- label
        if (token == '::') return parse_label(parent)
        -- function
        if (token == 'function' and tokens[ti] != '(') return parse_function(true)
        -- print shorthand
        if token == '?' then
            local print_node, nodes = var_node 'print', parse_list(parse_expr);
            return function (e) print_node(e)(depack(eval_nodes(e, nodes))) end
        end

        -- handle assignments and expressions
        ti -= 1
        local start = ti -- allow reparse
        local node, setnode, callnode = parse_expr()

        -- assignment
        if accept ',' or accept '=' then
            ti = start; return parse_assign()
        -- op-assignment
        elseif is_op_assign(tokens[ti]) then
            return parse_op_assign(node, setnode)
        -- repl-specific print of top-level expression
        elseif depth <= 1 and g_enable_repl then
            return function (e)
                local results = pack(node(e))
                if (not (callnode and results.n == 0)) add(g_results, results)
                g_last_value = results[1]
            end
        -- regular expression statements (must be call)
        else
            if (not callnode) fail "statement has no effect"
            return function(e) node(e) end
        end
    end

    -- parse a block of statements
    -- keep_locals: true to let the caller exit the block themselves
    parse_block = function(keep_locals)
        -- push a new labels map in the labels 'stack'
        labels = setmetatable({}, {__index=labels})
        labels[depth] = e_len

        -- increase depth
        depth += 1
        local block_depth = depth
        local block_e_len = keep_locals and 0x7fff or e_len

        -- parse block statements
        local block = {}
        while ti <= #tokens and not isin(tokens[ti], end_tokens) and not (endcb and endcb()) do
            local  stmt, need_end =  parse_stmt(block)
            if (stmt) add(block, stmt) 
            if (need_end) accept ';'; break
        end

        -- pop any locals pushed inside the block
        while (e_len > block_e_len) pop_locals()
        depth -= 1
        labels = getmetatable(labels).__index

        return function (e)
            -- execute the block's statements
            local retval, label
            local i,n = 1,#block
            while i <= n do
                
                retval, label = block[i](e)
                if retval then
                    -- handle returns & breaks
                    if (type(retval) != "number") break
                    -- handle goto to parent block
                    if (label.depth != block_depth) break
                    -- handle goto to this block
                    i = label.i
                    while (#e > label.e_len) deli(e)
                    retval, label = nil
                end
                i += 1
            end
            while (#e > block_e_len) deli(e)
            return retval, label
        end
    end
    
    -- create top-level upvalues
    locals = g_enable_repl and {_ENV=0, _env=0, _=0} or {_ENV=0}
    -- parse top-level block
    local root = parse_block()
    if (ti <= #tokens) fail "unexpected end"
    -- handle top-level gotos
    for g in all(gotos) do g() end

    return function(env)
        -- create top-level scope
        local scope = g_enable_repl and {_ENV=env, _env=env, _=g_last_value} or {_ENV=env}
        
        -- execute
                
        local retval = root{[0]=scope}
        
        -- for the allow_return case
        if (retval) return depack(retval)
    end
end

------------------------
-- Output
------------------------

g_show_max_items, g_hex_output = 10, false

-- reverse mapping of escapes
local unescapes = {["\0"]="000",["\014"]="014",["\015"]="015"}
for k, v in pairs(escapes) do 
    if (not isoneof(k, "'\n")) unescapes[v] = k
end

-- create quoted string from a string value
function requote(str)
    local i = 1
    while i <= #str do
        local ch = sub1(str,i)
        local nch = unescapes[ch]
        if (nch) str = sub(str,1,i-1) .. '\\' .. nch .. sub(str,i+1); i += #nch
        i += 1
    end
    return '"' .. str .. '"'
end

-- is 'key' representable as an identifier?
function is_identifier(key)
    if (type(key) != 'string') return false
    if (keyword_map[key]) return false
    if (#key == 0 or isdigit(sub1(key,1))) return false
    for i=1,#key do
        if (not isalnum(sub1(key,i))) return false
    end
    return true
end

-- convert value as a string
-- (more featured than tostr)
function value_to_str(val, depth)
    local ty = type(val)
    -- nil
    if (ty == 'nil') then
        return 'nil'
    -- boolean
    elseif (ty == 'boolean') then
        return val and 'true' or 'false'
    -- number (optionally hex)
    elseif (ty == 'number') then
        return tostr(val, g_hex_output)
    -- string (with quotes)
    elseif (ty == 'string') then
        return requote(val)
    -- table contents
    elseif (ty == 'table' and not depth) then
        local res = '{'
        local i = 0
        local prev = 0
        -- avoid pairs, as it uses metamethods
        for k,v in next, val do
            if (i == g_show_max_items) res = res .. ',<...>' break
            if (i > 0) res = res .. ','
            local vstr = value_to_str(v,1)
            if k == prev + 1 then res = res .. vstr; prev = k
            elseif is_identifier(k) then res = res .. k .. '=' .. vstr
            else res = res .. '[' .. value_to_str(k,1) ..']=' .. vstr end
            i += 1
        end
        return res .. '}'
    -- other
    else
        return '<' .. tostr(ty) .. '>'
    end
end

-- convert more results into a string
function results_to_str(str, results)
    if (results == nil) return str -- no new results
    if (not str) str = ''

    local count = min(21,#results)
    for ir=1, count do
        if (#str > 0) str ..= '\n'

        local result = results[ir]
        if type(result) == 'table' then
            local line = ''
            for i=1,result.n do
                if (#line > 0) line = line .. ', '
                line = line .. value_to_str(result[i])
            end
            str ..= line
        else
            str ..= result
        end
    end

    local new_results = {}
    for i=count+1, #results do new_results[i - count] = results[i] end
    return str, new_results
end

------------------------
-- Console output
------------------------

poke(0x5f2d,1) -- enable keyboard
cls()

g_prompt = "> " -- currently must be valid token!
g_input, g_input_lines, g_input_start = "", 1, 0
g_cursor_pos, g_cursor_time = 1, 20
--lint: g_str_output, g_error_output
g_history, g_history_i = {''}, 1
--lint: g_interrupt, g_notice, g_notice_time
g_abort = false
g_num_output_lines, g_line = 0, 1

g_enable_interrupt, g_enable_autoflip = true, true
g_pal = {7,4,3,5,6,8,5,12,14,7,11,5}

-- override print for better output
g_ENV.print = function(value, ...)
    if (pack(...).n != 0 or not g_enable_interrupt) return print(value, ...)

    add(g_results, tostr(value))
end

-- suppress pause (e.g. from p, etc.)
function unpause()
    poke(0x5f30,1)
end

-- an iterator over pressed keys
function get_keys()
    return function()
        if (stat(30)) return stat(31)
    end
end

-- walk over a string, calling a callback on its chars
function walk_str(str, cb)
    local i = 1
    local x, y = 0, 0
    if (not str) return i, x, y
    while i <= #str do
        local ch = sub1(str,i)
        local spch = ch >= '\x80'
        if (x >= (spch and 31 or 32)) y += 1; x = 0
        if (cb) cb(i,ch,x,y)

        if ch == '\n' then y += 1; x = 0
        else x += (spch and 2 or 1) end
        i += 1
    end
    return i, x, y
end

-- given string and index, return x,y at index
function str_i2xy(str, ci)
    local cx, cy = 0, 0
    local ei, ex, ey = walk_str(str, function(i,ch,x,y)
        if (ci == i) cx, cy = x, y
    end)
    if (ci >= ei) cx, cy = ex, ey
    if (ex > 0) ey += 1
    return cx, cy, ey
end

-- given string and x,y - return index at x,y
function str_xy2i(str, cx, cy)
    local ci = 1
    local found = false
    local ei, ex, ey = walk_str(str, function(i,ch,x,y)
        if (cy == y and cx == x and not found) ci = i; found = true
        if ((cy < y or cy == y and cx < x) and not found) ci = i - 1; found = true
    end)
    if (not found) ci = cy >= ey and ei or ei - 1
    if (ex > 0) ey += 1
    return ci, ey
end

-- print string at position, using color value or function
function str_print(str, xpos, ypos, color)
    if type(color) == "function" then
        walk_str(str, function(i,ch,x,y)
            print(ch, xpos + x*4, ypos + y*6, color(i))
        end)
    else
        print(str and "\^rw" .. str, xpos, ypos, color)
    end
end

-- print code, using syntax highlighting
function str_print_input(input, xpos, ypos)
    local tokens, _, tstarts, tends = tokenize(input) -- tlines not reliable!
    local ti = 1
    str_print(input, xpos, ypos, function(i)
        while ti <= #tends and tends[ti] < i do ti += 1 end

        local token
        if (ti <= #tends and tstarts[ti] <= i) token = tokens[ti]

        local c = g_pal[5]
        if token == false then c = g_pal[6] -- error
        elseif token == true then c = g_pal[7] -- comment
        elseif type(token) != 'string' or isin(token, {"nil","true","false"}) then c = g_pal[8]
        elseif keyword_map[token] then c = g_pal[9]
        elseif not isalnum(sub1(token,1)) then c = g_pal[10]
        elseif globfuncs[token] then c = g_pal[11] end

        return c
    end)
end

-- draw (messy...)
function _draw()
    local old_color = peek(0x5f25)
    local old_camx, old_camy = peek2(0x5f28), peek2(0x5f2a)
    camera()

    local function scroll(count)
        cursor(0,127)
        for _=1,count do
            rectfill(0,g_line*6,127,(g_line+1)*6-1,0)
            if g_line < 21 then
                g_line += 1
            else
                print ""
            end
        end
    end

    local function unscroll(count, minline)
        for _=1,count do
            if (g_line > minline) g_line -= 1
            rectfill(0,g_line*6,127,(g_line+1)*6-1,0)
        end
    end

    local function draw_cursor(x, y)
        for i=0,2 do
            local c = pget(x+i,y+5)
            pset(x+i,y+5,c==0 and g_pal[12] or 0)
        end
    end

    local function draw_input(cursor)
        local input = g_prompt .. g_input .. ' '
        local cx, cy, ilines = str_i2xy(input, #g_prompt + g_cursor_pos) -- ' ' is cursor placeholder

        if ilines > g_input_lines then
            scroll(ilines - g_input_lines)
        elseif ilines < g_input_lines then
            unscroll(g_input_lines - ilines, ilines)
        end
        g_input_lines = ilines

        g_input_start = mid(g_input_start, 0, max(g_input_lines - 21, 0))

        ::again::
        local sy = g_line - g_input_lines + g_input_start
        if (sy+cy < 0) g_input_start += 1; goto again
        if (sy+cy >= 21) g_input_start -= 1; goto again

        local y = sy*6
        rectfill(0,y,127,y+g_input_lines*6-1,0)
        if (g_input_lines>21) rectfill(0,126,127,127,0) -- clear partial line
        str_print_input(input,0,y)
        print(g_prompt,0,y,g_pal[4])

        if (g_cursor_time >= 10 and cursor != false and not g_interrupt) draw_cursor(cx*4, y + cy*6)
    end

    -- require pressing enter to view more results
    local function page_interrupt(page_olines)
        scroll(1)
        g_line -= 1
        print("[enter] ('esc' to abort)",0,g_line*6,g_pal[3])

        while true do
            flip(); unpause()
            for key in get_keys() do
                if (key == '\x1b') g_abort = true; g_str_output = ''; g_results = {}; return false
                if (key == '\r' or key == '\n') g_num_output_lines += page_olines; return true
            end
        end
    end

    ::again::
    local ostart, olines
    if g_results or g_str_output then
        ostart, olines = str_xy2i(g_str_output, 0, g_num_output_lines)
        if olines - g_num_output_lines <= 20 and g_results then -- add more output
            g_str_output, g_results = results_to_str(g_str_output, g_results)
            ostart, olines = str_xy2i(g_str_output, 0, g_num_output_lines)
            if (#g_results == 0 and not g_interrupt) g_results = nil
        end
    end

    if (not g_interrupt) camera()

    if (g_num_output_lines == 0 and not g_interrupt) draw_input(not g_str_output)

    if g_str_output then
        local output = sub(g_str_output, ostart)
        local page_olines = min(olines - g_num_output_lines, 20)

        scroll(page_olines)
        str_print(output,0,(g_line - page_olines)*6,g_pal[1])

        if page_olines < olines - g_num_output_lines then
            if (page_interrupt(page_olines)) goto again
        else
            local _, _, elines = str_i2xy(g_error_output, 0)
            scroll(elines)
            str_print(g_error_output,0,(g_line - elines)*6,g_pal[2])

            if g_interrupt then
                g_num_output_lines += page_olines
            else
                g_input, g_input_lines, g_input_start, g_cursor_pos, g_num_output_lines, g_str_output, g_error_output =
                    '', 0, 0, 1, 0
                draw_input()
            end
        end
    end

    if g_interrupt then
        scroll(1)
        g_line -= 1
        print(g_interrupt,0,g_line*6,g_pal[3])
    end

    if g_notice then
        scroll(1)
        g_line -= 1
        print(g_notice,0,g_line*6,g_pal[3])
        g_notice = nil
    end

    if g_notice_time then
        g_notice_time -= 1
        if (g_notice_time == 0) g_notice, g_notice_time = ''
    end

    g_cursor_time -= 1
    if (g_cursor_time == 0) g_cursor_time = 20

    color(old_color)
    camera(old_camx, old_camy)
    if (g_line <= 20) cursor(0, g_line * 6)
end

------------------------
--- Execution loop
------------------------

g_in_execute_yield, g_in_mainloop, g_from_flip = false, false, false
g_pending_keys = {}
--lint: g_results, g_error, g_error_idx

-- report compilation error
-- an error of nil means code is likely incomplete
function on_compile_fail(err, idx)
    g_error, g_error_idx = err, idx
    assert(false, err)
end

-- execute code
function execute_raw(line, env, allow_return)
    return parse(line, allow_return)(env or g_ENV)
end

-- evaluate code
function eval_raw(expr, env)
    return execute_raw("return " .. expr, env, true)
end

-- try parse code
function try_parse(line)
    local cc = cocreate(parse)
    ::_::
    local ok, result = coresume(cc, line)
    if (ok and not result) goto _ -- this shouldn't happen anymore, but does (pico bug?)
    if (not ok) result, g_error = g_error, false
    return ok, result
end

function pos_to_str(line, idx)
    local x, y = str_i2xy(line, idx)
    return "line " .. y+1 .. " col " .. x+1
end

-- execute code
function execute(line, complete)
    g_results, g_abort, g_error = {}, false, false
    g_in_execute_yield, g_in_mainloop, g_from_flip = false, false, false

    -- create a coroutine to allow the code to yield to us periodically
    local coro = cocreate(function () execute_raw(line) end)
    local ok, error
    while true do
        ok, error = coresume(coro)
        if (costatus(coro) == 'dead') break

        -- handle yields (due to yield/flip or periodic)
        if g_enable_interrupt and not g_in_mainloop then
            g_interrupt = "running, press 'esc' to abort"
            _draw(); flip()
            g_interrupt = nil
        else
            if (g_enable_autoflip and not g_in_mainloop and not g_from_flip) flip()
            if (not g_enable_autoflip and holdframe) holdframe()
            g_from_flip = false
        end

        for key in get_keys() do
            if key == '\x1b' then g_abort = true
            else add(g_pending_keys, key) end
        end

        -- abort execution if needed
        if (g_abort) error = 'computation aborted'; break
    end

    if g_error == nil then -- code is incomplete
        if (complete) error = "unexpected end of code" else error, g_results = nil
    end
    if (g_error) error, g_error = g_error .. "\nat " .. pos_to_str(line, g_error_idx)
    g_error_output = error
    g_pending_keys = {}
end

-- called periodically during execution
yield_execute = function ()
    -- yield all the way back to us
    g_in_execute_yield = true
    yield()
    g_in_execute_yield = false
end

-- override flip to force a yield_execute
g_ENV.flip = function(...)
    local results = pack(flip(...))
    g_from_flip = true
    yield_execute()
    return depack(results)
end

-- override coresume to handle yield_execute in coroutines
g_ENV.coresume = function(co, ...)
    local results = pack(coresume(co, ...))
    -- propagate yields from yield_execute
    while g_in_execute_yield do
        yield()
        results = pack(coresume(co)) -- and resume
    end
    g_error = false -- discard inner compilation errors (via \x)
    return depack(results)
end

-- override stat so we can handle keys ourselves
g_ENV.stat = function(i, ...)
    if i == 30 then
        return #g_pending_keys > 0 or stat(i, ...)
    elseif i == 31 then
        if #g_pending_keys > 0 then
            return deli(g_pending_keys, 1)
        else
            local key = stat(i, ...)
            if (key == '\x1b') g_abort = true
            return key
        end
    else
        return stat(i, ...)
    end
end

------------------------
-- Special \-commands
------------------------

-- simulate a mainloop.
-- TODO: low compatibility with real mainloops...
function do_mainloop(env)
    if (_set_fps) _set_fps(env._update60 and 60 or 30)
    if (env._init) env._init()
    g_in_mainloop = true
    while true do
        if (_update_buttons) _update_buttons()
        if (holdframe) holdframe()
        if env._update60 then env._update60() elseif env._update then env._update() end
        if (env._draw) env._draw()
        flip()
        g_from_flip = true
        yield_execute()
    end
    g_in_mainloop = false
end

-- execute a repl-specific command
function cmd_exec(name)
    if isin(name, {"i","interrupt"}) then
        return g_enable_interrupt
    elseif isin(name, {"f","flip"}) then
        return g_enable_autoflip
    elseif isin(name, {"r","repl"}) then
        return g_enable_repl
    elseif isin(name, {"mi","max_items"}) then
        return g_show_max_items
    elseif isin(name, {"h","hex"}) then
        return g_hex_output
    elseif isin(name, {"cl","colors"}) then
        return g_pal
    elseif isin(name, {"c","code"}) then
        local code = {[0]=g_input}
        for i=1,#g_history-1 do code[i] = g_history[#g_history-i] end
        return code
    elseif isin(name, {"cm","compile"}) then
        return function(str) return try_parse(str) end
    elseif isin(name, {"x","exec"}) then
        return function(str, env) execute_raw(str, env) end
    elseif isin(name, {"v","eval"}) then
        return function(str, env) return eval_raw(str, env) end
    elseif isin(name, {"p","print"}) then
        return function(str,...) g_ENV.print(value_to_str(str),...) end
    elseif isin(name, {"ts","tostr"}) then
        return function(str) return value_to_str(str) end
    elseif isin(name, {"rst","reset"}) then
        run() -- full pico8 reset
    elseif isin(name, {"run"}) then
        do_mainloop(g_ENV)
    else
        assert(false, "unknown \\-command")
    end
end

-- assign to a repl-specific command
function cmd_assign(name)
    local function trueish(t)
        return (t and t != 0) and true or false
    end

    local func
    if isin(name, {"i","interrupt"}) then
        func = function(v) g_enable_interrupt = trueish(v) end
    elseif isin(name, {"f","flip"}) then
        func = function(v) g_enable_autoflip = trueish(v) end
    elseif isin(name, {"r","repl"}) then
        func = function(v) g_enable_repl = trueish(v) end
    elseif isin(name, {"mi","max_items"}) then
        func = function(v) g_show_max_items = tonum(v) or -1 end
    elseif isin(name, {"h","hex"}) then
        func = function(v) g_hex_output = trueish(v) end
    elseif isin(name, {"cl","colors"}) then
        func = function(v) g_pal = v end
    else
        assert(false, "unknown \\-command assign")
    end

    -- do some trickery to allow calling func upon assignment
    -- (as we're expected to return the assignment target)
    local obj = {__newindex=function(t,k,v) func(v) end}
    return setmetatable(obj, obj), 0
end

------------------------
-- Console input
------------------------

--lint: g_ideal_x, g_key_code
g_prev_paste = stat(4)
g_key_time, g_lower = 0, false

poke(0x5f5c,10,2) -- faster btnp

-- return if keyboard key is pressed, using btnp-like logic
function keyp(code)
    if stat(28,code) then
        if (code != g_key_code) g_key_code, g_key_time = code, 0
        return g_key_time == 0 or (g_key_time >= 10 and g_key_time % 2 == 0)
    elseif g_key_code == code then
        g_key_code = nil
    end
end

-- update console input
function _update()
    local input = false

    local function go_line(dy)
        local cx, cy, h = str_i2xy(g_prompt .. g_input, #g_prompt + g_cursor_pos)
        if (g_ideal_x) cx = g_ideal_x
        cy += dy
        if (not (cy >= 0 and cy < h)) return false
        g_cursor_pos = max(str_xy2i(g_prompt .. g_input, cx, cy) - #g_prompt, 1)
        g_ideal_x = cx
        g_cursor_time = 20 -- setting input clears ideal x
        return true
    end

    local function go_edge(dx)
        local cx, cy = str_i2xy(g_prompt .. g_input, #g_prompt + g_cursor_pos)
        cx = dx > 0 and 100 or 0
        g_cursor_pos = max(str_xy2i(g_prompt .. g_input, cx, cy) - #g_prompt, 1)
        input = true
    end

    local function go_history(di)
        g_history[g_history_i] = g_input
        g_history_i += di
        g_input = g_history[g_history_i]
        if di < 0 then
            g_cursor_pos = #g_input + 1
        else
            g_cursor_pos = max(str_xy2i(g_prompt .. g_input, 32, 0) - #g_prompt, 1) -- end of first line
            local ch = sub1(g_input, g_cursor_pos)
            if (ch != '' and ch != '\n') g_cursor_pos -= 1
        end
        input = true
    end

    local function push_history()
        if #g_input > 0 then
            if (#g_history > 50) del(g_history, g_history[1])
            g_history[#g_history] = g_input
            add(g_history, '')
            g_history_i = #g_history
            input = true
        end
    end

    local function delchar(offset)
        if (g_cursor_pos+offset > 0) then
            g_input = sub(g_input,1,g_cursor_pos+offset-1) .. sub(g_input,g_cursor_pos+offset+1)
            g_cursor_pos += offset
            input = true
        end
    end

    local function inschar(key)
        g_input = sub(g_input,1,g_cursor_pos-1) .. key .. sub(g_input,g_cursor_pos)
        g_cursor_pos += #key
        input = true
    end

    local ctrl = stat(28,224) or stat(28,228)
    local shift = stat(28,225) or stat(28,229)

    local keycode = -1
    if keyp(80) then -- left
        if (g_cursor_pos > 1) g_cursor_pos -= 1; input = true
    elseif keyp(79) then -- right
        if (g_cursor_pos <= #g_input) g_cursor_pos += 1; input = true
    elseif keyp(82) then -- up
        if ((ctrl or not go_line(-1)) and g_history_i > 1) go_history(-1)
    elseif keyp(81) then -- down
        if ((ctrl or not go_line(1)) and g_history_i < #g_history) go_history(1)
    else
        local key = stat(31)
        keycode = ord(key)

        if key == '\x1b' then -- escape
            if #g_input == 0 then extcmd "pause"
            else g_results, g_error_output = {}; push_history() end
        elseif key == '\r' or key == '\n' then -- enter
            if shift then
                inschar '\n'
            else
                execute(g_input) -- sets g_results/g_error_output
                if (not g_results) inschar '\n' else push_history()
            end
        elseif ctrl and keyp(40) then -- ctrl+enter
            execute(g_input, true); push_history()
        elseif key != '' and keycode >= 0x20 and keycode < 0x9a then -- ignore ctrl-junk
            if (g_lower and keycode >= 0x80) key = chr(keycode - 63)
            inschar(key)
        elseif keycode == 193 then -- ctrl+b
            inschar '\n'
        elseif keycode == 192 then -- ctrl+a
            go_edge(-1)
        elseif keycode == 196 then -- ctrl+e
            go_edge(1)
        elseif keycode == 203 then -- ctrl+l
            g_lower = not g_lower
            g_notice, g_notice_time = "shift now selects " .. (g_lower and "punycase" or "symbols"), 40
        elseif keyp(74) then -- home
            if (ctrl) g_cursor_pos = 1; input = true else go_edge(-1);
        elseif keyp(77) then -- end
            if (ctrl) g_cursor_pos = #g_input + 1; input = true else go_edge(1);        
        elseif keyp(42) then delchar(-1) -- backspace
        elseif keyp(76) then delchar(0) -- del
        end
    end

    local paste = stat(4)
    if (paste != g_prev_paste or keycode == 213) inschar(paste); g_prev_paste = paste -- ctrl+v

    if keycode == 194 or keycode == 215 then -- ctrl+x/c
        if g_input != '' and g_input != g_prev_paste then
            g_prev_paste = g_input; printh(g_input, "@clip");
            if (keycode == 215) g_input = ''; g_cursor_pos = 1;
            g_notice = "press again to put in clipboard"
        else
            g_notice = ''
        end
    end

    if stat(120) then
        local count
        repeat
            count = serial(0x800,0x5f80,0x80)
            inschar(chr(peek(0x5f80,count)))
        until count == 0
    end

    if (input) g_cursor_time, g_ideal_x = 20
    g_key_time += 1

    unpause()
end

------------------------
-- Main
------------------------

-- Self-test
-- (so I can more easily see if something got regressed in the future (esp. due to pico8 changes))

function selftest(i, cb)
    local ok, error = coresume(cocreate(cb))
    if not ok then
        printh("error #" .. i .. ": " .. error)
        print("error #" .. i .. "\npico8 broke something again,\nthis cart may not work.\npress any button to ignore")
        while (btnp() == 0) flip()
        cls()
    end
end

selftest(1, function() assert(pack(eval_raw "(function (...) return ... end)(1,2,nil,nil)" ).n == 4) end)
selftest(2, function() assert(eval_raw "function() local temp, temp2 = {max(1,3)}, -20;return temp[1] + temp2; end" () == -17) end)

printh("finished")stop()

-- my own crummy mainloop, since time() does not seem to update if the regular mainloop goes "rogue" and flips.
while true do
    if (holdframe) holdframe()
    _update()
    _draw()
    flip()
end
