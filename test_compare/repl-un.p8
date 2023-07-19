pico-8 cartridge // http://www.pico-8.com
version 41
__lua__

--------------------------------------
-- Please see 'Commented Source Code' section in the BBS
-- for the original commented source code
-- (The below had the comments stripped due to cart size limits)
--------------------------------------
local t, nx, n3 = _ENV, {}, {}
for n, e in pairs(_ENV) do
  nx[n] = e
  if type(e) == "function" then
    n3[n] = true
  end
end
local _ENV = nx
z, W = true

function f(t, e)
  for n = 1, #e do
    if sub(e, n, n) == t then
      return n
    end
  end
end

function e(e, n)
  return sub(e, n, n)
end

local nm, n7, nx = split "a,b,f,n,r,t,v,\\,\",',\n,*,#,-,|,+,^", split "⁷,⁸,ᶜ,\n,\r,	,ᵇ,\\,\",',\n,¹,²,³,⁴,⁵,⁶", {}
for n = 1, #nm do
  nx[nm[n]] = n7[n]
end

function g(n)
  return n >= "0" and n <= "9"
end

function B(n)
  return n >= "A" and n <= "Z" or n >= "a" and n <= "z" or n == "_" or n >= "█" or g(n)
end

function nd(r, n, i, o)
  local t = ""
  while n <= #r do
    local l = e(r, n)
    if l == i then
      break
    end
    if l == "\\" then
      n += 1
      local t = e(r, n)
      l = nx[t]
      if t == "x" then
        t = tonum("0x" .. sub(r, n + 1, n + 2))
        if t then
          n += 2
        else
          o "bad hex escape"
        end
        l = chr(t)
      elseif g(t) then
        local i = n
        while g(t) and n < i + 3 do
          n += 1
          t = e(r, n)
        end
        n -= 1
        t = tonum(sub(r, i, n))
        if not t or t >= 256 then
          o "bad decimal escape"
        end
        l = chr(t)
      elseif t == "z" then
        repeat
          n += 1
          t = e(r, n)
        until not f(t, " \r	ᶜᵇ\n")
        if t == "" then
          o()
        end
        l = ""
        n -= 1
      elseif t == "" then
        o()
        l = ""
      end
      if not l then
        o("bad escape: " .. t)
        l = ""
      end
    elseif l == "\n" then
      o "unterminated string"
      break
    end
    t ..= l
    n += 1
  end
  if n > #r then
    o("unterminated string", true)
  end
  return t, n + 1
end

function Y(t, n, l, r)
  if e(t, n) == "[" then
    n += 1
    local r = n
    while e(t, n) == "=" do
      n += 1
    end
    local r = "]" .. sub(t, r, n - 1) .. "]"
    local o = #r
    if e(t, n) == "[" then
      n += 1
      if e(t, n) == "\n" then
        n += 1
      end
      local e = n
      while n <= #t and sub(t, n, n + o - 1) ~= r do
        n += 1
      end
      if n >= #t then
        l()
      end
      return sub(t, e, n - 1), n + o
    end
  end
  if r then
    l "invalid long brackets"
  end
  return nil, n
end

