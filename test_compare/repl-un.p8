pico-8 cartridge // http://www.pico-8.com
version 38
__lua__

local nw, nx, n3 = _ENV, {}, {}
for n, e in pairs(_ENV) do
  nx[n] = e
  if (type(e) == "function") n3[n] = true
end
local _ENV = nx
A, V = true

function i(t, e)
  for n = 1, #e do
    if (sub(e, n, n) == t) return n
  end
end

function e(t, n)
  return sub(t, n, n)
end

local nm, n7 = split "a,b,f,n,r,t,v,\\,\",',\n,*,#,-,|,+,^", split "⁷,⁸,ᶜ,\n,\r,	,ᵇ,\\,\",',\n,¹,²,³,⁴,⁵,⁶"
local nx = {}
for n = 1, #nm do
  nx[nm[n]] = n7[n]
end

function m(n)
  return n >= "0" and n <= "9"
end

function z(n)
  return n >= "A" and n <= "Z" or n >= "a" and n <= "z" or n == "_" or n >= "█" or m(n)
end

function nf(r, n, f, o)
  local t = ""
  while n <= #r do
    local l = e(r, n)
    if (l == f) break
    if l == "\\" then
      n += 1
      local t = e(r, n)
      l = nx[t]
      if t == "x" then
        t = tonum("0x" .. sub(r, n + 1, n + 2))
        if (t) n += 2 else o "bad hex escape"
        l = chr(t)
      elseif m(t) then
        local i = n
        while m(t) and n < i + 3 do
          n += 1
          t = e(r, n)
        end
        n -= 1
        t = tonum(sub(r, i, n))
        if (not t or t >= 256) o "bad decimal escape"
        l = chr(t)
      elseif t == "z" then
        repeat
          n += 1
          t = e(r, n)
        until not i(t, " \r	ᶜᵇ\n")
        if (t == "") o()
        l = ""
        n -= 1
      elseif t == "" then
        o()
        l = ""
      end
      if (not l) o("bad escape: " .. t); l = ""
    elseif l == "\n" then
      o "unterminated string"
      break
    end
    t ..= l
    n += 1
  end
  if (n > #r) o("unterminated string", true)
  return t, n + 1
end

function W(t, n, l, r)
  if e(t, n) == "[" then
    n += 1
    local o = n
    while (e(t, n) == "=") n += 1
    local r = "]" .. sub(t, o, n - 1) .. "]"
    local o = #r
    if e(t, n) == "[" then
      n += 1
      if (e(t, n) == "\n") n += 1
      local e = n
      while (n <= #t and sub(t, n, n + o - 1) ~= r) n += 1
      if (n >= #t) l()
      return sub(t, e, n - 1), n + o
    end
  end
  if (r) l "invalid long brackets"
  return nil, n
end

function Y(l, c)
  local n, s, f = 1, 1
  local o, h, b, p, u = {}, {}, {}, {}

  local function d(n, e)
    if (c) nn(n, f)
    u = n and not e
  end

  while n <= #l do
    f = n
    local t = e(l, n)
    local a, r
    if i(t, " \r	ᶜᵇ\n") then
      n += 1
      a = true
      if (t == "\n") s += 1
    elseif t == "-" and e(l, n + 1) == "-" then
      n += 2
      if (e(l, n) == "[") r, n = W(l, n, d)
      if not r then
        while (n <= #l and e(l, n) ~= "\n") n += 1
      end
      if (c) a = true else add(o, true)
    elseif m(t) or t == "." and m(e(l, n + 1)) then
      local u, a = "0123456789", true
      if t == "0" and i(e(l, n + 1), "xX") then
        u ..= "AaBbCcDdEeFf"
        n += 2
      elseif t == "0" and i(e(l, n + 1), "bB") then
        u = "01"
        n += 2
      end
      while true do
        t = e(l, n)
        if t == "." and a then
          a = false
        elseif not i(t, u) then
          break
        end
        n += 1
      end
      r = sub(l, f, n - 1)
      if (not tonum(r)) d "bad number"; r = "0"
      add(o, tonum(r))
    elseif z(t) then
      while z(e(l, n)) do
        n += 1
      end
      add(o, sub(l, f, n - 1))
    elseif t == "'" or t == '"' then
      r, n = nf(l, n + 1, t, d)
      add(o, {t = r})
    elseif t == "[" and i(e(l, n + 1), "=[") then
      r, n = W(l, n, d, true)
      add(o, {t = r})
    else
      n += 1
      local e, r, u = unpack(split(sub(l, n, n + 2), ""))
      if e == t and r == t and i(t, ".>") then
        n += 2
        if (u == "=" and i(t, ">")) n += 1
      elseif e == t and r ~= t and i(t, "<>") and i(r, "<>") then
        n += 2
        if (u == "=") n += 1
      elseif e == t and i(t, ".:^<>") then
        n += 1
        if (r == "=" and i(t, ".^<>")) n += 1
      elseif e == "=" and i(t, "+-*/\\%^&|<>=~!") then
        n += 1
      elseif i(t, "+-*/\\%^&|<>=~#(){}[];,?@$.:") then
      else
        d("bad char: " .. t)
      end
      add(o, sub(l, f, n - 1))
    end
    if (not a) add(h, s); add(b, f); add(p, n - 1)
    if (u) o[#o], u = false, false
  end
  return o, h, b, p
end

function l(t, n)
  for e = 1, #n do
    if (n[e] == t) return e
  end
end

function a(n)
  return unpack(n, 1, n.n)
end

function nd(e)
  local n = {}
  for t, l in next, e do
    n[t] = l
  end
  return n
end

local W = split "and,break,do,else,elseif,end,false,for,function,goto,if,in,local,nil,not,or,repeat,return,then,true,until,while"
q = {}
for n in all(W) do
  q[n] = true
end

local function W(n)
  return type(n) == "string" and e(n, #n) == "="
end

ne = split "end,else,elseif,until"

function nt(n, j)
  local o, F, r = Y(n, true)
  local n, f, s, y, h, Z = 1, 0, 0
  local t, b
  local v, d, w, x = {}

  local function i(e)
    nn(e, r[n - 1] or 1)
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

  local function G()
    local n = d["..."]
    if (not n or n ~= Z) i "unexpected '...'"
    return function(e)
      return a(e[n]["..."])
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

  local function r(e)
    local t = o[n]
    n += 1
    if (t == e) return
    if (t == nil) i()
    i("expected: " .. e)
  end

  local function c(t)
    if (not t) t = o[n]; n += 1
    if (t == nil) i()
    if (type(t) == "string" and z(e(t, 1)) and not q[t]) return t
    if (type(t) == "string") i("invalid identifier: " .. t)
    i "identifier expected"
  end

  local function e(t)
    if (o[n] == t) n += 1; return true
  end

  local function z()
    d = setmetatable({}, {__index = d})
    f += 1
  end

  local function B()
    d = getmetatable(d).__index
    f -= 1
  end

  local function m(r, l)
    local e = {}
    local n = #l
    for t = 1, n - 1 do
      e[t] = l[t](r)
    end
    if n > 0 then
      local t = pack(l[n](r))
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

  local function X(l, o, i)
    local n = {}
    if i then
      add(n, i)
    elseif not e ")" then
      while true do
        add(n, (t()))
        if (e ")") break
        r ","
      end
    end
    if o then
      return function(e)
        local t = l(e)
        return t[o](t, a(m(e, n)))
      end, true, nil, function(e)
        local t = l(e)
        return t[o], pack(t, a(m(e, n)))
      end
    else
      return function(e)
        return l(e)(a(m(e, n)))
      end, true, nil, function(e)
        return l(e), m(e, n)
      end
    end
  end

  local function q()
    local l, d = {}, {}
    local a, u = 1
    while not e "}" do
      u = nil
      local i, f
      if e "[" then
        i = t()
        r "]"
        r "="
        f = t()
      elseif o[n + 1] == "=" then
        i = g(c())
        r "="
        f = t()
      else
        i = g(a)
        f = t()
        a += 1
        u = #l + 1
      end
      add(l, i)
      add(d, f)
      if (e "}") break
      if (not e ";") r ","
    end
    return function(e)
      local t = {}
      for n = 1, #l do
        if n == u then
          local o, r = l[n](e), pack(d[n](e))
          for n = 1, r.n do
            t[o + n - 1] = r[n]
          end
        else
          t[l[n](e)] = d[n](e)
        end
      end
      return t
    end
  end

  local function E(o, u)
    local n, p, t
    if o then
      if u then
        z()
        n = c()
        d[n] = f
        t = D(n)
      else
        n = {c()}
        while (e ".") add(n, c())
        if (e ":") add(n, c()); p = true
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
    local n, l = {}
    if (p) add(n, "self")
    r "("
    if not e ")" then
      while true do
        if (e "...") l = true else add(n, c())
        if (e ")") break
        r ","
        if (l) i "unexpected param after '...'"
      end
    end
    z()
    for e in all(n) do
      d[e] = f
    end
    if (l) d["..."] = f
    local e, i, d = v, h, Z
    v, h, Z = {}, s + 1, f
    local c = b()
    for n in all(v) do
      n()
    end
    v, h, Z = e, i, d
    r "end"
    B()
    return function(e)
      if (u) add(e, {})
      local r = nd(e)
      local i = #r
      local f = function(...)
        local t = pack(...)
        local e = r
        if #e ~= i then
          local n = {}
          for t = 0, i do
            n[t] = e[t]
          end
          e = n
        end
        local r = {}
        for e = 1, #n do
          r[n[e]] = t[e]
        end
        if (l) r["..."] = pack(unpack(t, #n + 1, t.n))
        add(e, r)
        local n = c(e)
        deli(e)
        if n then
          if (type(n) == "table") return a(n)
          return n()
        end
      end
      if (o) local n, l = t(e); n[l] = f else return f
    end
  end

  local function Z()
    local e = o[n]
    n += 1
    local n
    if (e == nil) i()
    if (e == "nil") return g()
    if (e == "true") return g(true)
    if (e == "false") return g(false)
    if (type(e) == "number") return g(e)
    if (type(e) == "table") return g(e.t)
    if (e == "{") return q()
    if (e == "(") n = t(); r ")"; return function(e) return (n(e)) end, true
    if (e == "-") n = t(11); return function(e) return -n(e) end
    if (e == "~") n = t(11); return function(e) return ~n(e) end
    if (e == "not") n = t(11); return function(e) return not n(e) end
    if (e == "#") n = t(11); return function(e) return #n(e) end
    if (e == "@") n = t(11); return function(e) return @n(e) end
    if (e == "%") n = t(11); return function(e) return %n(e) end
    if (e == "$") n = t(11); return function(e) return $n(e) end
    if (e == "function") return E()
    if (e == "...") return G()
    if (e == "\\") n = c(); return function() return nu(n) end, true, function() return na(n) end
    if (c(e)) return C(e), true, D(e)
    i("unexpected token: " .. e)
  end

  local function D(e, t, l, r)
    local n
    if (e == "^" and t <= 12) n = r(12); return function(e) return l(e) ^ n(e) end
    if (e == "*" and t < 10) n = r(10); return function(e) return l(e) * n(e) end
    if (e == "/" and t < 10) n = r(10); return function(e) return l(e) / n(e) end
    if (e == "\\" and t < 10) n = r(10); return function(e) return l(e) \ n(e) end
    if (e == "%" and t < 10) n = r(10); return function(e) return l(e) % n(e) end
    if (e == "+" and t < 9) n = r(9); return function(e) return l(e) + n(e) end
    if (e == "-" and t < 9) n = r(9); return function(e) return l(e) - n(e) end
    if (e == ".." and t <= 8) n = r(8); return function(e) return l(e) .. n(e) end
    if (e == "<<" and t < 7) n = r(7); return function(e) return l(e) << n(e) end
    if (e == ">>" and t < 7) n = r(7); return function(e) return l(e) >> n(e) end
    if (e == ">>>" and t < 7) n = r(7); return function(e) return l(e) >>> n(e) end
    if (e == "<<>" and t < 7) n = r(7); return function(e) return l(e) <<> n(e) end
    if (e == ">><" and t < 7) n = r(7); return function(e) return l(e) >>< n(e) end
    if (e == "&" and t < 6) n = r(6); return function(e) return l(e) & n(e) end
    if (e == "^^" and t < 5) n = r(5); return function(e) return l(e) ~ n(e) end
    if (e == "|" and t < 4) n = r(4); return function(e) return l(e) | n(e) end
    if (e == "<" and t < 3) n = r(3); return function(e) return l(e) < n(e) end
    if (e == ">" and t < 3) n = r(3); return function(e) return l(e) > n(e) end
    if (e == "<=" and t < 3) n = r(3); return function(e) return l(e) <= n(e) end
    if (e == ">=" and t < 3) n = r(3); return function(e) return l(e) >= n(e) end
    if (e == "==" and t < 3) n = r(3); return function(e) return l(e) == n(e) end
    if ((e == "~=" or e == "!=") and t < 3) n = r(3); return function(e) return l(e) ~= n(e) end
    if (e == "and" and t < 2) n = r(2); return function(e) return l(e) and n(e) end
    if (e == "or" and t < 1) n = r(1); return function(e) return l(e) or n(e) end
  end

  local function q(d, e, u)
    local i = o[n]
    n += 1
    local l, f
    if u then
      if (i == ".") l = c(); return function(n) return e(n)[l] end, true, function(n) return e(n), l end
      if (i == "[") l = t(); r "]"; return function(n) return e(n)[l(n)] end, true, function(n) return e(n), l(n) end
      if (i == "(") return X(e)
      if (i == "{" or type(i) == "table") n -= 1; f = Z(); return X(e, nil, f)
      if i == ":" then
        l = c()
        if (o[n] == "{" or type(o[n]) == "table") f = Z(); return X(e, l, f)
        r "("
        return X(e, l)
      end
    end
    local l = D(i, d, e, t)
    if (not l) n -= 1
    return l
  end

  t = function(o)
    local n, e, t, l = Z()
    while true do
      local r, i, f, d = q(o or 0, n, e)
      if (not r) break
      n, e, t, l = r, i, f, d
    end
    return n, t, l
  end

  local function Z()
    local e, n = t()
    if (not n) i "cannot assign to value"
    return n
  end

  local function q()
    local n = k(Z)
    r "="
    local e = k(t)
    if #n == 1 and #e == 1 then
      return function(t)
        local l, r = n[1](t)
        l[r] = e[1](t)
      end
    else
      return function(t)
        local l, r = {}, {}
        for e = 1, #n do
          local o, i = n[e](t)
          add(l, o)
          add(r, i)
        end
        local o = m(t, e)
        for e = #n, 1, -1 do
          l[e][r[e]] = o[e]
        end
      end
    end
  end

  local function G(e, l)
    local r = o[n]
    n += 1
    local o = sub(r, 1, -2)
    local n = D(o, 0, e, function()
      return t()
    end)
    if (not n) i "invalid compound assignment"
    return function(e)
      local t, r = l(e)
      t[r] = n(e)
    end
  end

  local function H()
    if e "function" then
      return E(true, true)
    else
      local n = k(c)
      local l = e "=" and k(t) or {}
      z()
      for e = 1, #n do
        d[n[e]] = f
      end
      if #n == 1 and #l == 1 then
        return function(e)
          add(e, {[n[1]] = l[1](e)})
        end
      else
        return function(e)
          local t = {}
          local r = m(e, l)
          for e = 1, #n do
            t[n[e]] = r[e]
          end
          add(e, t)
        end
      end
    end
  end

  local function D(e)
    local t = F[n - 1]
    x = function()
      return t ~= F[n]
    end
    if (not e or x()) i(n <= #o and "bad shorthand" or nil)
  end

  local function F()
    local l = o[n] == "("
    local o = t()
    local t, n
    if e "then" then
      t, n = b()
      if e "else" then
        n = b()
        r "end"
      elseif e "elseif" then
        n = F()
      else
        r "end"
      end
    else
      D(l)
      t = b()
      if (not x() and e "else") n = b()
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
    if (n == true) return
    return n, e
  end

  local function I()
    local l = o[n] == "("
    local o = t()
    local n
    if e "do" then
      n = Z()
      r "end"
    else
      D(l)
      n = Z()
      x = nil
    end
    return function(e)
      while o(e) do
        if (stat(1) >= 1) p()
        local t, l = n(e)
        if (t) return X(t, l)
      end
    end
  end

  local function D()
    local l = f
    local o = Z(true)
    r "until"
    local r = t()
    while (f > l) B()
    return function(n)
      repeat
        if (stat(1) >= 1) p()
        local e, t = o(n)
        if (not e) t = r(n)
        while (#n > l) deli(n)
        if (e) return X(e, t)
      until t
    end
  end

  local function J()
    if o[n + 1] == "=" then
      local l = c()
      r "="
      local o = t()
      r ","
      local i = t()
      local u = e "," and t() or g(1)
      r "do"
      z()
      d[l] = f
      local t = Z()
      r "end"
      B()
      return function(n)
        for e = o(n), i(n), u(n) do
          if (stat(1) >= 1) p()
          add(n, {[l] = e})
          local e, l = t(n)
          deli(n)
          if (e) return X(e, l)
        end
      end
    else
      local l = k(c)
      r "in"
      local o = k(t)
      r "do"
      z()
      for n in all(l) do
        d[n] = f
      end
      local i = Z()
      r "end"
      B()
      return function(n)
        local e = m(n, o)
        while true do
          local r = {}
          local t = {e[1](e[2], e[3])}
          if (t[1] == nil) break
          e[3] = t[1]
          for n = 1, #l do
            r[l[n]] = t[n]
          end
          if (stat(1) >= 1) p()
          add(n, r)
          local e, t = i(n)
          deli(n)
          if (e) return X(e, t)
        end
      end
    end
  end

  local function g()
    if (not y or h and y < h) i "break outside of loop"
    return function()
      return true
    end
  end

  local function y()
    if (not h and not j) i "return outside of function"
    if o[n] == ";" or l(o[n], ne) or x and x() then
      return function()
        return pack()
      end
    else
      local r, n, l = t()
      local n = {r}
      while (e ",") add(n, (t()))
      if #n == 1 and l and h then
        return function(n)
          local e, t = l(n)
          if (stat(1) >= 1) p()
          return function()
            return e(a(t))
          end
        end
      else
        return function(e)
          return m(e, n)
        end
      end
    end
  end

  local function z(e)
    local n = c()
    r "::"
    if (w[n] and w[n].e == s) i "label already defined"
    w[n] = {l = f, e = s, o = e, r = #e}
  end

  local function Z()
    local t = c()
    local e, l, n = w, f
    add(v, function()
      n = e[t]
      if (not n) i "label not found"
      if (h and n.e < h) i "goto outside of function"
      local t = e[n.e] or l
      if (n.l > t and n.r < #n.o) i "goto past local"
    end)
    return function()
      if (stat(1) >= 1) p()
      return 0, n
    end
  end

  local function c(f)
    local l = o[n]
    n += 1
    if (l == ";") return
    if (l == "do") local n = b(); r "end"; return n
    if (l == "if") return F()
    if (l == "while") return I()
    if (l == "repeat") return D()
    if (l == "for") return J()
    if (l == "break") return g()
    if (l == "return") return y(), true
    if (l == "local") return H()
    if (l == "goto") return Z()
    if (l == "::") return z(f)
    if (l == "function" and o[n] ~= "(") return E(true)
    if l == "?" then
      local e, l = C "print", k(t)
      return function(n)
        e(n)(a(m(n, l)))
      end
    end
    n -= 1
    local f = n
    local l, d, r = t()
    if e "," or e "=" then
      n = f
      return q()
    elseif W(o[n]) then
      return G(l, d)
    elseif s <= 1 and A then
      return function(e)
        local n = pack(l(e))
        if (not (r and n.n == 0)) add(u, n)
        V = n[1]
      end
    else
      if (not r) i "statement has no effect"
      return function(n)
        l(n)
      end
    end
  end

  b = function(t)
    w = setmetatable({}, {__index = w})
    w[s] = f
    s += 1
    local d = s
    local i = t and 32767 or f
    local r = {}
    while n <= #o and not l(o[n], ne) and not (x and x()) do
      local n, t = c(r)
      if (n) add(r, n)
      if (t) e ";"; break
    end
    while (f > i) B()
    s -= 1
    w = getmetatable(w).__index
    return function(e)
      local t, n
      local l, o = 1, #r
      while l <= o do
        t, n = r[l](e)
        if t then
          if (type(t) ~= "number") break
          if (n.e ~= d) break
          l = n.r
          while (#e > n.l) deli(e)
          t, n = nil
        end
        l += 1
      end
      while (#e > i) deli(e)
      return t, n
    end
  end
  d = A and {_ENV = 0, _env = 0, _ = 0} or {_ENV = 0}
  local e = b()
  if (n <= #o) i "unexpected end"
  for n in all(v) do
    n()
  end
  return function(n)
    local t = A and {_ENV = n, _env = n, _ = V} or {_ENV = n}
    local n = e {[0] = t}
    if (n) return a(n)
  end
end

N, O = 10, false
local V = {["\0"] = "000", ["ᵉ"] = "014", ["ᶠ"] = "015"}
for n, e in pairs(nx) do
  if (not i(n, "'\n")) V[e] = n
end

function nc(n)
  local t = 1
  while t <= #n do
    local l = e(n, t)
    local e = V[l]
    if (e) n = sub(n, 1, t - 1) .. "\\" .. e .. sub(n, t + 1); t += #e
    t += 1
  end
  return '"' .. n .. '"'
end

function n1(n)
  if (type(n) ~= "string") return false
  if (q[n]) return false
  if (#n == 0 or m(e(n, 1))) return false
  for t = 1, #n do
    if (not z(e(n, t))) return false
  end
  return true
end

function B(e, t)
  local n = type(e)
  if n == "nil" then
    return "nil"
  elseif n == "boolean" then
    return e and "true" or "false"
  elseif n == "number" then
    return tostr(e, O)
  elseif n == "string" then
    return nc(e)
  elseif n == "table" and not t then
    local n = "{"
    local l = 0
    local r = 0
    for t, o in next, e do
      if (l == N) n = n .. ",<...>"; break
      if (l > 0) n = n .. ","
      local e = B(o, 1)
      if t == r + 1 then
        n = n .. e
        r = t
      elseif n1(t) then
        n = n .. t .. "=" .. e
      else
        n = n .. "[" .. B(t, 1) .. "]=" .. e
      end
      l += 1
    end
    return n .. "}"
  else
    return "<" .. tostr(n) .. ">"
  end
end

function ns(n, e)
  if (e == nil) return n
  if (not n) n = ""
  local t = min(21, #e)
  for l = 1, t do
    if (#n > 0) n ..= "\n"
    local t = e[l]
    if type(t) == "table" then
      local e = ""
      for n = 1, t.n do
        if (#e > 0) e = e .. ", "
        e = e .. B(t[n])
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
f = "> "
n, c, g = "", 1, 0
t, k = 1, 20
d, v = {""}, 1
Z = false
s, r = 0, 1
G, H = true, true
o = {7, 4, 3, 5, 6, 8, 5, 12, 14, 7, 11, 5}
nw.print = function(n, ...)
  if (pack(...).n ~= 0 or not G) return print(n, ...)
  add(u, tostr(n))
end

function nl()
  poke(24368, 1)
end

function nr()
  return function()
    if (stat(30)) return stat(31)
  end
end

function P(r, i)
  local t = 1
  local n, l = 0, 0
  if (not r) return t, n, l
  while t <= #r do
    local o = e(r, t)
    local e = o >= "█"
    if (n >= (e and 31 or 32)) l += 1; n = 0
    if (i) i(t, o, n, l)
    if o == "\n" then
      l += 1
      n = 0
    else
      n += e and 2 or 1
    end
    t += 1
  end
  return t, n, l
end

function X(o, l)
  local n, e = 0, 0
  local i, r, t = P(o, function(t, i, r, o)
    if (l == t) n, e = r, o
  end)
  if (l >= i) n, e = r, t
  if (r > 0) t += 1
  return n, e, t
end

function C(i, r, e)
  local t = 1
  local n = false
  local o, f, l = P(i, function(o, f, i, l)
    if (e == l and r == i and not n) t = o; n = true
    if ((e < l or e == l and r < i) and not n) t = o - 1; n = true
  end)
  if (not n) t = e >= l and o or o - 1
  if (f > 0) l += 1
  return t, l
end

function Q(n, t, l, e)
  if type(e) == "function" then
    P(n, function(n, r, o, i)
      print(r, t + o * 4, l + i * 6, e(n))
    end)
  else
    print(n and "⁶rw" .. n, t, l, e)
  end
end

function nh(n, i, f)
  local d, t, u, r = Y(n)
  local t = 1
  Q(n, i, f, function(i)
    while t <= #r and r[t] < i do
      t += 1
    end
    local n
    if (t <= #r and u[t] <= i) n = d[t]
    local t = o[5]
    if n == false then
      t = o[6]
    elseif n == true then
      t = o[7]
    elseif type(n) ~= "string" or l(n, {"nil", "true", "false"}) then
      t = o[8]
    elseif q[n] then
      t = o[9]
    elseif not z(e(n, 1)) then
      t = o[10]
    elseif n3[n] then
      t = o[11]
    end
    return t
  end)
end

function _draw()
  local a = peek(24357)
  local b, p = peek2(24360), peek2(24362)
  camera()

  local function e(n)
    cursor(0, 127)
    for e = 1, n do
      rectfill(0, r * 6, 127, (r + 1) * 6 - 1, 0)
      if r < 21 then
        r += 1
      else
        print ""
      end
    end
  end

  local function x(n, e)
    for t = 1, n do
      if (r > e) r -= 1
      rectfill(0, r * 6, 127, (r + 1) * 6 - 1, 0)
    end
  end

  local function m(n, e)
    for t = 0, 2 do
      local l = pget(n + t, e + 5)
      pset(n + t, e + 5, l == 0 and o[12] or 0)
    end
  end

  local function d(u)
    local i = f .. n .. " "
    local d, l, n = X(i, #f + t)
    if n > c then
      e(n - c)
    elseif n < c then
      x(c - n, n)
    end
    c = n
    g = mid(g, 0, max(c - 21, 0))
    ::again::
    local e = r - c + g
    if (e + l < 0) g += 1; goto again
    if (e + l >= 21) g -= 1; goto again
    local n = e * 6
    rectfill(0, n, 127, n + c * 6 - 1, 0)
    if (c > 21) rectfill(0, 126, 127, 127, 0)
    nh(i, 0, n)
    print(f, 0, n, o[4])
    if (k >= 10 and u ~= false and not w) m(d * 4, n + l * 6)
  end

  local function f(t)
    e(1)
    r -= 1
    print("[enter] ('esc' to abort)", 0, r * 6, o[3])
    while true do
      flip()
      nl()
      for n in nr() do
        if (n == "•") Z = true; h = ""; u = {}; return false
        if (n == "\r" or n == "\n") s += t; return true
      end
    end
  end

  ::again::
  local i, l
  if u or h then
    i, l = C(h, 0, s)
    if l - s <= 20 and u then
      h, u = ns(h, u)
      i, l = C(h, 0, s)
      if (#u == 0 and not w) u = nil
    end
  end
  if (not w) camera()
  if (s == 0 and not w) d(not h)
  if h then
    local u = sub(h, i)
    local i = min(l - s, 20)
    e(i)
    Q(u, 0, (r - i) * 6, o[1])
    if i < l - s then
      if (f(i)) goto again
    else
      local f, u, l = X(I, 0)
      e(l)
      Q(I, 0, (r - l) * 6, o[2])
      if w then
        s += i
      else
        n, c, g, t, s, h, I = "", 0, 0, 1, 0
        d()
      end
    end
  end
  if w then
    e(1)
    r -= 1
    print(w, 0, r * 6, o[3])
  end
  if y then
    e(1)
    r -= 1
    print(y, 0, r * 6, o[3])
    y = nil
  end
  if J then
    J -= 1
    if (J == 0) y, J = ""
  end
  k -= 1
  if (k == 0) k = 20
  color(a)
  camera(b, p)
  if (r <= 20) cursor(0, r * 6)
end

K, D, E = false, false, false
F = {}

function nn(n, e)
  x, n0 = n, e
  assert(false, n)
end

function R(n, e, t)
  return nt(n, t)(e or nw)
end

function S(n, e)
  return R("return " .. n, e, true)
end

function n2(t)
  local l = cocreate(nt)
  ::_::
  local n, e = coresume(l, t)
  if (n and not e) goto _
  if (not n) e, x = x, false
  return n, e
end

function nb(n, e)
  local t, l = X(n, e)
  return "line " .. l + 1 .. " col " .. t + 1
end

function no(e, l)
  u, Z, x = {}, false, false
  K, D, E = false, false, false
  local t = cocreate(function()
    R(e)
  end)
  local r, n
  while true do
    r, n = coresume(t)
    if (costatus(t) == "dead") break
    if G and not D then
      w = "running, press 'esc' to abort"
      _draw()
      flip()
      w = nil
    else
      if (H and not D and not E) flip()
      if (not H and holdframe) holdframe()
      E = false
    end
    for n in nr() do
      if n == "•" then
        Z = true
      else
        add(F, n)
      end
    end
    if (Z) n = "computation aborted"; break
  end
  if x == nil then
    if (l) n = "unexpected end of code" else n, u = nil
  end
  if (x) n, x = x .. "\nat " .. nb(e, n0)
  I = n
  F = {}
end

p = function()
  K = true
  yield()
  K = false
end
nw.flip = function(...)
  local n = pack(flip(...))
  E = true
  p()
  return a(n)
end
nw.coresume = function(n, ...)
  local e = pack(coresume(n, ...))
  while K do
    yield()
    e = pack(coresume(n))
  end
  x = false
  return a(e)
end
nw.stat = function(n, ...)
  if n == 30 then
    return #F > 0 or stat(n, ...)
  elseif n == 31 then
    if #F > 0 then
      return deli(F, 1)
    else
      local e = stat(n, ...)
      if (e == "•") Z = true
      return e
    end
  else
    return stat(n, ...)
  end
end

function np(n)
  if (_set_fps) _set_fps(n._update60 and 60 or 30)
  if (n._init) n._init()
  D = true
  while true do
    if (_update_buttons) _update_buttons()
    if (holdframe) holdframe()
    if n._update60 then
      n._update60()
    elseif n._update then
      n._update()
    end
    if (n._draw) n._draw()
    flip()
    E = true
    p()
  end
  D = false
end

function nu(e)
  if l(e, {"i", "interrupt"}) then
    return G
  elseif l(e, {"f", "flip"}) then
    return H
  elseif l(e, {"r", "repl"}) then
    return A
  elseif l(e, {"mi", "max_items"}) then
    return N
  elseif l(e, {"h", "hex"}) then
    return O
  elseif l(e, {"cl", "colors"}) then
    return o
  elseif l(e, {"c", "code"}) then
    local e = {[0] = n}
    for n = 1, #d - 1 do
      e[n] = d[#d - n]
    end
    return e
  elseif l(e, {"cm", "compile"}) then
    return function(n)
      return n2(n)
    end
  elseif l(e, {"x", "exec"}) then
    return function(n, e)
      R(n, e)
    end
  elseif l(e, {"v", "eval"}) then
    return function(n, e)
      return S(n, e)
    end
  elseif l(e, {"p", "print"}) then
    return function(n, ...)
      nw.print(B(n), ...)
    end
  elseif l(e, {"ts", "tostr"}) then
    return function(n)
      return B(n)
    end
  elseif l(e, {"rst", "reset"}) then
    run()
  elseif l(e, {"run"}) then
    np(nw)
  else
    assert(false, "unknown \\-command")
  end
end

function na(e)
  local function t(n)
    return n and n ~= 0 and true or false
  end

  local n
  if l(e, {"i", "interrupt"}) then
    n = function(n)
      G = t(n)
    end
  elseif l(e, {"f", "flip"}) then
    n = function(n)
      H = t(n)
    end
  elseif l(e, {"r", "repl"}) then
    n = function(n)
      A = t(n)
    end
  elseif l(e, {"mi", "max_items"}) then
    n = function(n)
      N = tonum(n) or -1
    end
  elseif l(e, {"h", "hex"}) then
    n = function(n)
      O = t(n)
    end
  elseif l(e, {"cl", "colors"}) then
    n = function(n)
      o = n
    end
  else
    assert(false, "unknown \\-command assign")
  end
  local e = {__newindex = function(t, l, e)
    n(e)
  end}
  return setmetatable(e, e), 0
end

L = stat(4)
j, M = 0, false
poke(24412, 10, 2)

function b(n)
  if stat(28, n) then
    if (n ~= T) T, j = n, 0
    return j == 0 or j >= 10 and j % 2 == 0
  elseif T == n then
    T = nil
  end
end

function _update()
  local l = false

  local function r(o)
    local l, e, r = X(f .. n, #f + t)
    if (U) l = U
    e += o
    if (not (e >= 0 and e < r)) return false
    t = max(C(f .. n, l, e) - #f, 1)
    U = l
    k = 20
    return true
  end

  local function a(r)
    local e, o = X(f .. n, #f + t)
    e = r > 0 and 100 or 0
    t = max(C(f .. n, e, o) - #f, 1)
    l = true
  end

  local function c(r)
    d[v] = n
    v += r
    n = d[v]
    if r < 0 then
      t = #n + 1
    else
      t = max(C(f .. n, 32, 0) - #f, 1)
      local l = e(n, t)
      if (l ~= "" and l ~= "\n") t -= 1
    end
    l = true
  end

  local function f()
    if #n > 0 then
      if (#d > 50) del(d, d[1])
      d[#d] = n
      add(d, "")
      v = #d
      l = true
    end
  end

  local function s(e)
    if t + e > 0 then
      n = sub(n, 1, t + e - 1) .. sub(n, t + e + 1)
      t += e
      l = true
    end
  end

  local function o(e)
    n = sub(n, 1, t - 1) .. e .. sub(n, t)
    t += #e
    l = true
  end

  local i = stat(28, 224) or stat(28, 228)
  local h = stat(28, 225) or stat(28, 229)
  local e = -1
  if b(80) then
    if (t > 1) t -= 1; l = true
  elseif b(79) then
    if (t <= #n) t += 1; l = true
  elseif b(82) then
    if ((i or not r(-1)) and v > 1) c(-1)
  elseif b(81) then
    if ((i or not r(1)) and v < #d) c(1)
  else
    local r = stat(31)
    e = ord(r)
    if r == "•" then
      if #n == 0 then
        extcmd "pause"
      else
        u, I = {}
        f()
      end
    elseif r == "\r" or r == "\n" then
      if h then
        o "\n"
      else
        no(n)
        if (not u) o "\n" else f()
      end
    elseif i and b(40) then
      no(n, true)
      f()
    elseif r ~= "" and e >= 32 and e < 154 then
      if (M and e >= 128) r = chr(e - 63)
      o(r)
    elseif e == 193 then
      o "\n"
    elseif e == 192 then
      a(-1)
    elseif e == 196 then
      a(1)
    elseif e == 203 then
      M = not M
      y, J = "shift now selects " .. (M and "punycase" or "symbols"), 40
    elseif b(74) then
      if (i) t = 1; l = true else a(-1)
    elseif b(77) then
      if (i) t = #n + 1; l = true else a(1)
    elseif b(42) then
      s(-1)
    elseif b(76) then
      s(0)
    end
  end
  local r = stat(4)
  if (r ~= L or e == 213) o(r); L = r
  if e == 194 or e == 215 then
    if n ~= "" and n ~= L then
      L = n
      printh(n, "@clip")
      if (e == 215) n = ""; t = 1
      y = "press again to put in clipboard"
    else
      y = ""
    end
  end
  if stat(120) then
    local n
    repeat
      n = serial(2048, 24448, 128)
      o(chr(peek(24448, n)))
    until n == 0
  end
  if (l) k, U = 20
  j += 1
  nl()
end

function ni(n, e)
  local t, l = coresume(cocreate(e))
  if not t then
    printh("error #" .. n .. ": " .. l)
    print("error #" .. n .. "\npico8 broke something again,\nthis cart may not work.\npress any button to ignore")
    while (btnp() == 0) flip()
    cls()
  end
end

ni(1, function()
  assert(pack(S "(function (...) return ... end)(1,2,nil,nil)").n == 4)
end)
ni(2, function()
  assert(S "function() local temp, temp2 = {max(1,3)}, -20;return temp[1] + temp2; end" () == -17)
end)
printh "finished"
stop()
while true do
  if (holdframe) holdframe()
  _update()
  _draw()
  flip()
end

__meta:title__
keep:------------------------------------
keep: Please see 'Commented Source Code' section in the BBS