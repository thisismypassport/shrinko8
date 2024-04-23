pico-8 cartridge // http://www.pico-8.com
version 42
__lua__

--------------------------------------
-- Please see 'Commented Source Code' section in the BBS
-- for the original commented source code
-- (The below had the comments stripped due to cart size limits)
--------------------------------------
local e, n, l = _ENV, {}, {}
for e, t in pairs(_ENV) do
  n[e] = t
  if type(t) == "function" then
    l[e] = true
  end
end
local _ENV = n
J, nt = true

function p(t, e)
  for n = 1, #e do
    if sub(e, n, n) == t then
      return n
    end
  end
end

function b(e, n)
  return sub(e, n, n)
end

local n, t, o = split "a,b,f,n,r,t,v,\\,\",',\n,*,#,-,|,+,^", split "⁷,⁸,ᶜ,\n,\r,	,ᵇ,\\,\",',\n,¹,²,³,⁴,⁵,⁶", {}
for e = 1, #n do
  o[n[e]] = t[e]
end

function y(n)
  return n >= "0" and n <= "9"
end

function D(n)
  return n >= "A" and n <= "Z" or n >= "a" and n <= "z" or n == "_" or n >= "█" or y(n)
end

function nc(l, n, i, r)
  local e = ""
  while n <= #l do
    local t = b(l, n)
    if t == i then
      break
    end
    if t == "\\" then
      n += 1
      local e = b(l, n)
      t = o[e]
      if e == "x" then
        e = tonum("0x" .. sub(l, n + 1, n + 2))
        if e then
          n += 2
        else
          r "bad hex escape"
        end
        t = chr(e)
      elseif y(e) then
        local o = n
        while y(e) and n < o + 3 do
          n += 1
          e = b(l, n)
        end
        n -= 1
        e = tonum(sub(l, o, n))
        if not e or e >= 256 then
          r "bad decimal escape"
        end
        t = chr(e)
      elseif e == "z" then
        repeat
          n += 1
          e = b(l, n)
        until not p(e, " \r	ᶜᵇ\n")
        if e == "" then
          r()
        end
        t = ""
        n -= 1
      elseif e == "" then
        r()
        t = ""
      end
      if not t then
        r("bad escape: " .. e)
        t = ""
      end
    elseif t == "\n" then
      r "unterminated string"
      break
    end
    e ..= t
    n += 1
  end
  if n > #l then
    r("unterminated string", true)
  end
  return e, n + 1
end

function Z(e, n, t, l)
  if b(e, n) == "[" then
    n += 1
    local l = n
    while b(e, n) == "=" do
      n += 1
    end
    local l = "]" .. sub(e, l, n - 1) .. "]"
    local r = #l
    if b(e, n) == "[" then
      n += 1
      if b(e, n) == "\n" then
        n += 1
      end
      local o = n
      while n <= #e and sub(e, n, n + r - 1) ~= l do
        n += 1
      end
      if n >= #e then
        t()
      end
      return sub(e, o, n - 1), n + r
    end
  end
  if l then
    t "invalid long brackets"
  end
  return nil, n
end