function nn(l, c)
  local n, s, o, h, b, p, u, i = 1, 1, {}, {}, {}, {}

  local function d(n, e)
    if c then
      ne(n, i)
    end
    u = n and not e
  end

  while n <= #l do
    i = n
    local t, a, r = e(l, n)
    if f(t, " \r	ᶜᵇ\n") then
      n += 1
      a = true
      if t == "\n" then
        s += 1
      end
    elseif t == "-" and e(l, n + 1) == "-" then
      n += 2
      if e(l, n) == "[" then
        r, n = Y(l, n, d)
      end
      if not r then
        while n <= #l and e(l, n) ~= "\n" do
          n += 1
        end
      end
      if c then
        a = true
      else
        add(o, true)
      end
    elseif g(t) or t == "." and g(e(l, n + 1)) then
      local u, a = "0123456789", true
      if t == "0" and f(e(l, n + 1), "xX") then
        u ..= "AaBbCcDdEeFf"
        n += 2
      elseif t == "0" and f(e(l, n + 1), "bB") then
        u = "01"
        n += 2
      end
      while true do
        t = e(l, n)
        if t == "." and a then
          a = false
        elseif not f(t, u) then
          break
        end
        n += 1
      end
      r = sub(l, i, n - 1)
      if not tonum(r) then
        d "bad number"
        r = "0"
      end
      add(o, tonum(r))
    elseif B(t) then
      while B(e(l, n)) do
        n += 1
      end
      add(o, sub(l, i, n - 1))
    elseif t == "'" or t == '"' then
      r, n = nd(l, n + 1, t, d)
      add(o, {t = r})
    elseif t == "[" and f(e(l, n + 1), "=[") then
      r, n = Y(l, n, d, true)
      add(o, {t = r})
    else
      n += 1
      local e, r, u = unpack(split(sub(l, n, n + 2), ""))
      if e == t and r == t and f(t, ".>") then
        n += 2
        if u == "=" and f(t, ">") then
          n += 1
        end
      elseif e == t and r ~= t and f(t, "<>") and f(r, "<>") then
        n += 2
        if u == "=" then
          n += 1
        end
      elseif e == t and f(t, ".:^<>") then
        n += 1
        if r == "=" and f(t, ".^<>") then
          n += 1
        end
      elseif e == "=" and f(t, "+-*/\\%^&|<>=~!") then
        n += 1
      elseif f(t, "+-*/\\%^&|<>=~#(){}[];,?@$.:") then
      else
        d("bad char: " .. t)
      end
      add(o, sub(l, i, n - 1))
    end
    if not a then
      add(h, s)
      add(b, i)
      add(p, n - 1)
    end
    if u then
      o[#o], u = false, false
    end
  end
  return o, h, b, p
end

function r(t, n)
  for e = 1, #n do
    if n[e] == t then
      return e
    end
  end
end

function c(n)
  return unpack(n, 1, n.n)
end

function nu(e)
  local n = {}
  for e, t in next, e do
    n[e] = t
  end
  return n
end

local Y = split "and,break,do,else,elseif,end,false,for,function,goto,if,in,local,nil,not,or,repeat,return,then,true,until,while"
G = {}
for n in all(Y) do
  G[n] = true
end

local function Y(n)
  return type(n) == "string" and e(n, #n) == "="
end

nt = split "end,else,elseif,until"

function nl(n, j)
  local o, F, l = nn(n, true)
  local n, f, s, v, d, p, x, t, b, y, h, Z = 1, 0, 0, {}

  local function i(e)
    ne(e, l[n - 1] or 1)
  end

  local function g(n)
    return function()
      return n
    end
  end

  local function C(e)
    local n = d[e]
    if n then
      return function(t)
        return t[n][e]
      end
    else
      n = d._ENV
      return function(t)
        return t[n]._ENV[e]
      end
    end
  end

  local function q()
    local n = d["..."]
    if not n or n ~= Z then
      i "unexpected '...'"
    end
    return function(e)
      return c(e[n]["..."])
    end
  end

  local function D(e)
    local n = d[e]
    if n then
      return function(t)
        return t[n], e
      end
    else
      n = d._ENV
      return function(t)
        return t[n]._ENV, e
      end
    end
  end

  local function l(e)
    local t = o[n]
    n += 1
    if t == e then
      return
    end
    if t == nil then
      i()
    end
    i("expected: " .. e)
  end

  local function u(t)
    if not t then
      t = o[n]
      n += 1
    end
    if t == nil then
      i()
    end
    if type(t) == "string" and B(e(t, 1)) and not G[t] then
      return t
    end
    if type(t) == "string" then
      i("invalid identifier: " .. t)
    end
    i "identifier expected"
  end

  local function e(e)
    if o[n] == e then
      n += 1
      return true
    end
  end

  local function A()
    d = setmetatable({}, {__index = d})
    f += 1
  end

  local function B()
    d = getmetatable(d).__index
    f -= 1
  end

  local function m(l, t)
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

  local function k(t)
    local n = {}
    add(n, (t()))
    while e "," do
      add(n, (t()))
    end
    return n
  end

  local function X(r, o, i)
    local n = {}
    if i then
      add(n, i)
    elseif not e ")" then
      while true do
        add(n, (t()))
        if e ")" then
          break
        end
        l ","
      end
    end
    if o then
      return function(e)
        local t = r(e)
        return t[o](t, c(m(e, n)))
      end, true, nil, function(e)
        local t = r(e)
        return t[o], pack(t, c(m(e, n)))
      end
    else
      return function(e)
        return r(e)(c(m(e, n)))
      end, true, nil, function(e)
        return r(e), m(e, n)
      end
    end
  end

  local function G()
    local r, d, c, a = {}, {}, 1
    while not e "}" do
      a = nil
      local i, f
      if e "[" then
        i = t()
        l "]"
        l "="
        f = t()
      elseif o[n + 1] == "=" then
        i = g(u())
        l "="
        f = t()
      else
        i = g(c)
        f = t()
        c += 1
        a = #r + 1
      end
      add(r, i)
      add(d, f)
      if e "}" then
        break
      end
      if not e ";" then
        l ","
      end
    end
    return function(e)
      local t = {}
      for n = 1, #r do
        if n == a then
          local l, n = r[n](e), pack(d[n](e))
          for e = 1, n.n do
            t[l + e - 1] = n[e]
          end
        else
          t[r[n](e)] = d[n](e)
        end
      end
      return t
    end
  end

  local function E(o, a)
    local n, p, t
    if o then
      if a then
        A()
        n = u()
        d[n] = f
        t = D(n)
      else
        n = {u()}
        while e "." do
          add(n, u())
        end
        if e ":" then
          add(n, u())
          p = true
        end
        if #n == 1 then
          t = D(n[1])
        else
          local e = C(n[1])
          for t = 2, #n - 1 do
            local l = e
            e = function(e)
              return l(e)[n[t]]
            end
          end
          t = function(t)
            return e(t), n[#n]
          end
        end
      end
    end
    local n, r = {}
    if p then
      add(n, "self")
    end
    l "("
    if not e ")" then
      while true do
        if e "..." then
          r = true
        else
          add(n, u())
        end
        if e ")" then
          break
        end
        l ","
        if r then
          i "unexpected param after '...'"
        end
      end
    end
    A()
    for n in all(n) do
      d[n] = f
    end
    if r then
      d["..."] = f
    end
    local e, i, d = v, h, Z
    v, h, Z = {}, s + 1, f
    local f = b()
    for n in all(v) do
      n()
    end
    v, h, Z = e, i, d
    l "end"
    B()
    return function(e)
      if a then
        add(e, {})
      end
      local l = nu(e)
      local i = #l
      local n = function(...)
        local t, e = pack(...), l
        if #e ~= i then
          local n = {}
          for t = 0, i do
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
        local n = f(e)
        deli(e)
        if n then
          if type(n) == "table" then
            return c(n)
          end
          return n()
        end
      end
      if o then
        local e, t = t(e)
        e[t] = n
      else
        return n
      end
    end
  end

  local function Z()
    local e = o[n]
    n += 1
    local n
    if e == nil then
      i()
    end
    if e == "nil" then
      return g()
    end
    if e == "true" then
      return g(true)
    end
    if e == "false" then
      return g(false)
    end
    if type(e) == "number" then
      return g(e)
    end
    if type(e) == "table" then
      return g(e.t)
    end
    if e == "{" then
      return G()
    end
    if e == "(" then
      n = t()
      l ")"
      return function(e)
        return (n(e))
      end, true
    end
    if e == "-" then
      n = t(11)
      return function(e)
        return -n(e)
      end
    end
    if e == "~" then
      n = t(11)
      return function(e)
        return ~n(e)
      end
    end
    if e == "not" then
      n = t(11)
      return function(e)
        return not n(e)
      end
    end
    if e == "#" then
      n = t(11)
      return function(e)
        return #n(e)
      end
    end
    if e == "@" then
      n = t(11)
      return function(e)
        return @n(e)
      end
    end
    if e == "%" then
      n = t(11)
      return function(e)
        return %n(e)
      end
    end
    if e == "$" then
      n = t(11)
      return function(e)
        return $n(e)
      end
    end
    if e == "function" then
      return E()
    end
    if e == "..." then
      return q()
    end
    if e == "\\" then
      n = u()
      return function()
        return na(n)
      end, true, function()
        return nc(n)
      end
    end
    if u(e) then
      return C(e), true, D(e)
    end
    i("unexpected token: " .. e)
  end

  local function D(e, t, l, r)
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

  local function q(d, e, a)
    local i = o[n]
    n += 1
    local r, f
    if a then
      if i == "." then
        r = u()
        return function(n)
          return e(n)[r]
        end, true, function(n)
          return e(n), r
        end
      end
      if i == "[" then
        r = t()
        l "]"
        return function(n)
          return e(n)[r(n)]
        end, true, function(n)
          return e(n), r(n)
        end
      end
      if i == "(" then
        return X(e)
      end
      if i == "{" or type(i) == "table" then
        n -= 1
        f = Z()
        return X(e, nil, f)
      end
      if i == ":" then
        r = u()
        if o[n] == "{" or type(o[n]) == "table" then
          f = Z()
          return X(e, r, f)
        end
        l "("
        return X(e, r)
      end
    end
    local e = D(i, d, e, t)
    if not e then
      n -= 1
    end
    return e
  end

  t = function(r)
    local n, e, t, l = Z()
    while true do
      local r, o, i, f = q(r or 0, n, e)
      if not r then
        break
      end
      n, e, t, l = r, o, i, f
    end
    return n, t, l
  end

  local function Z()
    local e, n = t()
    if not n then
      i "cannot assign to value"
    end
    return n
  end

  local function q()
    local n = k(Z)
    l "="
    local e = k(t)
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
        local e = m(t, e)
        for n = #n, 1, -1 do
          l[n][r[n]] = e[n]
        end
      end
    end
  end

  local function G(e, l)
    local r = o[n]
    n += 1
    local n = sub(r, 1, -2)
    local n = D(n, 0, e, function()
      return t()
    end)
    if not n then
      i "invalid compound assignment"
    end
    return function(e)
      local t, l = l(e)
      t[l] = n(e)
    end
  end

  local function H()
    if e "function" then
      return E(true, true)
    else
      local n, e = k(u), e "=" and k(t) or {}
      A()
      for e = 1, #n do
        d[n[e]] = f
      end
      if #n == 1 and #e == 1 then
        return function(t)
          add(t, {[n[1]] = e[1](t)})
        end
      else
        return function(t)
          local l, r = {}, m(t, e)
          for e = 1, #n do
            l[n[e]] = r[e]
          end
          add(t, l)
        end
      end
    end
  end

  local function D(e)
    local t = F[n - 1]
    x = function()
      return t ~= F[n]
    end
    if not e or x() then
      i(n <= #o and "bad shorthand" or nil)
    end
  end

  local function F()
    local r, o, t, n = o[n] == "(", t()
    if e "then" then
      t, n = b()
      if e "else" then
        n = b()
        l "end"
      elseif e "elseif" then
        n = F()
      else
        l "end"
      end
    else
      D(r)
      t = b()
      if not x() and e "else" then
        n = b()
      end
      x = nil
    end
    return function(e)
      if o(e) then
        return t(e)
      elseif n then
        return n(e)
      end
    end
  end

  local function Z(...)
    local n = y
    y = s + 1
    local e = b(...)
    y = n
    return e
  end

  local function X(n, e)
    if n == true then
      return
    end
    return n, e
  end

  local function I()
    local r, t, n = o[n] == "(", t()
    if e "do" then
      n = Z()
      l "end"
    else
      D(r)
      n = Z()
      x = nil
    end
    return function(e)
      while t(e) do
        if stat(1) >= 1 then
          w()
        end
        local n, e = n(e)
        if n then
          return X(n, e)
        end
      end
    end
  end

  local function D()
    local r, e = f, Z(true)
    l "until"
    local l = t()
    while f > r do
      B()
    end
    return function(n)
      repeat
        if stat(1) >= 1 then
          w()
        end
        local e, t = e(n)
        if not e then
          t = l(n)
        end
        while #n > r do
          deli(n)
        end
        if e then
          return X(e, t)
        end
      until t
    end
  end

  local function J()
    if o[n + 1] == "=" then
      local r = u()
      l "="
      local o = t()
      l ","
      local i, e = t(), e "," and t() or g(1)
      l "do"
      A()
      d[r] = f
      local t = Z()
      l "end"
      B()
      return function(n)
        for e = o(n), i(n), e(n) do
          if stat(1) >= 1 then
            w()
          end
          add(n, {[r] = e})
          local e, t = t(n)
          deli(n)
          if e then
            return X(e, t)
          end
        end
      end
    else
      local r = k(u)
      l "in"
      local e = k(t)
      l "do"
      A()
      for n in all(r) do
        d[n] = f
      end
      local o = Z()
      l "end"
      B()
      return function(n)
        local e = m(n, e)
        while true do
          local l, t = {}, {e[1](e[2], e[3])}
          if t[1] == nil then
            break
          end
          e[3] = t[1]
          for n = 1, #r do
            l[r[n]] = t[n]
          end
          if stat(1) >= 1 then
            w()
          end
          add(n, l)
          local e, t = o(n)
          deli(n)
          if e then
            return X(e, t)
          end
        end
      end
    end
  end

  local function g()
    if not y or h and y < h then
      i "break outside of loop"
    end
    return function()
      return true
    end
  end

  local function y()
    if not h and not j then
      i "return outside of function"
    end
    if o[n] == ";" or r(o[n], nt) or x and x() then
      return function()
        return pack()
      end
    else
      local n, r, l = t()
      local n = {n}
      while e "," do
        add(n, (t()))
      end
      if #n == 1 and l and h then
        return function(n)
          local n, e = l(n)
          if stat(1) >= 1 then
            w()
          end
          return function()
            return n(c(e))
          end
        end
      else
        return function(e)
          return m(e, n)
        end
      end
    end
  end

  local function A(e)
    local n = u()
    l "::"
    if p[n] and p[n].e == s then
      i "label already defined"
    end
    p[n] = {l = f, e = s, o = e, r = #e}
  end

  local function Z()
    local t, e, l, n = u(), p, f
    add(v, function()
      n = e[t]
      if not n then
        i "label not found"
      end
      if h and n.e < h then
        i "goto outside of function"
      end
      local e = e[n.e] or l
      if n.l > e and n.r < #n.o then
        i "goto past local"
      end
    end)
    return function()
      if stat(1) >= 1 then
        w()
      end
      return 0, n
    end
  end

  local function u(f)
    local r = o[n]
    n += 1
    if r == ";" then
      return
    end
    if r == "do" then
      local n = b()
      l "end"
      return n
    end
    if r == "if" then
      return F()
    end
    if r == "while" then
      return I()
    end
    if r == "repeat" then
      return D()
    end
    if r == "for" then
      return J()
    end
    if r == "break" then
      return g()
    end
    if r == "return" then
      return y(), true
    end
    if r == "local" then
      return H()
    end
    if r == "goto" then
      return Z()
    end
    if r == "::" then
      return A(f)
    end
    if r == "function" and o[n] ~= "(" then
      return E(true)
    end
    if r == "?" then
      local e, t = C "print", k(t)
      return function(n)
        e(n)(c(m(n, t)))
      end
    end
    n -= 1
    local r, t, f, l = n, t()
    if e "," or e "=" then
      n = r
      return q()
    elseif Y(o[n]) then
      return G(t, f)
    elseif s <= 1 and z then
      return function(n)
        local n = pack(t(n))
        if not (l and n.n == 0) then
          add(a, n)
        end
        W = n[1]
      end
    else
      if not l then
        i "statement has no effect"
      end
      return function(n)
        t(n)
      end
    end
  end

  b = function(t)
    p = setmetatable({}, {__index = p})
    p[s] = f
    s += 1
    local d, i, l = s, t and 32767 or f, {}
    while n <= #o and not r(o[n], nt) and not (x and x()) do
      local n, t = u(l)
      if n then
        add(l, n)
      end
      if t then
        e ";"
        break
      end
    end
    while f > i do
      B()
    end
    s -= 1
    p = getmetatable(p).__index
    return function(e)
      local r, o, t, n = 1, #l
      while r <= o do
        t, n = l[r](e)
        if t then
          if type(t) ~= "number" then
            break
          end
          if n.e ~= d then
            break
          end
          r = n.r
          while #e > n.l do
            deli(e)
          end
          t, n = nil
        end
        r += 1
      end
      while #e > i do
        deli(e)
      end
      return t, n
    end
  end
  d = z and {_ENV = 0, _env = 0, _ = 0} or {_ENV = 0}
  local e = b()
  if n <= #o then
    i "unexpected end"
  end
  for n in all(v) do
    n()
  end
  return function(n)
    local n = z and {_ENV = n, _env = n, _ = W} or {_ENV = n}
    local n = e {[0] = n}
    if n then
      return c(n)
    end
  end
end

O, P = 10, false
local W = {["\0"] = "000", ["ᵉ"] = "014", ["ᶠ"] = "015"}
for n, e in pairs(nx) do
  if not f(n, "'\n") then
    W[e] = n
  end
end

function n1(n)
  local t = 1
  while t <= #n do
    local e = e(n, t)
    local e = W[e]
    if e then
      n = sub(n, 1, t - 1) .. "\\" .. e .. sub(n, t + 1)
      t += #e
    end
    t += 1
  end
  return '"' .. n .. '"'
end

function ns(n)
  if type(n) ~= "string" then
    return false
  end
  if G[n] then
    return false
  end
  if #n == 0 or g(e(n, 1)) then
    return false
  end
  for t = 1, #n do
    if not B(e(n, t)) then
      return false
    end
  end
  return true
end

function Z(e, t)
  local n = type(e)
  if n == "nil" then
    return "nil"
  elseif n == "boolean" then
    return e and "true" or "false"
  elseif n == "number" then
    return tostr(e, P)
  elseif n == "string" then
    return n1(e)
  elseif n == "table" and not t then
    local n, t, r = "{", 0, 0
    for e, l in next, e do
      if t == O then
        n = n .. ",<...>"
        break
      end
      if t > 0 then
        n = n .. ","
      end
      local l = Z(l, 1)
      if e == r + 1 then
        n = n .. l
        r = e
      elseif ns(e) then
        n = n .. e .. "=" .. l
      else
        n = n .. "[" .. Z(e, 1) .. "]=" .. l
      end
      t += 1
    end
    return n .. "}"
  else
    return "<" .. tostr(n) .. ">"
  end
end

function nh(n, e)
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
        e = e .. Z(t[n])
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
d = "> "
n, s, k = "", 1, 0
l, v = 1, 20
u, y = {""}, 1
X = false
h, o = 0, 1
H, I = true, true
i = {7, 4, 3, 5, 6, 8, 5, 12, 14, 7, 11, 5}
t.print = function(n, ...)
  if pack(...).n ~= 0 or not H then
    return print(n, ...)
  end
  add(a, tostr(n))
end

function nr()
  poke(24368, 1)
end

function no()
  return function()
    if stat(30) then
      return stat(31)
    end
  end
end

function Q(r, o)
  local t, n, l = 1, 0, 0
  if not r then
    return t, n, l
  end
  while t <= #r do
    local e = e(r, t)
    local r = e >= "█"
    if n >= (r and 31 or 32) then
      l += 1
      n = 0
    end
    if o then
      o(t, e, n, l)
    end
    if e == "\n" then
      l += 1
      n = 0
    else
      n += r and 2 or 1
    end
    t += 1
  end
  return t, n, l
end

function C(t, l)
  local n, e = 0, 0
  local o, r, t = Q(t, function(t, i, r, o)
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

function D(l, r, e)
  local t, n = 1, false
  local r, o, l = Q(l, function(o, f, i, l)
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

function R(n, t, l, e)
  if type(e) == "function" then
    Q(n, function(n, r, o, i)
      print(r, t + o * 4, l + i * 6, e(n))
    end)
  else
    print(n and "⁶rw" .. n, t, l, e)
  end
end

function n0(n, o, f)
  local d, t, u, l = nn(n)
  local t = 1
  R(n, o, f, function(o)
    while t <= #l and l[t] < o do
      t += 1
    end
    local n
    if t <= #l and u[t] <= o then
      n = d[t]
    end
    local t = i[5]
    if n == false then
      t = i[6]
    elseif n == true then
      t = i[7]
    elseif type(n) ~= "string" or r(n, {"nil", "true", "false"}) then
      t = i[8]
    elseif G[n] then
      t = i[9]
    elseif not B(e(n, 1)) then
      t = i[10]
    elseif n3[n] then
      t = i[11]
    end
    return t
  end)
end

function _draw()
  local u, c, p = peek(24357), peek2(24360), peek2(24362)
  camera()

  local function e(n)
    cursor(0, 127)
    for n = 1, n do
      rectfill(0, o * 6, 127, (o + 1) * 6 - 1, 0)
      if o < 21 then
        o += 1
      else
        print ""
      end
    end
  end

  local function w(n, e)
    for n = 1, n do
      if o > e then
        o -= 1
      end
      rectfill(0, o * 6, 127, (o + 1) * 6 - 1, 0)
    end
  end

  local function m(n, e)
    for t = 0, 2 do
      local l = pget(n + t, e + 5)
      pset(n + t, e + 5, l == 0 and i[12] or 0)
    end
  end

  local function f(f)
    local r = d .. n .. " "
    local l, t, n = C(r, #d + l)
    if n > s then
      e(n - s)
    elseif n < s then
      w(s - n, n)
    end
    s = n
    k = mid(k, 0, max(s - 21, 0))
    ::n::
    local n = o - s + k
    if n + t < 0 then
      k += 1
      goto n
    end
    if n + t >= 21 then
      k -= 1
      goto n
    end
    local n = n * 6
    rectfill(0, n, 127, n + s * 6 - 1, 0)
    if s > 21 then
      rectfill(0, 126, 127, 127, 0)
    end
    n0(r, 0, n)
    print(d, 0, n, i[4])
    if v >= 10 and f ~= false and not x then
      m(l * 4, n + t * 6)
    end
  end

  local function d(t)
    e(1)
    o -= 1
    print("[enter] ('esc' to abort)", 0, o * 6, i[3])
    while true do
      flip()
      nr()
      for n in no() do
        if n == "•" then
          X = true
          b = ""
          a = {}
          return false
        end
        if n == "\r" or n == "\n" then
          h += t
          return true
        end
      end
    end
  end

  ::n::
  local r, t
  if a or b then
    r, t = D(b, 0, h)
    if t - h <= 20 and a then
      b, a = nh(b, a)
      r, t = D(b, 0, h)
      if #a == 0 and not x then
        a = nil
      end
    end
  end
  if not x then
    camera()
  end
  if h == 0 and not x then
    f(not b)
  end
  if b then
    local u, r = sub(b, r), min(t - h, 20)
    e(r)
    R(u, 0, (o - r) * 6, i[1])
    if r < t - h then
      if d(r) then
        goto n
      end
    else
      local d, u, t = C(J, 0)
      e(t)
      R(J, 0, (o - t) * 6, i[2])
      if x then
        h += r
      else
        n, s, k, l, h, b, J = "", 0, 0, 1, 0
        f()
      end
    end
  end
  if x then
    e(1)
    o -= 1
    print(x, 0, o * 6, i[3])
  end
  if A then
    e(1)
    o -= 1
    print(A, 0, o * 6, i[3])
    A = nil
  end
  if K then
    K -= 1
    if K == 0 then
      A, K = ""
    end
  end
  v -= 1
  if v == 0 then
    v = 20
  end
  color(u)
  camera(c, p)
  if o <= 20 then
    cursor(0, o * 6)
  end
end

L, E, F = false, false, false
j = {}

function ne(n, e)
  m, n2 = n, e
  assert(false, n)
end

function S(n, e, l)
  return nl(n, l)(e or t)
end

function T(n, e)
  return S("return " .. n, e, true)
end

function nb(n)
  local e = cocreate(nl)
  ::n::
  local n, e = coresume(e, n)
  if n and not e then
    goto n
  end
  if not n then
    e, m = m, false
  end
  return n, e
end

function np(n, e)
  local n, e = C(n, e)
  return "line " .. e + 1 .. " col " .. n + 1
end

function ni(e, l)
  a, X, m = {}, false, false
  L, E, F = false, false, false
  local t, r, n = cocreate(function()
    S(e)
  end)
  while true do
    r, n = coresume(t)
    if costatus(t) == "dead" then
      break
    end
    if H and not E then
      x = "running, press 'esc' to abort"
      _draw()
      flip()
      x = nil
    else
      if I and not E and not F then
        flip()
      end
      if not I and holdframe then
        holdframe()
      end
      F = false
    end
    for n in no() do
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
  if m == nil then
    if l then
      n = "unexpected end of code"
    else
      n, a = nil
    end
  end
  if m then
    n, m = m .. "\nat " .. np(e, n2)
  end
  J = n
  j = {}
end

w = function()
  L = true
  yield()
  L = false
end
t.flip = function(...)
  local n = pack(flip(...))
  F = true
  w()
  return c(n)
end
t.coresume = function(n, ...)
  local e = pack(coresume(n, ...))
  while L do
    yield()
    e = pack(coresume(n))
  end
  m = false
  return c(e)
end
t.stat = function(n, ...)
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

function nw(n)
  if _set_fps then
    _set_fps(n._update60 and 60 or 30)
  end
  if n._init then
    n._init()
  end
  E = true
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
    w()
  end
  E = false
end

function na(e)
  if r(e, {"i", "interrupt"}) then
    return H
  elseif r(e, {"f", "flip"}) then
    return I
  elseif r(e, {"r", "repl"}) then
    return z
  elseif r(e, {"mi", "max_items"}) then
    return O
  elseif r(e, {"h", "hex"}) then
    return P
  elseif r(e, {"cl", "colors"}) then
    return i
  elseif r(e, {"c", "code"}) then
    local n = {[0] = n}
    for e = 1, #u - 1 do
      n[e] = u[#u - e]
    end
    return n
  elseif r(e, {"cm", "compile"}) then
    return function(n)
      return nb(n)
    end
  elseif r(e, {"x", "exec"}) then
    return function(n, e)
      S(n, e)
    end
  elseif r(e, {"v", "eval"}) then
    return function(n, e)
      return T(n, e)
    end
  elseif r(e, {"p", "print"}) then
    return function(n, ...)
      t.print(Z(n), ...)
    end
  elseif r(e, {"ts", "tostr"}) then
    return function(n)
      return Z(n)
    end
  elseif r(e, {"rst", "reset"}) then
    run()
  elseif r(e, {"run"}) then
    nw(t)
  else
    assert(false, "unknown \\-command")
  end
end

function nc(e)
  local function t(n)
    return n and n ~= 0 and true or false
  end

  local n
  if r(e, {"i", "interrupt"}) then
    n = function(n)
      H = t(n)
    end
  elseif r(e, {"f", "flip"}) then
    n = function(n)
      I = t(n)
    end
  elseif r(e, {"r", "repl"}) then
    n = function(n)
      z = t(n)
    end
  elseif r(e, {"mi", "max_items"}) then
    n = function(n)
      O = tonum(n) or -1
    end
  elseif r(e, {"h", "hex"}) then
    n = function(n)
      P = t(n)
    end
  elseif r(e, {"cl", "colors"}) then
    n = function(n)
      i = n
    end
  else
    assert(false, "unknown \\-command assign")
  end
  local n = {__newindex = function(t, l, e)
    n(e)
  end}
  return setmetatable(n, n), 0
end

M = stat(4)
q, N = 0, false
poke(24412, 10, 2)

function p(n)
  if stat(28, n) then
    if n ~= U then
      U, q = n, 0
    end
    return q == 0 or q >= 10 and q % 2 == 0
  elseif U == n then
    U = nil
  end
end

function _update()
  local t = false

  local function r(r)
    local t, e, o = C(d .. n, #d + l)
    if V then
      t = V
    end
    e += r
    if not (e >= 0 and e < o) then
      return false
    end
    l = max(D(d .. n, t, e) - #d, 1)
    V = t
    v = 20
    return true
  end

  local function f(r)
    local e, o = C(d .. n, #d + l)
    e = r > 0 and 100 or 0
    l = max(D(d .. n, e, o) - #d, 1)
    t = true
  end

  local function c(r)
    u[y] = n
    y += r
    n = u[y]
    if r < 0 then
      l = #n + 1
    else
      l = max(D(d .. n, 32, 0) - #d, 1)
      local n = e(n, l)
      if n ~= "" and n ~= "\n" then
        l -= 1
      end
    end
    t = true
  end

  local function d()
    if #n > 0 then
      if #u > 50 then
        del(u, u[1])
      end
      u[#u] = n
      add(u, "")
      y = #u
      t = true
    end
  end

  local function s(e)
    if l + e > 0 then
      n = sub(n, 1, l + e - 1) .. sub(n, l + e + 1)
      l += e
      t = true
    end
  end

  local function o(e)
    n = sub(n, 1, l - 1) .. e .. sub(n, l)
    l += #e
    t = true
  end

  local i, h, e = stat(28, 224) or stat(28, 228), stat(28, 225) or stat(28, 229), -1
  if p(80) then
    if l > 1 then
      l -= 1
      t = true
    end
  elseif p(79) then
    if l <= #n then
      l += 1
      t = true
    end
  elseif p(82) then
    if (i or not r(-1)) and y > 1 then
      c(-1)
    end
  elseif p(81) then
    if (i or not r(1)) and y < #u then
      c(1)
    end
  else
    local r = stat(31)
    e = ord(r)
    if r == "•" then
      if #n == 0 then
        extcmd "pause"
      else
        a, J = {}
        d()
      end
    elseif r == "\r" or r == "\n" then
      if h then
        o "\n"
      else
        ni(n)
        if not a then
          o "\n"
        else
          d()
        end
      end
    elseif i and p(40) then
      ni(n, true)
      d()
    elseif r ~= "" and e >= 32 and e < 154 then
      if N and e >= 128 then
        r = chr(e - 63)
      end
      o(r)
    elseif e == 193 then
      o "\n"
    elseif e == 192 then
      f(-1)
    elseif e == 196 then
      f(1)
    elseif e == 203 then
      N = not N
      A, K = "shift now selects " .. (N and "punycase" or "symbols"), 40
    elseif p(74) then
      if i then
        l = 1
        t = true
      else
        f(-1)
      end
    elseif p(77) then
      if i then
        l = #n + 1
        t = true
      else
        f(1)
      end
    elseif p(42) then
      s(-1)
    elseif p(76) then
      s(0)
    end
  end
  local r = stat(4)
  if r ~= M or e == 213 then
    o(r)
    M = r
  end
  if e == 194 or e == 215 then
    if n ~= "" and n ~= M then
      M = n
      printh(n, "@clip")
      if e == 215 then
        n = ""
        l = 1
      end
      A = "press again to put in clipboard"
    else
      A = ""
    end
  end
  if stat(120) then
    local n
    repeat
      n = serial(2048, 24448, 128)
      o(chr(peek(24448, n)))
    until n == 0
  end
  if t then
    v, V = 20
  end
  q += 1
  nr()
end

function nf(n, e)
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

nf(1, function()
  assert(pack(T "(function (...) return ... end)(1,2,nil,nil)").n == 4)
end)
nf(2, function()
  assert(T "function() local temp, temp2 = {max(1,3)}, -20;return temp[1] + temp2; end" () == -17)
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