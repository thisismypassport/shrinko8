__lua__
--------------------------------------
-- Please see 'Where is the Commented Source Code?' section in the BBS
-- for the original commented source code
-- (The below had the comments stripped due to cart size limits)
--------------------------------------

local g_ENV, my_ENV, globfuncs = _ENV, {}, {}
for k,v in pairs(_ENV) do
    my_ENV[k] = v
    if (type(v) == "function") globfuncs[k] = true
end

local _ENV = my_ENV 
g_enable_repl, g_last_value = true


function isoneof(elem, seq)
    for i=1,#seq do
        if (seq[i] == elem) return i
    end
end

local esc_keys, esc_values,escapes = split "a,b,f,n,r,t,v,\\,\",',\n,*,#,-,|,+,^", split "\a,\b,\f,\n,\r,\t,\v,\\,\",',\n,\*,\#,\-,\|,\+,\^",{}
for i=1,#esc_keys do escapes[esc_keys[i]] = esc_values[i] end

function isdigit(ch)
    return ch and ch >= '0' and ch <= '9'
end
function isalnum(ch)
    return ch and (ch >= 'A' and ch <= 'Z' or ch >= 'a' and ch <= 'z' or isoneof(ch, '_\x1e\x1f') or ch >= '\x80' or isdigit(ch))
end


function dequote(str, i, strlen, quote, fail)
    local rawstr = ''
    while i <= strlen do
        local ch = str[i]
        if (ch == quote) break
        if ch == '\\' then 
            i += 1
            local esch = str[i]
            ch = escapes[esch] 
            if esch == 'x' then
                esch = tonum('0x'..sub(str,i+1,i+2))
                if (esch) i += 2 else fail "bad hex escape"
                ch = chr(esch)
                        elseif isdigit(esch) then
                local start = i
                while isdigit(esch) and i < start + 3 do i += 1; esch = str[i] end
                i -= 1
                esch = tonum(sub(str,start,i))
                if (not esch or esch >= 256) fail "bad decimal escape"
                ch = chr(esch)
                        elseif esch == 'z' then
                repeat i += 1; esch = str[i] until not isoneof(esch, ' \r\t\f\v\n')
                if (not esch) fail()
                ch = ''
                i -= 1
            elseif not esch then fail() ch='' end
            if (not ch) fail("bad escape: " .. esch) ch=''
        elseif ch == '\n' then
            fail "unterminated string"
            break
        end
        rawstr ..= ch
        i += 1
    end
    if (i > strlen) fail("unterminated string", true)
    return rawstr, i+1
end

function delongbracket(str, i, strlen, fail)
    if str[i] == '[' then
        i += 1
        local eq_start = i
        while (str[i] == '=') i += 1
        local end_delim = ']' .. sub(str,eq_start,i-1) .. ']'
        local j = #end_delim

        if str[i] == '[' then
            i += 1
            if (str[i] == '\n') i += 1
            local start = i
            while (i <= strlen and sub(str,i,i+j-1) != end_delim) i += 1
            if (i >= strlen) fail()
            return sub(str,start,i-1), i+j
        end
    end
    return nil, i
end

function tokenize(str, strict)
    local i, line,tokens,tlines,tstarts,tends,err, start = 1, 1,{},{},{},{}
    local function fail(v, ok)
        if (strict) on_compile_fail(v, start)
        err = v and not ok
    end

        local strlen = #str >= 0 and #str or 0x7fff
    while i <= strlen do
        if (i >= 0x4001 and strlen >= 0x7fff) str = sub(str, 0x4001); i -= 0x4000; strlen = #str >= 0 and #str or 0x7fff
        
        start = i
        local ch,ws,token = str[i]
                if isoneof(ch, ' \r\t\f\v\n') then
            i += 1; ws = true
            if (ch == '\n') line += 1
                elseif isoneof(ch, '-/') and str[i+1] == ch then
            i += 2
            if (ch == '-' and str[i] == '[') token, i = delongbracket(str, i, strlen, fail)
            if not token then
                while (i <= strlen and str[i] != '\n') i += 1
            end
            if (strict) ws = true else add(tokens, true)
                elseif isdigit(ch) or (ch == '.' and isdigit(str[i+1])) then
            local digits, dot = "0123456789", true
                        if ch == '0' and isoneof(str[i+1], 'xX') then digits ..= "AaBbCcDdEeFf"; i += 2
                        elseif ch == '0' and isoneof(str[i+1], 'bB') then digits = "01"; i += 2
            end
            while true do
                ch = str[i]
                if ch == '.' and dot then dot = false
                elseif not isoneof(ch, digits) then break end
                i += 1
            end
            token = sub(str,start,i-1)
            if (not tonum(token)) fail "bad number"; token="0"
            add(tokens, tonum(token))
                elseif isalnum(ch) then
            while isalnum(str[i]) do i += 1 end
            add(tokens, sub(str,start,i-1))
                elseif ch == "'" or ch == '"' then
            token, i = dequote(str, i+1, strlen, ch, fail)
            add(tokens, {token})
                elseif ch == '[' and isoneof(str[i+1], "=[") then
            token, i = delongbracket(str, i, strlen, fail)
            if (not token) fail "invalid long brackets"
            add(tokens, {token})
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
function depack(t)
    return unpack(t,1,t.n) 
end

function copy(t)
    local ct = {}
    for k, v in next, t do ct[k] = v end
    return ct
end

local keywords = split "and,break,do,else,elseif,end,false,for,function,goto,if,in,local,nil,not,or,repeat,return,then,true,until,while"

keyword_map = {}
for kw in all(keywords) do keyword_map[kw] = true end

local function is_op_assign(token)
    return type(token) == "string" and token[-1] == '='
end

end_tokens = split 'end,else,elseif,until'