function nl(t, u)
  local n, a, r, c, s, h, f, o = 1, 1, {}, {}, {}, {}

  local function i(n, e)
    if u then
      nr(n, o)
    end
    f = n and not e
  end

  while n <= #t do
    o = n
    local e, d, l = b(t, n)
    if p(e, " \r	ᶜᵇ\n") then
      n += 1
      d = true
      if e == "\n" then
        a += 1
      end
    elseif e == "-" and b(t, n + 1) == "-" then
      n += 2
      if b(t, n) == "[" then
        l, n = Z(t, n, i)
      end
      if not l then
        while n <= #t and b(t, n) ~= "\n" do
          n += 1
        end
      end
      if u then
        d = true
      else
        add(r, true)
      end
    elseif y(e) or e == "." and y(b(t, n + 1)) then
      local f, d = "0123456789", true
      if e == "0" and p(b(t, n + 1), "xX") then
        f ..= "AaBbCcDdEeFf"
        n += 2
      elseif e == "0" and p(b(t, n + 1), "bB") then
        f = "01"
        n += 2
      end
      while true do
        e = b(t, n)
        if e == "." and d then
          d = false
        elseif not p(e, f) then
          break
        end
        n += 1
      end
      l = sub(t, o, n - 1)
      if not tonum(l) then
        i "bad number"
        l = "0"
      end
      add(r, tonum(l))
    elseif D(e) then
      while D(b(t, n)) do
        n += 1
      end
      add(r, sub(t, o, n - 1))
    elseif e == "'" or e == '"' then
      l, n = nc(t, n + 1, e, i)
      add(r, {t = l})
    elseif e == "[" and p(b(t, n + 1), "=[") then
      l, n = Z(t, n, i, true)
      add(r, {t = l})
    else
      n += 1
      local l, f, d = unpack(split(sub(t, n, n + 2), ""))
      if l == e and f == e and p(e, ".>") then
        n += 2
        if d == "=" and p(e, ">") then
          n += 1
        end
      elseif l == e and f ~= e and p(e, "<>") and p(f, "<>") then
        n += 2
        if d == "=" then
          n += 1
        end
      elseif l == e and p(e, ".:^<>") then
        n += 1
        if f == "=" and p(e, ".^<>") then
          n += 1
        end
      elseif l == "=" and p(e, "+-*/\\%^&|<>=~!") then
        n += 1
      elseif p(e, "+-*/\\%^&|<>=~#(){}[];,?@$.:") then
      else
        i("bad char: " .. e)
      end
      add(r, sub(t, o, n - 1))
    end
    if not d then
      add(c, a)
      add(s, o)
      add(h, n - 1)
    end
    if f then
      r[#r], f = false, false
    end
  end
  return r, c, s, h
end

function q(t, n)
  for e = 1, #n do
    if n[e] == t then
      return e
    end
  end
end

function H(n)
  return unpack(n, 1, n.n)
end

function n1(e)
  local n = {}
  for e, t in next, e do
    n[e] = t
  end
  return n
end

local n = split "and,break,do,else,elseif,end,false,for,function,goto,if,in,local,nil,not,or,repeat,return,then,true,until,while"
L = {}
for n in all(n) do
  L[n] = true
end

local function Z(n)
  return type(n) == "string" and b(n, #n) == "="
end

no = split "end,else,elseif,until"

function ni(n, X)
  local r, B, t = nl(n, true)
  local n, i, u, x, f, s, h, e, c, m, a, v = 1, 0, 0, {}

  local function o(e)
    nr(e, t[n - 1] or 1)
  end

  local function p(n)
    return function()
      return n
    end
  end

  local function _(e)
    local n = f[e]
    if n then
      return function(t)
        return t[n][e]
      end
    else
      n = f._ENV
      return function(t)
        return t[n]._ENV[e]
      end
    end
  end

  local function C()
    local n = f["..."]
    if not n or n ~= v then
      o "unexpected '...'"
    end
    return function(e)
      return H(e[n]["..."])
    end
  end

  local function A(e)
    local n = f[e]
    if n then
      return function(t)
        return t[n], e
      end
    else
      n = f._ENV
      return function(t)
        return t[n]._ENV, e
      end
    end
  end

  local function t(e)
    local t = r[n]
    n += 1
    if t == e then
      return
    end
    if t == nil then
      o()
    end
    o("expected: " .. e)
  end

  local function d(e)
    if not e then
      e = r[n]
      n += 1
    end
    if e == nil then
      o()
    end
    if type(e) == "string" and D(b(e, 1)) and not L[e] then
      return e
    end
    if type(e) == "string" then
      o("invalid identifier: " .. e)
    end
    o "identifier expected"
  end

  local function l(e)
    if r[n] == e then
      n += 1
      return true
    end
  end

  local function g()
    f = setmetatable({}, {__index = f})
    i += 1
  end

  local function k()
    f = getmetatable(f).__index
    i -= 1
  end

  local function b(l, t)
    local e, n = {}, #t
    for n = 1, n - 1 do
      e[n] = t[n](l)
    end
    if n > 0 then
      local t = pack(t[n](l))
      if t.n ~= 1 then
        for l = 1, t.n do
          e[n + l - 1] = t[l]
        end
        n += t.n - 1
      else
        e[n] = t[1]
      end
    end
    e.n = n
    return e
  end

  local function w(e)
    local n = {}
    add(n, (e()))
    while l "," do
      add(n, (e()))
    end
    return n
  end

  local function y(r, o, i)
    local n = {}
    if i then
      add(n, i)
    elseif not l ")" then
      while true do
        add(n, (e()))
        if l ")" then
          break
        end
        t ","
      end
    end
    if o then
      return function(e)
        local t = r(e)
        return t[o](t, H(b(e, n)))
      end, true, nil, function(e)
        local t = r(e)
        return t[o], pack(t, H(b(e, n)))
      end
    else
      return function(e)
        return r(e)(H(b(e, n)))
      end, true, nil, function(e)
        return r(e), b(e, n)
      end
    end
  end

  local function D()
    local o, u, c, a = {}, {}, 1
    while not l "}" do
      a = nil
      local i, f
      if l "[" then
        i = e()
        t "]"
        t "="
        f = e()
      elseif r[n + 1] == "=" then
        i = p(d())
        t "="
        f = e()
      else
        i = p(c)
        f = e()
        c += 1
        a = #o + 1
      end
      add(o, i)
      add(u, f)
      if l "}" then
        break
      end
      if not l ";" then
        t ","
      end
    end
    return function(e)
      local t = {}
      for n = 1, #o do
        if n == a then
          local l, n = o[n](e), pack(u[n](e))
          for e = 1, n.n do
            t[l + e - 1] = n[e]
          end
        else
          t[o[n](e)] = u[n](e)
        end
      end
      return t
    end
  end

  local function z(s, h)
    local n, b, e
    if s then
      if h then
        g()
        n = d()
        f[n] = i
        e = A(n)
      else
        n = {d()}
        while l "." do
          add(n, d())
        end
        if l ":" then
          add(n, d())
          b = true
        end
        if #n == 1 then
          e = A(n[1])
        else
          local t = _(n[1])
          for e = 2, #n - 1 do
            local l = t
            t = function(t)
              return l(t)[n[e]]
            end
          end
          e = function(e)
            return t(e), n[#n]
          end
        end
      end
    end
    local n, r = {}
    if b then
      add(n, "self")
    end
    t "("
    if not l ")" then
      while true do
        if l "..." then
          r = true
        else
          add(n, d())
        end
        if l ")" then
          break
        end
        t ","
        if r then
          o "unexpected param after '...'"
        end
      end
    end
    g()
    for n in all(n) do
      f[n] = i
    end
    if r then
      f["..."] = i
    end
    local l, o, f = x, a, v
    x, a, v = {}, u + 1, i
    local i = c()
    for n in all(x) do
      n()
    end
    x, a, v = l, o, f
    t "end"
    k()
    return function(t)
      if h then
        add(t, {})
      end
      local l = n1(t)
      local o = #l
      local n = function(...)
        local t, e = pack(...), l
        if #e ~= o then
          local n = {}
          for t = 0, o do
            n[t] = e[t]
          end
          e = n
        end
        local l = {}
        for e = 1, #n do
          l[n[e]] = t[e]
        end
        if r then
          l["..."] = pack(unpack(t, #n + 1, t.n))
        end
        add(e, l)
        local n = i(e)
        deli(e)
        if n then
          if type(n) == "table" then
            return H(n)
          end
          return n()
        end
      end
      if s then
        local e, t = e(t)
        e[t] = n
      else
        return n
      end
    end
  end

  local function v()
    local l = r[n]
    n += 1
    local n
    if l == nil then
      o()
    end
    if l == "nil" then
      return p()
    end
    if l == "true" then
      return p(true)
    end
    if l == "false" then
      return p(false)
    end
    if type(l) == "number" then
      return p(l)
    end
    if type(l) == "table" then
      return p(l.t)
    end
    if l == "{" then
      return D()
    end
    if l == "(" then
      n = e()
      t ")"
      return function(e)
        return (n(e))
      end, true
    end
    if l == "-" then
      n = e(11)
      return function(e)
        return -n(e)
      end
    end
    if l == "~" then
      n = e(11)
      return function(e)
        return ~n(e)
      end
    end
    if l == "not" then
      n = e(11)
      return function(e)
        return not n(e)
      end
    end
    if l == "#" then
      n = e(11)
      return function(e)
        return #n(e)
      end
    end
    if l == "@" then
      n = e(11)
      return function(e)
        return @n(e)
      end
    end
    if l == "%" then
      n = e(11)
      return function(e)
        return %n(e)
      end
    end
    if l == "$" then
      n = e(11)
      return function(e)
        return $n(e)
      end
    end
    if l == "function" then
      return z()
    end
    if l == "..." then
      return C()
    end
    if l == "\\" then
      n = d()
      return function()
        return ns(n)
      end, true, function()
        return nh(n)
      end
    end
    if d(l) then
      return _(l), true, A(l)
    end
    o("unexpected token: " .. l)
  end

  local function A(e, t, l, r)
    local n
    if e == "^" and t <= 12 then
      n = r(12)
      return function(e)
        return l(e) ^ n(e)
      end
    end
    if e == "*" and t < 10 then
      n = r(10)
      return function(e)
        return l(e) * n(e)
      end
    end
    if e == "/" and t < 10 then
      n = r(10)
      return function(e)
        return l(e) / n(e)
      end
    end
    if e == "\\" and t < 10 then
      n = r(10)
      return function(e)
        return l(e) \ n(e)
      end
    end
    if e == "%" and t < 10 then
      n = r(10)
      return function(e)
        return l(e) % n(e)
      end
    end
    if e == "+" and t < 9 then
      n = r(9)
      return function(e)
        return l(e) + n(e)
      end
    end
    if e == "-" and t < 9 then
      n = r(9)
      return function(e)
        return l(e) - n(e)
      end
    end
    if e == ".." and t <= 8 then
      n = r(8)
      return function(e)
        return l(e) .. n(e)
      end
    end
    if e == "<<" and t < 7 then
      n = r(7)
      return function(e)
        return l(e) << n(e)
      end
    end
    if e == ">>" and t < 7 then
      n = r(7)
      return function(e)
        return l(e) >> n(e)
      end
    end
    if e == ">>>" and t < 7 then
      n = r(7)
      return function(e)
        return l(e) >>> n(e)
      end
    end
    if e == "<<>" and t < 7 then
      n = r(7)
      return function(e)
        return l(e) <<> n(e)
      end
    end
    if e == ">><" and t < 7 then
      n = r(7)
      return function(e)
        return l(e) >>< n(e)
      end
    end
    if e == "&" and t < 6 then
      n = r(6)
      return function(e)
        return l(e) & n(e)
      end
    end
    if e == "^^" and t < 5 then
      n = r(5)
      return function(e)
        return l(e) ~ n(e)
      end
    end
    if e == "|" and t < 4 then
      n = r(4)
      return function(e)
        return l(e) | n(e)
      end
    end
    if e == "<" and t < 3 then
      n = r(3)
      return function(e)
        return l(e) < n(e)
      end
    end
    if e == ">" and t < 3 then
      n = r(3)
      return function(e)
        return l(e) > n(e)
      end
    end
    if e == "<=" and t < 3 then
      n = r(3)
      return function(e)
        return l(e) <= n(e)
      end
    end
    if e == ">=" and t < 3 then
      n = r(3)
      return function(e)
        return l(e) >= n(e)
      end
    end
    if e == "==" and t < 3 then
      n = r(3)
      return function(e)
        return l(e) == n(e)
      end
    end
    if (e == "~=" or e == "!=") and t < 3 then
      n = r(3)
      return function(e)
        return l(e) ~= n(e)
      end
    end
    if e == "and" and t < 2 then
      n = r(2)
      return function(e)
        return l(e) and n(e)
      end
    end
    if e == "or" and t < 1 then
      n = r(1)
      return function(e)
        return l(e) or n(e)
      end
    end
  end

  local function C(u, l, a)
    local i = r[n]
    n += 1
    local o, f
    if a then
      if i == "." then
        o = d()
        return function(n)
          return l(n)[o]
        end, true, function(n)
          return l(n), o
        end
      end
      if i == "[" then
        o = e()
        t "]"
        return function(n)
          return l(n)[o(n)]
        end, true, function(n)
          return l(n), o(n)
        end
      end
      if i == "(" then
        return y(l)
      end
      if i == "{" or type(i) == "table" then
        n -= 1
        f = v()
        return y(l, nil, f)
      end
      if i == ":" then
        o = d()
        if r[n] == "{" or type(r[n]) == "table" then
          f = v()
          return y(l, o, f)
        end
        t "("
        return y(l, o)
      end
    end
    local e = A(i, u, l, e)
    if not e then
      n -= 1
    end
    return e
  end

  e = function(r)
    local n, e, t, l = v()
    while true do
      local r, o, i, f = C(r or 0, n, e)
      if not r then
        break
      end
      n, e, t, l = r, o, i, f
    end
    return n, t, l
  end

  local function v()
    local e, n = e()
    if not n then
      o "cannot assign to value"
    end
    return n
  end

  local function C()
    local n = w(v)
    t "="
    local e = w(e)
    if #n == 1 and #e == 1 then
      return function(t)
        local n, l = n[1](t)
        n[l] = e[1](t)
      end
    else
      return function(t)
        local l, r = {}, {}
        for e = 1, #n do
          local n, e = n[e](t)
          add(l, n)
          add(r, e)
        end
        local e = b(t, e)
        for n = #n, 1, -1 do
          l[n][r[n]] = e[n]
        end
      end
    end
  end

  local function D(t, l)
    local r = r[n]
    n += 1
    local n = sub(r, 1, -2)
    local n = A(n, 0, t, function()
      return e()
    end)
    if not n then
      o "invalid compound assignment"
    end
    return function(e)
      local t, l = l(e)
      t[l] = n(e)
    end
  end

  local function E()
    if l "function" then
      return z(true, true)
    else
      local n, e = w(d), l "=" and w(e) or {}
      g()
      for e = 1, #n do
        f[n[e]] = i
      end
      if #n == 1 and #e == 1 then
        return function(t)
          add(t, {[n[1]] = e[1](t)})
        end
      else
        return function(t)
          local l, r = {}, b(t, e)
          for e = 1, #n do
            l[n[e]] = r[e]
          end
          add(t, l)
        end
      end
    end
  end

  local function A(e)
    local t = B[n - 1]
    h = function()
      return t ~= B[n]
    end
    if not e or h() then
      o(n <= #r and "bad shorthand" or nil)
    end
  end

  local function B()
    local r, o, e, n = r[n] == "(", e()
    if l "then" then
      e, n = c()
      if l "else" then
        n = c()
        t "end"
      elseif l "elseif" then
        n = B()
      else
        t "end"
      end
    else
      A(r)
      e = c()
      if not h() and l "else" then
        n = c()
      end
      h = nil
    end
    return function(t)
      if o(t) then
        return e(t)
      elseif n then
        return n(t)
      end
    end
  end

  local function v(...)
    local n = m
    m = u + 1
    local e = c(...)
    m = n
    return e
  end

  local function y(n, e)
    if n == true then
      return
    end
    return n, e
  end

  local function F()
    local r, o, n = r[n] == "(", e()
    if l "do" then
      n = v()
      t "end"
    else
      A(r)
      n = v()
      h = nil
    end
    return function(e)
      while o(e) do
        if stat(1) >= 1 then
          I()
        end
        local n, e = n(e)
        if n then
          return y(n, e)
        end
      end
    end
  end

  local function A()
    local l, r = i, v(true)
    t "until"
    local o = e()
    while i > l do
      k()
    end
    return function(n)
      repeat
        if stat(1) >= 1 then
          I()
        end
        local e, t = r(n)
        if not e then
          t = o(n)
        end
        while #n > l do
          deli(n)
        end
        if e then
          return y(e, t)
        end
      until t
    end
  end

  local function j()
    if r[n + 1] == "=" then
      local r = d()
      t "="
      local o = e()
      t ","
      local d, e = e(), l "," and e() or p(1)
      t "do"
      g()
      f[r] = i
      local l = v()
      t "end"
      k()
      return function(n)
        for e = o(n), d(n), e(n) do
          if stat(1) >= 1 then
            I()
          end
          add(n, {[r] = e})
          local e, t = l(n)
          deli(n)
          if e then
            return y(e, t)
          end
        end
      end
    else
      local l = w(d)
      t "in"
      local e = w(e)
      t "do"
      g()
      for n in all(l) do
        f[n] = i
      end
      local o = v()
      t "end"
      k()
      return function(n)
        local e = b(n, e)
        while true do
          local r, t = {}, {e[1](e[2], e[3])}
          if t[1] == nil then
            break
          end
          e[3] = t[1]
          for n = 1, #l do
            r[l[n]] = t[n]
          end
          if stat(1) >= 1 then
            I()
          end
          add(n, r)
          local e, t = o(n)
          deli(n)
          if e then
            return y(e, t)
          end
        end
      end
    end
  end

  local function p()
    if not m or a and m < a then
      o "break outside of loop"
    end
    return function()
      return true
    end
  end

  local function m()
    if not a and not X then
      o "return outside of function"
    end
    if r[n] == ";" or q(r[n], no) or h and h() then
      return function()
        return pack()
      end
    else
      local n, r, t = e()
      local n = {n}
      while l "," do
        add(n, (e()))
      end
      if #n == 1 and t and a then
        return function(n)
          local n, e = t(n)
          if stat(1) >= 1 then
            I()
          end
          return function()
            return n(H(e))
          end
        end
      else
        return function(e)
          return b(e, n)
        end
      end
    end
  end

  local function g(e)
    local n = d()
    t "::"
    if s[n] and s[n].e == u then
      o "label already defined"
    end
    s[n] = {l = i, e = u, o = e, r = #e}
  end

  local function v()
    local t, e, l, n = d(), s, i
    add(x, function()
      n = e[t]
      if not n then
        o "label not found"
      end
      if a and n.e < a then
        o "goto outside of function"
      end
      local e = e[n.e] or l
      if n.l > e and n.r < #n.o then
        o "goto past local"
      end
    end)
    return function()
      if stat(1) >= 1 then
        I()
      end
      return 0, n
    end
  end

  local function d(f)
    local i = r[n]
    n += 1
    if i == ";" then
      return
    end
    if i == "do" then
      local n = c()
      t "end"
      return n
    end
    if i == "if" then
      return B()
    end
    if i == "while" then
      return F()
    end
    if i == "repeat" then
      return A()
    end
    if i == "for" then
      return j()
    end
    if i == "break" then
      return p()
    end
    if i == "return" then
      return m(), true
    end
    if i == "local" then
      return E()
    end
    if i == "goto" then
      return v()
    end
    if i == "::" then
      return g(f)
    end
    if i == "function" and r[n] ~= "(" then
      return z(true)
    end
    if i == "?" then
      local e, t = _ "print", w(e)
      return function(n)
        e(n)(H(b(n, t)))
      end
    end
    n -= 1
    local i, e, f, t = n, e()
    if l "," or l "=" then
      n = i
      return C()
    elseif Z(r[n]) then
      return D(e, f)
    elseif u <= 1 and J then
      return function(n)
        local n = pack(e(n))
        if not (t and n.n == 0) then
          add(G, n)
        end
        nt = n[1]
      end
    else
      if not t then
        o "statement has no effect"
      end
      return function(n)
        e(n)
      end
    end
  end

  c = function(e)
    s = setmetatable({}, {__index = s})
    s[u] = i
    u += 1
    local a, f, o = u, e and 32767 or i, {}
    while n <= #r and not q(r[n], no) and not (h and h()) do
      local n, e = d(o)
      if n then
        add(o, n)
      end
      if e then
        l ";"
        break
      end
    end
    while i > f do
      k()
    end
    u -= 1
    s = getmetatable(s).__index
    return function(e)
      local l, r, t, n = 1, #o
      while l <= r do
        t, n = o[l](e)
        if t then
          if type(t) ~= "number" then
            break
          end
          if n.e ~= a then
            break
          end
          l = n.r
          while #e > n.l do
            deli(e)
          end
          t, n = nil
        end
        l += 1
      end
      while #e > f do
        deli(e)
      end
      return t, n
    end
  end
  f = J and {_ENV = 0, _env = 0, _ = 0} or {_ENV = 0}
  local e = c()
  if n <= #r then
    o "unexpected end"
  end
  for n in all(x) do
    n()
  end
  return function(n)
    local n = J and {_ENV = n, _env = n, _ = nt} or {_ENV = n}
    local n = e {[0] = n}
    if n then
      return H(n)
    end
  end
end

S, T = 10, false
local t = {["\0"] = "000", ["ᵉ"] = "014", ["ᶠ"] = "015"}
for n, e in pairs(o) do
  if not p(n, "'\n") then
    t[e] = n
  end
end

function n0(n)
  local e = 1
  while e <= #n do
    local l = b(n, e)
    local t = t[l]
    if t then
      n = sub(n, 1, e - 1) .. "\\" .. t .. sub(n, e + 1)
      e += #t
    end
    e += 1
  end
  return '"' .. n .. '"'
end

function n2(n)
  if type(n) ~= "string" then
    return false
  end
  if L[n] then
    return false
  end
  if #n == 0 or y(b(n, 1)) then
    return false
  end
  for e = 1, #n do
    if not D(b(n, e)) then
      return false
    end
  end
  return true
end

function f(e, t)
  local n = type(e)
  if n == "nil" then
    return "nil"
  elseif n == "boolean" then
    return e and "true" or "false"
  elseif n == "number" then
    return tostr(e, T)
  elseif n == "string" then
    return n0(e)
  elseif n == "table" and not t then
    local n, t, r = "{", 0, 0
    for e, l in next, e do
      if t == S then
        n = n .. ",<...>"
        break
      end
      if t > 0 then
        n = n .. ","
      end
      local l = f(l, 1)
      if e == r + 1 then
        n = n .. l
        r = e
      elseif n2(e) then
        n = n .. e .. "=" .. l
      else
        n = n .. "[" .. f(e, 1) .. "]=" .. l
      end
      t += 1
    end
    return n .. "}"
  else
    return "<" .. tostr(n) .. ">"
  end
end

function nb(n, e)
  if e == nil then
    return n
  end
  if not n then
    n = ""
  end
  local t = min(21, #e)
  for t = 1, t do
    if #n > 0 then
      n ..= "\n"
    end
    local t = e[t]
    if type(t) == "table" then
      local e = ""
      for n = 1, t.n do
        if #e > 0 then
          e = e .. ", "
        end
        e = e .. f(t[n])
      end
      n ..= e
    else
      n ..= t
    end
  end
  local l = {}
  for n = t + 1, #e do
    l[n - t] = e[n]
  end
  return n, l
end

poke(24365, 1)
cls()
h = "> "
a, x, _ = "", 1, 0
c, A = 1, 20
w, z = {""}, 1
X = false
m, u = 0, 1
M, N = true, true
s = {7, 4, 3, 5, 6, 8, 5, 12, 14, 7, 11, 5}
e.print = function(n, ...)
  if pack(...).n ~= 0 or not M then
    return print(n, ...)
  end
  add(G, tostr(n))
end

function nf()
  poke(24368, 1)
end

function nd()
  return function()
    if stat(30) then
      return stat(31)
    end
  end
end

function U(l, r)
  local e, n, t = 1, 0, 0
  if not l then
    return e, n, t
  end
  while e <= #l do
    local l = b(l, e)
    local o = l >= "█"
    if n >= (o and 31 or 32) then
      t += 1
      n = 0
    end
    if r then
      r(e, l, n, t)
    end
    if l == "\n" then
      t += 1
      n = 0
    else
      n += o and 2 or 1
    end
    e += 1
  end
  return e, n, t
end

function C(t, l)
  local n, e = 0, 0
  local o, r, t = U(t, function(t, i, r, o)
    if l == t then
      n, e = r, o
    end
  end)
  if l >= o then
    n, e = r, t
  end
  if r > 0 then
    t += 1
  end
  return n, e, t
end

function E(l, r, e)
  local t, n = 1, false
  local r, o, l = U(l, function(o, f, i, l)
    if e == l and r == i and not n then
      t = o
      n = true
    end
    if (e < l or e == l and r < i) and not n then
      t = o - 1
      n = true
    end
  end)
  if not n then
    t = e >= l and r or r - 1
  end
  if o > 0 then
    l += 1
  end
  return t, l
end

function V(n, t, l, e)
  if type(e) == "function" then
    U(n, function(n, r, o, i)
      print(r, t + o * 4, l + i * 6, e(n))
    end)
  else
    print(n and "⁶rw" .. n, t, l, e)
  end
end

function np(n, r, o)
  local i, e, f, t = nl(n)
  local e = 1
  V(n, r, o, function(r)
    while e <= #t and t[e] < r do
      e += 1
    end
    local n
    if e <= #t and f[e] <= r then
      n = i[e]
    end
    local e = s[5]
    if n == false then
      e = s[6]
    elseif n == true then
      e = s[7]
    elseif type(n) ~= "string" or q(n, {"nil", "true", "false"}) then
      e = s[8]
    elseif L[n] then
      e = s[9]
    elseif not D(b(n, 1)) then
      e = s[10]
    elseif l[n] then
      e = s[11]
    end
    return e
  end)
end

function _draw()
  local r, o, i = peek(24357), peek2(24360), peek2(24362)
  camera()

  local function n(n)
    cursor(0, 127)
    for n = 1, n do
      rectfill(0, u * 6, 127, (u + 1) * 6 - 1, 0)
      if u < 21 then
        u += 1
      else
        print ""
      end
    end
  end

  local function f(n, e)
    for n = 1, n do
      if u > e then
        u -= 1
      end
      rectfill(0, u * 6, 127, (u + 1) * 6 - 1, 0)
    end
  end

  local function d(n, e)
    for t = 0, 2 do
      local l = pget(n + t, e + 5)
      pset(n + t, e + 5, l == 0 and s[12] or 0)
    end
  end

  local function l(r)
    local l = h .. a .. " "
    local o, t, e = C(l, #h + c)
    if e > x then
      n(e - x)
    elseif e < x then
      f(x - e, e)
    end
    x = e
    _ = mid(_, 0, max(x - 21, 0))
    ::n::
    local n = u - x + _
    if n + t < 0 then
      _ += 1
      goto n
    end
    if n + t >= 21 then
      _ -= 1
      goto n
    end
    local n = n * 6
    rectfill(0, n, 127, n + x * 6 - 1, 0)
    if x > 21 then
      rectfill(0, 126, 127, 127, 0)
    end
    np(l, 0, n)
    print(h, 0, n, s[4])
    if A >= 10 and r ~= false and not v then
      d(o * 4, n + t * 6)
    end
  end

  local function f(e)
    n(1)
    u -= 1
    print("[enter] ('esc' to abort)", 0, u * 6, s[3])
    while true do
      flip()
      nf()
      for n in nd() do
        if n == "•" then
          X = true
          g = ""
          G = {}
          return false
        end
        if n == "\r" or n == "\n" then
          m += e
          return true
        end
      end
    end
  end

  ::n::
  local t, e
  if G or g then
    t, e = E(g, 0, m)
    if e - m <= 20 and G then
      g, G = nb(g, G)
      t, e = E(g, 0, m)
      if #G == 0 and not v then
        G = nil
      end
    end
  end
  if not v then
    camera()
  end
  if m == 0 and not v then
    l(not g)
  end
  if g then
    local r, t = sub(g, t), min(e - m, 20)
    n(t)
    V(r, 0, (u - t) * 6, s[1])
    if t < e - m then
      if f(t) then
        goto n
      end
    else
      local r, o, e = C(O, 0)
      n(e)
      V(O, 0, (u - e) * 6, s[2])
      if v then
        m += t
      else
        a, x, _, c, m, g, O = "", 0, 0, 1, 0
        l()
      end
    end
  end
  if v then
    n(1)
    u -= 1
    print(v, 0, u * 6, s[3])
  end
  if B then
    n(1)
    u -= 1
    print(B, 0, u * 6, s[3])
    B = nil
  end
  if P then
    P -= 1
    if P == 0 then
      B, P = ""
    end
  end
  A -= 1
  if A == 0 then
    A = 20
  end
  color(r)
  camera(o, i)
  if u <= 20 then
    cursor(0, u * 6)
  end
end

r, d, F = false, false, false
j = {}

function nr(n, e)
  i, nw = n, e
  assert(false, n)
end

function W(n, t, l)
  return ni(n, l)(t or e)
end

function Y(n, e)
  return W("return " .. n, e, true)
end

function nx(n)
  local e = cocreate(ni)
  ::n::
  local n, e = coresume(e, n)
  if n and not e then
    goto n
  end
  if not n then
    e, i = i, false
  end
  return n, e
end

function n3(n, e)
  local n, e = C(n, e)
  return "line " .. e + 1 .. " col " .. n + 1
end

function nu(e, l)
  G, X, i = {}, false, false
  r, d, F = false, false, false
  local t, r, n = cocreate(function()
    W(e)
  end)
  while true do
    r, n = coresume(t)
    if costatus(t) == "dead" then
      break
    end
    if M and not d then
      v = "running, press 'esc' to abort"
      _draw()
      flip()
      v = nil
    else
      if N and not d and not F then
        flip()
      end
      if not N and holdframe then
        holdframe()
      end
      F = false
    end
    for n in nd() do
      if n == "•" then
        X = true
      else
        add(j, n)
      end
    end
    if X then
      n = "computation aborted"
      break
    end
  end
  if i == nil then
    if l then
      n = "unexpected end of code"
    else
      n, G = nil
    end
  end
  if i then
    n, i = i .. "\nat " .. n3(e, nw)
  end
  O = n
  j = {}
end

I = function()
  r = true
  yield()
  r = false
end
e.flip = function(...)
  local n = pack(flip(...))
  F = true
  I()
  return H(n)
end
e.coresume = function(n, ...)
  local e = pack(coresume(n, ...))
  while r do
    yield()
    e = pack(coresume(n))
  end
  i = false
  return H(e)
end
e.stat = function(n, ...)
  if n == 30 then
    return #j > 0 or stat(n, ...)
  elseif n == 31 then
    if #j > 0 then
      return deli(j, 1)
    else
      local n = stat(n, ...)
      if n == "•" then
        X = true
      end
      return n
    end
  else
    return stat(n, ...)
  end
end

function nm(n)
  if _set_fps then
    _set_fps(n._update60 and 60 or 30)
  end
  if n._init then
    n._init()
  end
  d = true
  while true do
    if _update_buttons then
      _update_buttons()
    end
    if holdframe then
      holdframe()
    end
    if n._update60 then
      n._update60()
    elseif n._update then
      n._update()
    end
    if n._draw then
      n._draw()
    end
    flip()
    F = true
    I()
  end
  d = false
end

function ns(n)
  if q(n, {"i", "interrupt"}) then
    return M
  elseif q(n, {"f", "flip"}) then
    return N
  elseif q(n, {"r", "repl"}) then
    return J
  elseif q(n, {"mi", "max_items"}) then
    return S
  elseif q(n, {"h", "hex"}) then
    return T
  elseif q(n, {"cl", "colors"}) then
    return s
  elseif q(n, {"c", "code"}) then
    local n = {[0] = a}
    for e = 1, #w - 1 do
      n[e] = w[#w - e]
    end
    return n
  elseif q(n, {"cm", "compile"}) then
    return function(n)
      return nx(n)
    end
  elseif q(n, {"x", "exec"}) then
    return function(n, e)
      W(n, e)
    end
  elseif q(n, {"v", "eval"}) then
    return function(n, e)
      return Y(n, e)
    end
  elseif q(n, {"p", "print"}) then
    return function(n, ...)
      e.print(f(n), ...)
    end
  elseif q(n, {"ts", "tostr"}) then
    return function(n)
      return f(n)
    end
  elseif q(n, {"rst", "reset"}) then
    run()
  elseif q(n, {"run"}) then
    nm(e)
  else
    assert(false, "unknown \\-command")
  end
end

function nh(e)
  local function t(n)
    return n and n ~= 0 and true or false
  end

  local n
  if q(e, {"i", "interrupt"}) then
    n = function(n)
      M = t(n)
    end
  elseif q(e, {"f", "flip"}) then
    n = function(n)
      N = t(n)
    end
  elseif q(e, {"r", "repl"}) then
    n = function(n)
      J = t(n)
    end
  elseif q(e, {"mi", "max_items"}) then
    n = function(n)
      S = tonum(n) or -1
    end
  elseif q(e, {"h", "hex"}) then
    n = function(n)
      T = t(n)
    end
  elseif q(e, {"cl", "colors"}) then
    n = function(n)
      s = n
    end
  else
    assert(false, "unknown \\-command assign")
  end
  local n = {__newindex = function(t, l, e)
    n(e)
  end}
  return setmetatable(n, n), 0
end

Q = stat(4)
K, R = 0, false
poke(24412, 10, 2)

function k(n)
  if stat(28, n) then
    if n ~= nn then
      nn, K = n, 0
    end
    return K == 0 or K >= 10 and K % 2 == 0
  elseif nn == n then
    nn = nil
  end
end

function _update()
  local e = false

  local function t(t)
    local e, n, l = C(h .. a, #h + c)
    if ne then
      e = ne
    end
    n += t
    if not (n >= 0 and n < l) then
      return false
    end
    c = max(E(h .. a, e, n) - #h, 1)
    ne = e
    A = 20
    return true
  end

  local function o(t)
    local n, l = C(h .. a, #h + c)
    n = t > 0 and 100 or 0
    c = max(E(h .. a, n, l) - #h, 1)
    e = true
  end

  local function f(n)
    w[z] = a
    z += n
    a = w[z]
    if n < 0 then
      c = #a + 1
    else
      c = max(E(h .. a, 32, 0) - #h, 1)
      local n = b(a, c)
      if n ~= "" and n ~= "\n" then
        c -= 1
      end
    end
    e = true
  end

  local function i()
    if #a > 0 then
      if #w > 50 then
        del(w, w[1])
      end
      w[#w] = a
      add(w, "")
      z = #w
      e = true
    end
  end

  local function d(n)
    if c + n > 0 then
      a = sub(a, 1, c + n - 1) .. sub(a, c + n + 1)
      c += n
      e = true
    end
  end

  local function l(n)
    a = sub(a, 1, c - 1) .. n .. sub(a, c)
    c += #n
    e = true
  end

  local r, u, n = stat(28, 224) or stat(28, 228), stat(28, 225) or stat(28, 229), -1
  if k(80) then
    if c > 1 then
      c -= 1
      e = true
    end
  elseif k(79) then
    if c <= #a then
      c += 1
      e = true
    end
  elseif k(82) then
    if (r or not t(-1)) and z > 1 then
      f(-1)
    end
  elseif k(81) then
    if (r or not t(1)) and z < #w then
      f(1)
    end
  else
    local t = stat(31)
    n = ord(t)
    if t == "•" then
      if #a == 0 then
        extcmd "pause"
      else
        G, O = {}
        i()
      end
    elseif t == "\r" or t == "\n" then
      if u then
        l "\n"
      else
        nu(a)
        if not G then
          l "\n"
        else
          i()
        end
      end
    elseif r and k(40) then
      nu(a, true)
      i()
    elseif t ~= "" and n >= 32 and n < 154 then
      if R and n >= 128 then
        t = chr(n - 63)
      end
      l(t)
    elseif n == 193 then
      l "\n"
    elseif n == 192 then
      o(-1)
    elseif n == 196 then
      o(1)
    elseif n == 203 then
      R = not R
      B, P = "shift now selects " .. (R and "punycase" or "symbols"), 40
    elseif k(74) then
      if r then
        c = 1
        e = true
      else
        o(-1)
      end
    elseif k(77) then
      if r then
        c = #a + 1
        e = true
      else
        o(1)
      end
    elseif k(42) then
      d(-1)
    elseif k(76) then
      d(0)
    end
  end
  local t = stat(4)
  if t ~= Q or n == 213 then
    l(t)
    Q = t
  end
  if n == 194 or n == 215 then
    if a ~= "" and a ~= Q then
      Q = a
      printh(a, "@clip")
      if n == 215 then
        a = ""
        c = 1
      end
      B = "press again to put in clipboard"
    else
      B = ""
    end
  end
  if stat(120) then
    local n
    repeat
      n = serial(2048, 24448, 128)
      l(chr(peek(24448, n)))
    until n == 0
  end
  if e then
    A, ne = 20
  end
  K += 1
  nf()
end

function na(n, e)
  local e, t = coresume(cocreate(e))
  if not e then
    printh("error #" .. n .. ": " .. t)
    print("error #" .. n .. "\npico8 broke something again,\nthis cart may not work.\npress any button to ignore")
    while btnp() == 0 do
      flip()
    end
    cls()
  end
end

na(1, function()
  assert(pack(Y "(function (...) return ... end)(1,2,nil,nil)").n == 4)
end)
na(2, function()
  assert(Y "function() local temp, temp2 = {max(1,3)}, -20;return temp[1] + temp2; end" () == -17)
end)
printh "finished"
stop()
while true do
  if holdframe then
    holdframe()
  end
  _update()
  _draw()
  flip()
end

__meta:title__
keep:------------------------------------
keep: Please see 'Commented Source Code' section in the BBS
