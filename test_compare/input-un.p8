pico-8 cartridge // http://www.pico-8.com
version 41
__lua__

print = printh
?"hello ᶜ7there♥ら"
🐱, d, r, h, x, s, o, o = 11, 12, 13, 14, 15, 16, 17, 17
t(stat(band()))
t()
e = 0
n = 0
n = 0
print "this is included"
?"#[disable[[this for now/ever]]]"
local o = {1, 2, 3}
print(#o)
print(#[[#include notaninclude
]])
local o = "preserved_key"
local n = {preserved_key = 123}
?n[o]
local o = "preserved_glob"
preserved_glob = 123
?_ENV[o]
local o = {}
o["whatever"] = 123
?o.whatever

function o.subfunc()
end

function o:subfunc()
end

?o:subfunc()
local o = "a"
local n = {a = 123}
?n[o]
local o = split "o,f,c,123"
local n = {o = 123, f = 234, c = 345}
?n[o[2]]
local o = "f"
f = 123
?_ENV[o]
local o = "o:f#~~c,", "!t$h+123-x\nif\ns"
do
  local _ENV = {assert = assert}
  assert(true)
end
for _ENV in all {{l = 1}, {l = 2}} do
  l += 1
end

function some_future_pico8_api()
end

some_future_pico8_api(1, 2, 3)
local o = {preserved1 = 1, preserved2 = 2}
o.preserved1 += 1
?o["preserved1"]
o = setmetatable({preserved3 = 3}, c)
?o["preserved3"]
l = {preserved1 = 1, preserved2 = 2}
l.preserved1 += 1
?l["preserved1"]
l = setmetatable({preserved3 = 3}, c)
?l["preserved3"]
local o = {assert = assert, add = add}
do
  local _ENV = o
  assert(add({}, 1) == 1)
end
do
  local _ENV = {assert = assert, add = add}
  assert(add({}, 1) == 1)
end
local o
for _ENV in all {{l = 1, e = 5}, {l = 2, e = 6}} do
  l += e + e * l
  o = deli {2}
end
assert(o == 2)
local l = {key1 = 1, key2 = 2, i = 3}
l.key1 = l.i
circfill, rectfill = circfill, rectfill
circfill(120, 126, 3)
circfill(126, 120, 3)
rectfill(120, 120, 123, 123)
rectfill(123, 123, 126, 126)
while (1 == 0) ;
while (1 == 0) sin = cos; cos = sin
if (1 == 2) ;
if (1 == 2) sin = cos; cos = sin
local l = {1}, {1, 2, 3, 4}
local l = 1 ~= 2
local o = 1, 1.2345, 4660, 4660.33777, -1, -1.2345, -4660.33777, 32776, 0xf000.f, -39322, -65535.99999
local o = "hi", "hello", '"hi"', "'hello'", '"hi"', "'hi'", "", "", "a\nb", "\\", "\0¹²³⁴⁵⁶", "¹²³⁴⁵⁶⁷", "\\\\\\\\\\\\", "\n\n\n\n\n\n", "¹²³⁴⁵⁶]]"
local o = [[]], [[hi]], [['hi']], [["'hi'"]], [["""""'''''hi'''''"""""]], [[♥♥♥♥]], [[]], [[

]]
local o = -256, -256 * 4, 65280 ^ 4, -65280, ~65280
if (not l) l = -1
?1 or 1 or 2 and 3 == 4 >= 4 | 5 ~ 6 << 1 >>< 1 .. 2 .. 3 - -1 ^ 4 ^ 1 / 1 & 7
?((~(((((((tonum(((3 or 4) and 5) ~= 2) | 1) ~ 2) & 3) >> 1) .. 1) - (1 + 3)) * 3)) ^ 2) ^ 1
local l = ({})[1], (function()
end)()
local o, n = sin(1, 2), cos((cos()))
local f, c = (cos((cos())))
local l = {d = ord, r = pal}
local l = ord "123", pal {1, 2}, l:d("ord"), l:r({1, 2}), sin(1)
local d = {ord "1", [2] = 3, l = 4, (ord "1")}
l += 1
o, n = sin(1, 2), cos((cos()))
f, c = (cos((cos())))

function u()
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
for l in (all {}) do
end
print("test" .. @16 .. "str")
a = "renaming bug"

function i()
  local l, e, o, n, f, c, i, d, r, t, h, x, s, u, k, y, v, p, b, w, g, m, j, q, z, A, B
  return a
end

?i()
e = 0
e = 1