function parse(str )
        local tokens, tlines, tstarts = tokenize(str, true)
        local ti, e_len, depth, func_e_len,gotos,locals,labels,endcb,parse_expr,parse_block, loop_depth, func_depth = 1, 0, 0 , 0,{}
        
local function fail(err)
        on_compile_fail(err, tstarts[ti-1] or 1)
    end

        local function const_node(value)
        return function() return value end
    end
        local function var_node(name)
        local e_i = locals[name]
        if e_i then return function(e) return e[e_i][name] end 
        else e_i = locals._ENV return function(e) return e[e_i]._ENV[name] end 
        end
    end
        local function vararg_node()
        local e_i = locals['...']
        if (not e_i or e_i != func_e_len) fail "unexpected '...'"
        return function(e) return depack(e[e_i]["..."]) end
    end
        local function assign_node(name)
        local e_i = locals[name]
        if e_i then return function(e) return e[e_i], name end 
        else e_i = locals._ENV return function(e) return e[e_i]._ENV, name end 
        end
    end

        local function require(expect)
        local token = tokens[ti]; ti += 1
        if (token == expect) return
        if (token == nil) fail()
        fail("expected: " .. expect)
    end

        local function require_ident(token)
        if (not token) token = tokens[ti]; ti += 1
        if (token == nil) fail()
        if (type(token) == 'string' and isalnum(token[1]) and not keyword_map[token]) return token
        if (type(token) == 'string') fail("invalid identifier: " .. token)
        fail "identifier expected"
    end

        local function accept(expect)
        if (tokens[ti] == expect) ti += 1; return true
    end

        local function at_stmt_end()
        return isoneof(tokens[ti], end_tokens) or (endcb and endcb(ti))
    end

        local function push_locals()
        locals = setmetatable({}, {__index=locals})
        e_len += 1
    end

        local function pop_locals()
        locals = getmetatable(locals).__index
        e_len -= 1
    end

        local function eval_nodes(e, nodes)
        local results,n = {},#nodes
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

        local function parse_list(parser)
        local list = {}
        add(list, (parser()))
        while accept ',' do
            add(list, (parser()))
        end
        return list
    end

        local function parse_call(node, method, arg)
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
                                local obj = node(e)
                return obj[method](obj, depack(eval_nodes(e, args)))
            end, true, nil, function(e)
                                local obj = node(e)
                return obj[method], pack(obj, depack(eval_nodes(e, args)))
            end, true
        else
            return function(e)
                                return node(e)(depack(eval_nodes(e, args)))
            end, true, nil, function(e)
                                return node(e), eval_nodes(e, args)
            end, true
        end
    end

        local function parse_table()
                local keys, values,index,splat_i = {}, {},1
                
