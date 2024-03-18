__lua__

local l_local = 1
g_global = {member=2}

function foo() end
local function bar() end

--use-compiler: repl

local my_local = 3
print("a string")
g_global.member = foo(l_local)
if (bar) bar(my_local)

--use-compiler: bytecode --minimal-interpreter

-- constants
local a, b, c, d, e, f, g, h = nil, true, false, 0, 0x1234.5678, -3, "hello\t!", [[world
and bytecode★]]
-- local
local a, b
local c
local i = 1, 2, 3
-- assign
a, b, c = d, e, f
g, h = h, g
-- global
g_newglob = a
h = g_global
a, b, c = d
i = 4, 5, 6
-- member
i = g_global.member
g_global.member2 = d
-- index
g_global[3] = 4
local j = g_global[3]
-- ops
local k = a + b - c * d / e \ f % g ^ h
local l = a & b | c ^^ d ~ e
local m = a << b >> c >>> d >>< e <<> f
local n = a < b and c > d or e <= f and g >= h
local o = a ~= b and c != d or e == f
local p = -a .. ~b .. not c .. #g_global .. @d .. %e .. $f
-- ctor
local q = {}
local r = {1, 2, 3, a=4, b=5, [100]=6, 7, 8, c=9, [a]=b}
-- group/call
foo(1, 2, 3)
foo(foo())
foo(1, 2, 3, foo"z")
foo((foo()))
g_global:call(1, 2)
g_global:call{1, 2}
local s = foo()
local t, u, v = foo()
local w = {1, foo()}
local x, y, z = (foo())
local aa = 1, foo()
-- function/upval
function f1(p1, p2)
    if (p1 == p2) return
    return r[p1] + q[p2]
end
local function f2(...)
    a = {10, a=11, ...}
    print((...))
    return f2(a, ...)
end
function g_global.misc.f3() end
function g_global:call(a, b, ...)
    print(self)
    local u, v, w = -1, ...
    return b, a, ..., ...
end
-- op assign
b += 1; c -= 2; d *= 3; e /= 4; f \= 5; g %= 6; h ^= 7
b &= 1; c |= 2; d ^^= 3; 
b <<= 4; c >>= 4; d >>>= 5; e <<>= 6; f >><= 7
g_global[3] += 1; g_global.x -= 2
({member=1}).member += 2
({member=1})[b + c] -= 3
-- if
if (a == b) print"eq"
if (a != b) print"ne" else print"eq"
if a != b then print"ne1" end
if a != b then print"ne1" else print"eq1" end
if a != b then print"ne1" 
elseif a == b then print"eq1" else print"??1" end
-- while/break
while (c == d) print"stuck"
while c != d do print"nel" end
while c != d do
    if (f) break
end
repeat print"nel2"
    if (f) break
until e == f
-- for
for i=1,10 do print(i) end
for j=1,-5,-1 do print(j) end
g_step=2 for k=1,4,g_step do print(k) end
g_step=2 for k=1,g_step,g_step do print(k) end
for k in next,g_global do print(k) end
for k in next,1,2,3,print(k) do print(k) end
for k,v in all{1,2,3} do print(k..v) end
-- goto/label
::back::
if (a) goto fwd else goto back
::fwd::
-- misc
do print"ende" end

--use-compiler: none

print("back in the main code! "..l_local)
