pico-8 cartridge // http://www.pico-8.com
version 42
__lua__

print = printh
?"hello ᶜ7there♥ら"
🐱, h, u, s, x, k, e, e = 11, 12, 13, 14, 15, 16, 17, 17
t(stat(band()))
-- this one comment, i do want!
t()
c = 0
l = 0
l = 0
print "this is included"
?"#[disable[[this for now/ever]]]"
local e = {1, 2, 3}
print(#e)
print(#[[#include notaninclude
]])
local e, l = "preserved_key", {preserved_key = 123}
?l[e]
local e = "preserved_glob"
preserved_glob = 123
?_ENV[e]
local e = {}
e["whatever"] = 123
?e.whatever

function e.subfunc()
end

function e:subfunc()
end

?e:subfunc()
local e, l = "c", {c = 123}
?l[e]
local e, l = split "e,l,i,123", {e = 123, l = 234, i = 345}
?l[e[2]]
local e = "o"
o = 123
?_ENV[e]
local e = "e:l#~~i,", "!t$h+123-u\nif\ns"
do
  local _ENV = {assert = assert}
  assert(true)
end
for _ENV in all {{o = 1}, {o = 2}} do
  o += 1
end

function some_future_pico8_api()
end

some_future_pico8_api(1, 2, 3)
local e = {preserved1 = 1, preserved2 = 2}
e.preserved1 += 1
?e["preserved1"]
e = setmetatable({preserved3 = 3}, f)
?e["preserved3"]
n = {preserved1 = 1, preserved2 = 2}
n.preserved1 += 1
?n["preserved1"]
n = setmetatable({preserved3 = 3}, f)
?n["preserved3"]
local e = {assert = assert, add = add}
do
  local _ENV = e
  assert(add({}, 1) == 1)
end
do
  local _ENV = {assert = assert, add = add}
  assert(add({}, 1) == 1)
end
local e
for _ENV in all {{o = 1, f = 5}, {o = 2, f = 6}} do
  o += f + f * o
  e = deli {2}
end
assert(e == 2)
local e = {key1 = 1, key2 = 2, r = 3}
e.key1 = e.r
while 1 == 0 do
end
while 1 == 0 do
  sin = cos
  cos = sin
end
if 1 == 2 then
end
if 1 == 2 then
  sin = cos
  cos = sin
end
local e = {1}, {1, 2, 3, 4}
local e, l = 1 ~= 2, 1, 1.2345, 4660, 4660.33777, -1, -1.2345, -4660.33777, 32776, 0xf000.f, -39322, -65535.99999
local l = "hi", "hello", '"hi"', "'hello'", '"hi"', "'hi'", "", "", "a\nb", "\\", "\0¹²³⁴⁵⁶", "¹²³⁴⁵⁶⁷", "\\\\\\\\\\\\", "\n\n\n\n\n\n", "¹²³⁴⁵⁶]]"
local l = [[]], [[hi]], [['hi']], [["'hi'"]], [["""""'''''hi'''''"""""]], [[♥♥♥♥]], [[]], [[

]], [==[\\\\\\\\\

]]]=]]===]]==]
local l = -256, -256 * 4, 65280 ^ 4, -65280, ~65280
if not e then
  e = -1
end

function i(...)
  return 1.2 .. 4 .. ... .. 0
end

?i(3)
?1 or 1 or 2 and 3 == 4 >= 4 | 5 ~ 6 << 1 >>< 1 .. 2 .. 3 - -1 ^ 4 ^ 1 / 1 & 7
?((~(((((((tonum(((3 or 4) and 5) ~= 2) | 1) ~ 2) & 3) >> 1) .. 1) - (1 + 3)) * 3)) ^ 2) ^ 1
local e = ({})[1], (function()
end)()
local l, n, o, e, f = sin(1, 2), cos((cos())), (cos((cos()))), {d = ord, a = pal}
local e = ord "123", pal {1, 2}, e:d("ord"), e:a({1, 2}), sin(1)
local i = {ord "1", [2] = 3, o = 4, (ord "1")}
e += 1
l, n = sin(1, 2), cos((cos()))
o, f = (cos((cos())))

function r()
  return 1, 2, ord "1", (ord "1")
end

if 1 == 2 then
elseif 1 == 2 then
else
end
while 1 == 2 do
end
repeat
until 1 == 1
for e in (all {}) do
end
print("test" .. @16 .. "str")
?e + (({})[1] and ({}).x or ... or r()) + 3 + -3
if true then
  ?"sh1"
end
if true then
  ?"sh2"
end
if true then
  if false then
  else
    print "sh3"
  end
end
if true then
  if false then
  else
    print "sh4"
  end
end
j = "renaming bug"

function d()
  local e, l, n, o, f, i, c, r, d, a, t, h, u, s, x, k, y, v, p, b, w, g, _, m, E, N, D
  return j
end

?d()
c = 0
c = 1

function new_name(new_name, e)
  return new_name.new_member, e.new_member
end

function new_name(new_name2, e, l)
  local e, l
  return new_name2.new_member
end

function a(l, e, f, n, o, i)
  return l + e + f + n + o + i
end

?a(1, 2, 4, 8, 16, 32)
y = ?"END!"