while not accept '}' do
            splat_i = nil

            local key, value
                        if accept '[' then
                key = parse_expr(); require ']'; require '='; value = parse_expr()
                        elseif tokens[ti+1] == '=' then
                key = const_node(require_ident()); require '='; value = parse_expr()
                        else
                key = const_node(index); value = parse_expr(); index += 1; splat_i = #keys + 1
            end

            add(keys, key); add(values, value)

            if (accept '}') break
            if (not accept ';') require ','
        end

        return function(e)
                        local table = {}
            for i=1,#keys do
                if i == splat_i then
                                        local key, value = keys[i](e), pack(values[i](e))
                    for j=1,value.n do
                        table[key + j - 1] = value[j]
                    end
                else
                                        table[keys[i](e)] = values[i](e)
                end
            end
            return table
        end
    end

        local function parse_function(is_stmt, is_local)
        
                local name, has_self, setnode

        if is_stmt then
            if is_local then
                                push_locals()
                name = require_ident()
                locals[name] = e_len
                setnode = assign_node(name)
                
            else
                                name = {require_ident()}
                                while (accept '.') add(name, require_ident())
                                if (accept ':') add(name, require_ident()); has_self = true

                if #name == 1 then setnode = assign_node(name[1])
                else
                    local node = var_node(name[1])
                    for i=2,#name-1 do
                        local node_i = node 
                        node = function(e) return node_i(e)[name[i]] end
                    end
                    setnode = function(e) return node(e), name[#name] end
                end
                
            end
        end

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

                push_locals()
        for param in all(params) do locals[param] = e_len end
        if (vararg) locals['...'] = e_len

                local old_gotos, old_depth, old_e_len = gotos, func_depth, func_e_len
        gotos, func_depth, func_e_len = {}, depth + 1, e_len
        local body = parse_block()
        for g in all(gotos) do g() end 
        gotos, func_depth, func_e_len = old_gotos, old_depth, old_e_len
        require 'end'
        pop_locals()

        return function(e)
            if (is_local) add(e, {})

                        local func_e = copy(e)
            local expected_e_len = #func_e

                        local func = function(...)
                local args,my_e = pack(...),func_e                 
if #my_e != expected_e_len then
                    local new_e = {}
                    for i=0, expected_e_len do new_e[i] = my_e[i] end
                    my_e = new_e
                end

                                local scope = {}
                for i=1,#params do scope[params[i]] = args[i] end

                if (vararg) scope['...'] = pack(unpack(args, #params+1, args.n))

                                add(my_e, scope)
                local retval = body(my_e)
                deli(my_e)

                
                
                                if retval then
                    if (type(retval) == "table") return depack(retval) 
                    return retval() 
                end
            end

                        if (is_stmt) local d,k = setnode(e); d[k] = func else return func
        end
    end

        local function parse_core()
        local token = tokens[ti]; ti += 1
        local arg
        if (token == nil) fail()
                if (token == "nil") return const_node()
                if (token == "true") return const_node(true)
                if (token == "false") return const_node(false)
                if (type(token) == "number") return const_node(token)
                if (type(token) == "table") return const_node(token[1])
                if (token == "{") return parse_table()
                if (token == "(") arg = parse_expr(); require ')'; return function(e) return (arg(e)) end, true
                if (token == "-") arg = parse_expr(11); return function(e) return -arg(e) end
        if (token == "~") arg = parse_expr(11); return function(e) return ~arg(e) end
        if (token == "not") arg = parse_expr(11); return function(e) return not arg(e) end
        if (token == "#") arg = parse_expr(11); return function(e) return #arg(e) end
        if (token == "@") arg = parse_expr(11); return function(e) return @arg(e) end
        if (token == "%") arg = parse_expr(11); return function(e) return %arg(e) end
        if (token == "$") arg = parse_expr(11); return function(e) return $arg(e) end
                if (token == 'function') return parse_function()
                if (token == "...") return vararg_node()
                if token == '?' then
            local print_node, nodes = var_node 'print', parse_list(parse_expr);
            return function (e) return (print_node(e)(depack(eval_nodes(e, nodes)))) end, false, nil, nil, true
        end
                if (token == "\\") arg = require_ident() return function() return cmd_exec(arg) end, true, function() return cmd_assign(arg) end
                if (require_ident(token)) return var_node(token), true, assign_node(token)
        fail("unexpected token: " .. token)
    end

        local function parse_binary_op(token, prec, left, right_expr)
        local right
        if (token == "^" and prec <= 12) right = right_expr(12); return function(e,v) return left(e,v) ^ right(e) end
        if (token == "*" and prec < 10) right = right_expr(10); return function(e,v) return left(e,v) * right(e) end
        if (token == "/" and prec < 10) right = right_expr(10); return function(e,v) return left(e,v) / right(e) end
        if (token == "\\" and prec < 10) right = right_expr(10); return function(e,v) return left(e,v) \ right(e) end
        if (token == "%" and prec < 10) right = right_expr(10); return function(e,v) return left(e,v) % right(e) end
        if (token == "+" and prec < 9) right = right_expr(9); return function(e,v) return left(e,v) + right(e) end
        if (token == "-" and prec < 9) right = right_expr(9); return function(e,v) return left(e,v) - right(e) end
        if (token == ".." and prec <= 8) right = right_expr(8); return function(e,v) return left(e,v) .. right(e) end
        if (token == "<<" and prec < 7) right = right_expr(7); return function(e,v) return left(e,v) << right(e) end
        if (token == ">>" and prec < 7) right = right_expr(7); return function(e,v) return left(e,v) >> right(e) end
        if (token == ">>>" and prec < 7) right = right_expr(7); return function(e,v) return left(e,v) >>> right(e) end
        if (token == "<<>" and prec < 7) right = right_expr(7); return function(e,v) return left(e,v) <<> right(e) end
        if (token == ">><" and prec < 7) right = right_expr(7); return function(e,v) return left(e,v) >>< right(e) end
        if (token == "&" and prec < 6) right = right_expr(6); return function(e,v) return left(e,v) & right(e) end
        if ((token == "^^" or token == "~") and prec < 5) right = right_expr(5); return function(e,v) return left(e,v) ^^ right(e) end
        if (token == "|" and prec < 4) right = right_expr(4); return function(e,v) return left(e,v) | right(e) end
        if (token == "<" and prec < 3) right = right_expr(3); return function(e,v) return left(e,v) < right(e) end
        if (token == ">" and prec < 3) right = right_expr(3); return function(e,v) return left(e,v) > right(e) end
        if (token == "<=" and prec < 3) right = right_expr(3); return function(e,v) return left(e,v) <= right(e) end
        if (token == ">=" and prec < 3) right = right_expr(3); return function(e,v) return left(e,v) >= right(e) end
        if (token == "==" and prec < 3) right = right_expr(3); return function(e,v) return left(e,v) == right(e) end
        if ((token == "~=" or token == "!=") and prec < 3) right = right_expr(3); return function(e,v) return left(e,v) ~= right(e) end
        if (token == "and" and prec < 2) right = right_expr(2); return function(e,v) return left(e,v) and right(e) end
        if (token == "or" and prec < 1) right = right_expr(1); return function(e,v) return left(e,v) or right(e) end
    end

        local function parse_expr_more(prec, left, isprefix)
        local token = tokens[ti]; ti += 1
        local right, arg
        if isprefix then
                        if (token == '.') right = require_ident(); return function(e) return left(e)[right] end, true, function(e) return left(e), right end
                        if (token == '[') right = parse_expr(); require ']'; return function(e) return left(e)[right(e)] end, true, function(e) return left(e), right(e) end
                        if (token == "(") return parse_call(left)
                        if (token == "{" or type(token) == "table") ti -= 1; arg = parse_core(); return parse_call(left, nil, arg)
                        if token == ":" then 
                right = require_ident();
                                if (tokens[ti] == "{" or type(tokens[ti]) == "table") arg = parse_core(); return parse_call(left, right, arg)
                require '('; return parse_call(left, right)
            end
        end
        
                local node = parse_binary_op(token, prec, left, parse_expr)
        if (not node) ti -= 1
        return node
    end

        parse_expr = function(prec)
        local node, isprefix, setnode, callnode, iscall = parse_core()
        while true do
            local newnode, newisprefix, newsetnode, newcallnode, newiscall = parse_expr_more(prec or 0, node, isprefix)
            if (not newnode) break
            node, isprefix, setnode, callnode, iscall = newnode, newisprefix, newsetnode, newcallnode, newiscall
        end
        return node, setnode, callnode, iscall
    end

        local function parse_assign_expr()
        local _, assign_expr = parse_expr()
        if (not assign_expr) fail "cannot assign to value"
        return assign_expr
    end

        local function parse_assign()
        local targets = parse_list(parse_assign_expr)
        require "="
        local sources = parse_list(parse_expr)

        if #targets == 1 and #sources == 1 then return function(e)
                        local d,k = targets[1](e); d[k] = sources[1](e)
        end else return function(e)
                        local dests, keys = {}, {}
            for i=1,#targets do local d,k = targets[i](e); add(dests,d) add(keys,k) end
            local values = eval_nodes(e, sources)
                        for i=#targets,1,-1 do dests[i][keys[i]] = values[i] end
        end end
    end

        local function parse_op_assign(setnode)
        local token = tokens[ti]; ti += 1
        local op,node = sub(token,1,-2),function(e,v)return v end
                local op_node = parse_binary_op(op, 0, node, function() return parse_expr() end) 
        if (not op_node) fail "invalid compound assignment"
        return function(e) local d,k = setnode(e); d[k] = op_node(e, d[k]) end
    end

        local function parse_local()
        if accept 'function' then
                        return parse_function(true, true)
        else
            local targets,sources = parse_list(require_ident),accept'='and parse_list(parse_expr)or{}
            push_locals()
            for i=1,#targets do locals[targets[i]] = e_len end

            if #targets == 1 and #sources == 1 then return function(e)
                                add(e, {[targets[1]] = sources[1](e)})
            end else return function(e)
                                local scope,values = {},eval_nodes(e,sources)
                for i=1,#targets do scope[targets[i]] = values[i] end
                add(e, scope)
            end end
        end
    end

        local function start_shorthand(allowed)
        local line,prev_endcb = tlines[ti - 1],endcb
        endcb = function(i) return line != tlines[i] end
        if (not allowed or endcb(ti)) fail(ti <= #tokens and "unterminated shorthand" or nil)
        return prev_endcb
    end

        local function end_shorthand(prev_endcb)
        if (endcb(ti-1)) fail("unterminated shorthand")
        endcb = prev_endcb
    end

        local function parse_ifstmt()
        local short,cond,then_b,else_b = tokens[ti] == '(',parse_expr()
        if accept 'then' or accept 'do' then
                        then_b, else_b = parse_block()
            if accept 'else' then else_b = parse_block(); require "end" 
            elseif accept 'elseif' then else_b = parse_ifstmt() 
            else require "end" end
        else
                        local prev = start_shorthand(short)
            then_b = parse_block()
            if (not endcb(ti) and accept 'else') else_b = parse_block() 
            end_shorthand(prev)
        end

        return function(e)
                        if cond(e) then return then_b(e)
            elseif else_b then return else_b(e)
            end
        end
    end

        local function parse_loop_block(...)
        local old_depth = loop_depth
        loop_depth = depth + 1
        local result = parse_block(...)
        loop_depth = old_depth
        return result
    end

        local function handle_break(retval, label)
        if (retval == true) return 
        return retval, label
    end

        local function parse_while()
        local short,cond,body = tokens[ti] == '(',parse_expr()
        if accept 'do' then
                        body = parse_loop_block()
            require 'end'
        else
                        local prev = start_shorthand(short)
            body = parse_loop_block()
            end_shorthand(prev)
        end

        return function(e)
                        while cond(e) do
                if (stat(1)>=1) yield_execute()
                local retval, label = body(e)
                if (retval) return handle_break(retval, label)
            end
        end
    end

        local function parse_repeat()
                local block_e_len,body = e_len,parse_loop_block(true)
        require 'until'
        local cond = parse_expr()
        while (e_len > block_e_len) pop_locals()

        return function(e)
                        repeat
                if (stat(1)>=1) yield_execute()
                local retval, label = body(e)
                if (not retval) label = cond(e) 
                while (#e > block_e_len) deli(e) 
                if (retval) return handle_break(retval, label)
            until label 
        end
    end

        local function parse_for()
        if tokens[ti + 1] == '=' then
                        local varb = require_ident()
            require '='
            local min = parse_expr()
            require ','
            local max,step = parse_expr(),accept','and parse_expr()or const_node(1)
            require 'do'

                        push_locals()
            locals[varb] = e_len
            local body = parse_loop_block()
            require 'end'
            pop_locals()

            return function(e)
                                for i=min(e),max(e),step(e) do
                    if (stat(1)>=1) yield_execute()
                    add(e, {[varb]=i})
                    local retval, label = body(e)
                    deli(e)
                    if (retval) return handle_break(retval, label)
                end
            end
        else
                        local targets = parse_list(require_ident)
            require "in"
            local sources = parse_list(parse_expr)
            require 'do'

                        push_locals()
            for target in all(targets) do locals[target] = e_len end

            local body = parse_loop_block()
            require 'end'
            pop_locals()

            return function(e)
                                local exps = eval_nodes(e, sources)
                while true do
                    local scope,vars = {},{exps[1](exps[2],exps[3])}

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

        local function parse_break()
        if (not loop_depth or func_depth and loop_depth < func_depth) fail "break outside of loop"
        return function() return true end
    end

        local function parse_return()

        if tokens[ti] == ';' or at_stmt_end() then
                        return function() return pack() end
        else
            local node, _, callnode = parse_expr()
            local nodes = {node}
            while (accept ',') add(nodes, (parse_expr()))

            if #nodes == 1 and callnode and func_depth then
                                return function(e) local func, args = callnode(e);
                    if (stat(1)>=1) yield_execute()
                    return function() return func(depack(args)) end
                end
            else
                                return function(e) return eval_nodes(e, nodes) end
            end
        end
    end

        local function parse_label(parent)
        local label = require_ident()
        require '::'
        if (labels[label] and labels[label].depth == depth) fail "label already defined"
                labels[label] = {e_len=e_len, depth=depth, block=parent, i=#parent}
    end

        local function parse_goto()
        local label,labels_c,e_len_c,value = require_ident(),labels,e_len
                add(gotos, function ()
            value = labels_c[label]
            if (not value) fail "label not found"
            if (func_depth and value.depth < func_depth) fail "goto outside of function"
                        local goto_e_len = labels_c[value.depth] or e_len_c
            if (value.e_len > goto_e_len and value.i < #value.block) fail "goto past local"
        end)

        return function()
            if (stat(1)>=1) yield_execute()
            return 0, value
        end
    end

        local function parse_stmt(parent)
        local token = tokens[ti]; ti += 1
                if (token == ';') return
                if (token == 'do') local node = parse_block(); require 'end'; return node
                if (token == 'if') return parse_ifstmt()
                if (token == 'while') return parse_while()
                if (token == 'repeat') return parse_repeat()
                if (token == 'for') return parse_for()
                if (token == 'break') return parse_break()
                if (token == 'return') return parse_return(), true
                if (token == 'local') return parse_local()
                if (token == 'goto') return parse_goto()
                if (token == '::') return parse_label(parent)
                if (token == 'function' and tokens[ti] != '(') return parse_function(true)

                ti -= 1
        local start,node,setnode,tailcall,iscall = ti,parse_expr() 
        if accept ',' or accept '=' then
            ti = start; return parse_assign()
                elseif is_op_assign(tokens[ti]) then
            return parse_op_assign(setnode)
                elseif depth <= 1 and g_enable_repl then
            return function (e)
                local results = pack(node(e))
                                if (not (iscall and (results.n == 0 or not tailcall))) add(g_results, results)
                g_last_value = results[1]
            end
                else
            if (not iscall) fail "statement has no effect"
            return function(e) node(e) end
        end
    end

        parse_block = function(keep_locals)
                labels = setmetatable({}, {__index=labels})
        labels[depth] = e_len

                depth += 1
        local block_depth,block_e_len,block = depth,keep_locals and 0x7fffor e_len,{}
                
while ti <= #tokens and not at_stmt_end() do
            local  stmt, need_end =  parse_stmt(block)
            if (stmt) add(block, stmt) 
            if (need_end) accept ';'; break
        end

                while (e_len > block_e_len) pop_locals()
        depth -= 1
        labels = getmetatable(labels).__index

        return function (e)
                        local i,n, retval, label=1,#block
            while i <= n do
                
                retval, label = block[i](e)
                if retval then
                                        if (type(retval) != "number") break
                                        if (label.depth != block_depth) break
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
    
        locals = g_enable_repl and {_ENV=0, _env=0, _=0} or {_ENV=0}
    locals['...'] = 0
        local root = parse_block()
    if (ti <= #tokens) fail "unexpected end"
        for g in all(gotos) do g() end

    return function(env, ...)
                local scope = g_enable_repl and {_ENV=env, _env=env, _=g_last_value} or {_ENV=env}
        scope['...'] = pack(...)
        
                        
        local retval = root{[0]=scope}
        
        if (retval) return depack(retval)
    end
end

g_show_max_items, g_hex_output, g_precise_output = 10, false, false


local unescapes = {["\0"]="000",["\014"]="014",["\015"]="015"}
for k, v in pairs(escapes) do 
    if (not isoneof(k, "'\n")) unescapes[v] = k
end

function requote(str)
    local i = 1
    while i <= #str do
        local ch = str[i]
        local nch = unescapes[ch]
        if (nch) str = sub(str,1,i-1) .. '\\' .. nch .. sub(str,i+1); i += #nch
        i += 1
    end
    return '"' .. str .. '"'
end

function is_identifier(key)
    if (type(key) != 'string') return false
    if (keyword_map[key]) return false
    if (#key == 0 or isdigit(key[1])) return false
    for i=1,#key do
        if (not isalnum(key[i])) return false
    end
    return true
end

function value_to_str(val, depth)
    local ty = type(val)
        if (ty == 'nil') then
        return 'nil'
        elseif (ty == 'boolean') then
        return val and 'true' or 'false'
        elseif (ty == 'number') then
        if (not g_precise_output) return tostr(val, g_hex_output)
        local str = tostr(val)
        return tonum(str) == val and str or tostr(val,1)
        elseif (ty == 'string') then
        return requote(val)
        elseif (ty == 'table' and not depth) then
        local res,i,prev = '{',0,0
                for k,v in next, val do
            if (i == g_show_max_items) res ..= ',<...>' break
            if (i > 0) res ..= ','
            
            local vstr = value_to_str(v,1)
            if k == prev + 1 then res ..= vstr; prev = k
            elseif is_identifier(k) then res ..= k .. '=' .. vstr
            else res ..= '[' .. value_to_str(k,1) ..']=' .. vstr end
            i += 1
        end
        
        return res .. '}'
        else
        return '<' .. tostr(ty) .. '>'
    end
end
function results_to_str(str, results)
    if (results == nil) return str 
    if (not str) str = ''

    local count = min(21,#results)
    for ir=1, count do
        if (#str > 0) str ..= '\n'

        local result = results[ir]
        if type(result) == 'table' then
            local line = ''
            for i=1,result.n do
                if (#line > 0) line ..= ', '
                line ..= value_to_str(result[i])
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


poke(0x5f2d,1) 
cls()

g_prompt = "> " 
g_input, g_input_lines, g_input_start = "", 1, 0
g_cursor_pos, g_cursor_time = 1, 20
g_history, g_history_i = {''}, 1
g_abort = false
g_num_output_lines, g_line = 0, 1

g_enable_interrupt, g_enable_autoflip = true, true
g_pal = split "7,4,3,5,6,8,5,12,14,7,11,5"

g_ENV.print = function(value, ...)
    if (not g_enable_interrupt or select('#', ...) != 0) return print(value, ...)

    add(g_results, tostr(value))
    local resx, resy = print(value, 1000, 1000) 
    return resx - 1000, resy - 1000 
end

function unpause()
    poke(0x5f30,1)
end

function get_keys()
    return function()
        if (stat(30)) return stat(31)
    end
end

function walk_str(str, cb)
    local i,x,y = 1,0,0
    if (not str) return i, x, y
    while i <= #str do
        local ch = str[i]
        local spch = ch >= '\x80'
        if (x >= (spch and 31 or 32)) y += 1; x = 0
        if (cb) cb(i,ch,x,y)

        if ch == '\n' then y += 1; x = 0
        else x += (spch and 2 or 1) end
        i += 1
    end
    return i, x, y
end

function str_i2xy(str, ci)
    local cx, cy = 0, 0
    local ei, ex, ey = walk_str(str, function(i,ch,x,y)
        if (ci == i) cx, cy = x, y
    end)
    if (ci >= ei) cx, cy = ex, ey
    if (ex > 0) ey += 1
    return cx, cy, ey
end

function str_xy2i(str, cx, cy)
    local ci,found = 1,false
    local ei, ex, ey = walk_str(str, function(i,ch,x,y)
        if (cy == y and cx == x and not found) ci = i; found = true
        if ((cy < y or cy == y and cx < x) and not found) ci = i - 1; found = true
    end)
    if (not found) ci = cy >= ey and ei or ei - 1
    if (ex > 0) ey += 1
    return ci, ey
end

function str_print(str, xpos, ypos, color)
    if type(color) == "function" then
        walk_str(str, function(i,ch,x,y)
            print(ch, xpos + x*4, ypos + y*6, color(i))
        end)
    else
        print(str and "\^rw" .. str, xpos, ypos, color)
    end
end

function str_print_input(input, xpos, ypos)
    local tokens, _, tstarts, tends = tokenize(input) 
    local ti = 1
    str_print(input, xpos, ypos, function(i)
        while ti <= #tends and tends[ti] < i do ti += 1 end

        local token
        if (ti <= #tends and tstarts[ti] <= i) token = tokens[ti]

        local c = g_pal[5]
        if token == false then c = g_pal[6] 
        elseif token == true then c = g_pal[7] 
        elseif type(token) != 'string' or isoneof(token, split"nil,true,false") then c = g_pal[8]
        elseif keyword_map[token] then c = g_pal[9]
        elseif not isalnum(token[1]) then c = g_pal[10]
        elseif globfuncs[token] then c = g_pal[11] end

        return c
    end)
end

function _draw()
    local old_color,old_camx,old_camy = peek(0x5f25),peek2(0x5f28),peek2(0x5f2a)
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
        local cx, cy, ilines = str_i2xy(input, #g_prompt + g_cursor_pos) 
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
        if (g_input_lines>21) rectfill(0,126,127,127,0) 
        str_print_input(input,0,y)
        print(g_prompt,0,y,g_pal[4])

        if (g_cursor_time >= 10 and cursor != false and not g_interrupt) draw_cursor(cx*4, y + cy*6)
    end

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

    ::restart::
    local ostart, olines
    if g_results or g_str_output then
        ostart, olines = str_xy2i(g_str_output, 0, g_num_output_lines)
        if olines - g_num_output_lines <= 20 and g_results then 
            g_str_output, g_results = results_to_str(g_str_output, g_results)
            ostart, olines = str_xy2i(g_str_output, 0, g_num_output_lines)
            if (#g_results == 0 and not g_interrupt) g_results = nil
        end
    end

    if (not g_interrupt) camera()

    if (g_num_output_lines == 0 and not g_interrupt) draw_input(not g_str_output)

    if g_str_output then
        local output,page_olines = sub(g_str_output, ostart),min(olines-g_num_output_lines,20)
        scroll(page_olines)
        str_print(output,0,(g_line - page_olines)*6,g_pal[1])

        if page_olines < olines - g_num_output_lines then
            if (page_interrupt(page_olines)) goto restart
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


g_in_execute_yield, g_in_mainloop, g_from_flip = false, false, false
g_pending_keys = {}
function on_compile_fail(err, idx)
    g_error, g_error_idx = err, idx
    assert(false, err)
end

function execute_raw(line, env, ...)
    return parse(line)(env or g_ENV, ...)
end

function eval_raw(expr, env, ...)
    return execute_raw("return " .. expr, env, ...)
end

function try_parse(line)
    local cc = cocreate(parse)
    ::_::
    local ok, result = coresume(cc, line)
    if (ok and not result) goto _ 
    if (not ok) result, g_error = g_error, false
    return ok, result
end

function pos_to_str(line, idx)
    local x, y = str_i2xy(line, idx)
    return "line " .. y+1 .. " col " .. x+1
end

function execute(line, complete)
    g_results, g_abort, g_error = {}, false, false
    g_in_execute_yield, g_in_mainloop, g_from_flip = false, false, false

        local coro,_ok,error = cocreate(function () 
        local results = pack(execute_raw(line))
        if (results.n != 0) add(g_results, results)
    end)
    while true do
        _ok, error = coresume(coro)
        if (costatus(coro) == 'dead') break

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

                if (g_abort) error = 'computation aborted'; break
    end

    if g_error == nil then 
        if (complete) error = "unexpected end of code" else error, g_results = nil
    end
    if (g_error) error, g_error = g_error .. "\nat " .. pos_to_str(line, g_error_idx)
    g_error_output = error
    g_pending_keys = {}
    return not error
end

yield_execute = function ()
        g_in_execute_yield = true
    yield()
    g_in_execute_yield = false
end

g_ENV.flip = function(...)
    local results = pack(flip(...))
    g_from_flip = true
    yield_execute()
    return depack(results)
end

g_ENV.coresume = function(co, ...)
    local results = pack(coresume(co, ...))
        while g_in_execute_yield do
        yield()
        results = pack(coresume(co)) 
    end
    g_error = false 
    return depack(results)
end

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

function do_mainloop(env, continue)
    if not continue then
        if (_set_fps) _set_fps(env._update60 and 60 or 30)
        if (env._init) env._init()
    end
    g_in_mainloop = true
    while env._draw or env._update or env._update60 do
                if (holdframe) holdframe()
        if env._update60 then env._update60() elseif env._update then env._update() end
        if (env._draw) env._draw()
        flip()
        g_from_flip = true
        yield_execute()
    end
    g_in_mainloop = false
end


k_old_code_table = "\n 0123456789abcdefghijklmnopqrstuvwxyz!#%(){}[]<>+=/*:;.,~_"

function uncompress_code_old(comp)
    local code, i = "", 9
    while true do
        local ch = ord(comp, i); i += 1
        if ch == 0 then
                        local ch2 = comp[i]; i += 1
            if (ch2 == '\0') break 
            code ..= ch2
        elseif ch <= 0x3b then
                        code ..= k_old_code_table[ch]
        else
                        local ch2 = ord(comp, i); i += 1
            local count,offset = (ch2 >> 4) + 2,((ch-0x3c)<<4)+(ch2&0xf) 
            for _=1,count do
                code ..= code[-offset]
            end
        end
    end
    return code
end

function uncompress_code_new(comp)
    local code, i, shift, mtf = "", 9, 0, {}
    comp..="\0\0\0" 
    for idx=0,0xff do mtf[idx] = chr(idx) end

    local function getbit()
        local bit = (ord(comp, i) >> shift) & 1
        shift += 1
        if (shift == 8) i += 1; shift = 0
        return bit == 1
    end
    local function getbits(n)
        local value = 0
        for bit=0,n-1 do 
            value |= tonum(getbit()) << bit
        end
        return value
    end

    while true do
        if getbit() then
                        local nbits, idx = 4, 0
            while (getbit()) idx |= 1 << nbits; nbits += 1
            idx += getbits(nbits)

            local ch = mtf[idx]
            code ..= ch

                        for j=idx,1,-1 do
                mtf[j] = mtf[j-1]
            end
            mtf[0] = ch
        else
                        local obits = getbit() and (getbit() and 5 or 10) or 15
            local offset = getbits(obits) + 1

            if offset == 1 and obits == 15 then
                break 
            elseif offset == 1 and obits == 10 then
                                while true do
                    local ch = getbits(8)
                    if (ch == 0) break else code ..= chr(ch)
                end
            else
                local count = 3
                repeat
                    local part = getbits(3)
                    count += part
                until part != 7

                for _=1,count do
                                        code ..= code[-offset]
                end
            end
        end
    end
    return code
end

g_prev_paste = stat(4)
g_key_time, g_lower = 0, false

poke(0x5f5c,10,2) 
function keyp(code)
    if stat(28,code) then
        if (code != g_key_code) g_key_code, g_key_time = code, 0
        return g_key_time == 0 or (g_key_time >= 10 and g_key_time % 2 == 0)
    elseif g_key_code == code then
        g_key_code = nil
    end
end

function _update()
    local input = false

    local function go_line(dy)
        local cx, cy, h = str_i2xy(g_prompt .. g_input, #g_prompt + g_cursor_pos)
        if (g_ideal_x) cx = g_ideal_x
        cy += dy
        if (not (cy >= 0 and cy < h)) return false
        g_cursor_pos = max(str_xy2i(g_prompt .. g_input, cx, cy) - #g_prompt, 1)
        g_ideal_x = cx
        g_cursor_time = 20 
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
            g_cursor_pos = max(str_xy2i(g_prompt .. g_input, 32, 0) - #g_prompt, 1) 
            local ch = g_input[g_cursor_pos]
            if (ch and ch != '\n') g_cursor_pos -= 1
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

    local ctrl,shift,keycode = stat(28,224) or stat(28,228),stat(28,225)or stat(28,229),-1
    if keyp(80) then 
        if (g_cursor_pos > 1) g_cursor_pos -= 1; input = true
    elseif keyp(79) then 
        if (g_cursor_pos <= #g_input) g_cursor_pos += 1; input = true
    elseif keyp(82) then 
        if ((ctrl or not go_line(-1)) and g_history_i > 1) go_history(-1)
    elseif keyp(81) then 
        if ((ctrl or not go_line(1)) and g_history_i < #g_history) go_history(1)
    else
        local key = stat(31)
        keycode = ord(key)

        if key == '\x1b' then 
            if #g_input == 0 then extcmd "pause"
            else g_results, g_error_output = {}; push_history() end
        elseif key == '\r' or key == '\n' then 
            if shift then
                inschar '\n'
            else
                execute(g_input) 
                if (not g_results) inschar '\n' else push_history()
            end
        elseif ctrl and keyp(40) then 
            execute(g_input, true); push_history()
        elseif key != '' and keycode >= 0x20 and keycode < 0x9a then 
            if (g_lower and keycode >= 0x80) key = chr(keycode - 63)
            inschar(key)
        elseif keycode == 193 then 
            inschar '\n'
        elseif keycode == 192 then 
            go_edge(-1)
        elseif keycode == 196 then 
            go_edge(1)
        elseif keycode == 203 then 
            g_lower = not g_lower
            g_notice, g_notice_time = "shift now selects " .. (g_lower and "punycase" or "symbols"), 40
        elseif keyp(74) then 
            if (ctrl) g_cursor_pos = 1; input = true else go_edge(-1);
        elseif keyp(77) then 
            if (ctrl) g_cursor_pos = #g_input + 1; input = true else go_edge(1);        
        elseif keyp(42) then delchar(-1) 
        elseif keyp(76) then delchar(0) 
        end
    end

    local paste = stat(4)
    if (paste != g_prev_paste or keycode == 213) inschar(paste); g_prev_paste = paste 
    if keycode == 194 or keycode == 215 then 
        if g_input != '' and g_input != g_prev_paste then
            g_prev_paste = g_input; printh(g_input, "@clip");
            if (keycode == 215) g_input = ''; g_cursor_pos = 1;
            g_notice = "press again to put in clipboard"
        else
            g_notice = ''
        end
    end

    if stat(120) then 
        local str, count = ""
        repeat
            count = serial(0x800,0x5f80,0x80)
            str ..= chr(peek(0x5f80,count))
        until count == 0
        if (not load_cart(str)) inschar(str)
    end

    if (input) g_cursor_time, g_ideal_x = 20
    g_key_time += 1

    unpause()
end

function toplevel_main()
    local passed = false -- just in case
    selftest(3, function() assert(execute_raw "\\h=1; return \\ts{1,0x.0001,a=true}" == "{0x0001.0000,0x0000.0001,a=true}"); passed = true; end)
    assert(passed)
    printh("finished")stop()
    --[[
    while true do
        if (holdframe) holdframe()
        _update()
        _draw()
        flip()
    end
    ]]
end


function selftest(i, cb)
    local ccb = cocreate(cb)
    local ok, error = coresume(ccb)
    while (ok and costatus(ccb) != 'dead') ok, error = coresume(ccb)
    if not ok then
        printh("error #" .. i .. ": " .. error)
        print("error #" .. i .. "\npico8 broke something again,\nthis cart may not work.\npress any button to ignore")
        while (btnp() == 0) flip()
        cls()
    end
end

selftest(1, function() assert(pack(eval_raw "(function (...) return ... end)(1,2,nil,nil)" ).n == 4) end)
selftest(2, function() assert(eval_raw "function() local temp, temp2 = {max(1,3)}, -20;return temp[1] + temp2; end" () == -17) end)


_ENV.g_ENV = g_ENV 
execute_raw([[
function cmd_exec(name)
    if isoneof(name, {"i","interrupt"}) then
        return g_enable_interrupt
    elseif isoneof(name, {"f","flip"}) then
        return g_enable_autoflip
    elseif isoneof(name, {"r","repl"}) then
        return g_enable_repl
    elseif isoneof(name, {"mi","max_items"}) then
        return g_show_max_items
    elseif isoneof(name, {"h","hex"}) then
        return g_hex_output
    elseif isoneof(name, {"pr","precise"}) then
        return g_precise_output
    elseif isoneof(name, {"cl","colors"}) then
        return g_pal
    elseif isoneof(name, {"c","code"}) then
        local code = {[0]=g_input}
        for i=1,#g_history-1 do code[i] = g_history[#g_history-i] end
        return code
    elseif isoneof(name, {"cm","compile"}) then
        return function(str) return try_parse(str) end
    elseif isoneof(name, {"x","exec"}) then
        return function(str, env, ...) execute_raw(str, env, ...) end
    elseif isoneof(name, {"v","eval"}) then
        return function(str, env, ...) return eval_raw(str, env, ...) end
    elseif isoneof(name, {"p","print"}) then
        return function(str, ...) g_ENV.print(value_to_str(str), ...) end
    elseif isoneof(name, {"ts","tostr"}) then
        return function(str) return value_to_str(str) end
    elseif isoneof(name, {"rst","reset"}) then
        run() 
    elseif isoneof(name, {"run"}) then
        do_mainloop(g_ENV)
    elseif isoneof(name, {"cont"}) then
        do_mainloop(g_ENV, true)
    else
        assert(false, "unknown \\-command")
    end
end

function cmd_assign(name)
    local function trueish(t)
        return (t and t != 0) and true or false
    end

    local func
    if isoneof(name, {"i","interrupt"}) then
        func = function(v) g_enable_interrupt = trueish(v) end
    elseif isoneof(name, {"f","flip"}) then
        func = function(v) g_enable_autoflip = trueish(v) end
    elseif isoneof(name, {"r","repl"}) then
        func = function(v) g_enable_repl = trueish(v) end
    elseif isoneof(name, {"mi","max_items"}) then
        func = function(v) g_show_max_items = tonum(v) or -1 end
    elseif isoneof(name, {"h","hex"}) then
        func = function(v) g_hex_output = trueish(v) end
    elseif isoneof(name, {"pr","precise"}) then
        func = function(v) g_precise_output = trueish(v) end
    elseif isoneof(name, {"cl","colors"}) then
        func = function(v) g_pal = v end
    else
        assert(false, "unknown \\-command assign")
    end

        local obj = {
        __newindex=function(t,k,v) func(v) end,
        __index=function() return cmd_exec(name) end, 
    }
    return setmetatable(obj, obj), 0
end


function load_cart(str)
        local code, full = sub(str, 0x4301)
    if #code == 0x3d00 then
        full = true
        poke(0, ord(str, 1, 0x4300)) 
    else
        code = str 
    end

    local header = sub(code, 1, 4)
    if header == ":c:\0" then
        code = uncompress_code_old(code)
    elseif header == "\0pxa" then
        code = uncompress_code_new(code)
    elseif full then
        code = split(code, '\0')[1]
    else
                return
    end

        g_enable_interrupt, g_enable_repl = false, false
    local ok = execute(code, true)
    g_enable_repl = true
    if (ok) execute("\\run") 
    return true
end

toplevel_main()]], _ENV)
