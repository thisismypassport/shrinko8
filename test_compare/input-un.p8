pico-8 cartridge // http://www.pico-8.com
version 41
__lua__

print = printh
?"hello ᶜ7there♥ら"
🐱, d, r, h, s, u, n, n = 11, 12, 13, 14, 15, 16, 17, 17
t(stat(band()))
t()
l = 0
o = 0
o = 0
print "this is included"
?"#[disable[[this for now/ever]]]"
local n = {1, 2, 3}
print(#n)
print(#[[#include notaninclude
]])
local n = "preserved_key"
local o = {preserved_key = 123}
?o[n]
local n = "preserved_glob"
preserved_glob = 123
?_ENV[n]
local n = {}
n["whatever"] = 123
?n.whatever

function n.subfunc()
end

function n:subfunc()
end

?n:subfunc()
local n = "c"
local o = {c = 123}
?o[n]
local n = split "o,f,i,123"
local o = {o = 123, f = 234, i = 345}
?o[n[2]]
local n = "f"
f = 123
?_ENV[n]
local n = "o:f#~~i,", "!t$h+123-s\nif\nu"
do
  local _ENV = {assert = assert}
  assert(true)
end
for _ENV in all {{e = 1}, {e = 2}} do
  e += 1
end

function some_future_pico8_api()
end

some_future_pico8_api(1, 2, 3)
local n = {preserved1 = 1, preserved2 = 2}
n.preserved1 += 1
?n["preserved1"]
n = setmetatable({preserved3 = 3}, i)
?n["preserved3"]
e = {preserved1 = 1, preserved2 = 2}
e.preserved1 += 1
?e["preserved1"]
e = setmetatable({preserved3 = 3}, i)
?e["preserved3"]
local n = {assert = assert, add = add}
do
  local _ENV = n
  assert(add({}, 1) == 1)
end
do
  local _ENV = {assert = assert, add = add}
  assert(add({}, 1) == 1)
end
local n
for _ENV in all {{e = 1, l = 5}, {e = 2, l = 6}} do
  e += l + l * e
  n = deli {2}
end
assert(n == 2)
local e = {key1 = 1, key2 = 2, a = 3}
e.key1 = e.a
circfill, rectfill = circfill, rectfill
circfill(120, 126, 3)
circfill(126, 120, 3)
rectfill(120, 120, 123, 123)
rectfill(123, 123, 126, 126)
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
local e = 1 ~= 2
local n = 1, 1.2345, 4660, 4660.33777, -1, -1.2345, -4660.33777, 32776, 0xf000.f, -39322, -65535.99999
local n = "hi", "hello", '"hi"', "'hello'", '"hi"', "'hi'", "", "", "a\nb", "\\", "\0¹²³⁴⁵⁶", "¹²³⁴⁵⁶⁷", "\\\\\\\\\\\\", "\n\n\n\n\n\n", "¹²³⁴⁵⁶]]"
local n = [[]], [[hi]], [['hi']], [["'hi'"]], [["""""'''''hi'''''"""""]], [[♥♥♥♥]], [[]], [[

]]
local n = -256, -256 * 4, 65280 ^ 4, -65280, ~65280
if not e then
  e = -1
end
?1 or 1 or 2 and 3 == 4 >= 4 | 5 ~ 6 << 1 >>< 1 .. 2 .. 3 - -1 ^ 4 ^ 1 / 1 & 7
?((~(((((((tonum(((3 or 4) and 5) ~= 2) | 1) ~ 2) & 3) >> 1) .. 1) - (1 + 3)) * 3)) ^ 2) ^ 1
local e = ({})[1], (function()
end)()
local n, o = sin(1, 2), cos((cos()))
local f, i = (cos((cos())))
local e = {d = ord, r = pal}
local e = ord "123", pal {1, 2}, e:d("ord"), e:r({1, 2}), sin(1)
local d = {ord "1", [2] = 3, e = 4, (ord "1")}
e += 1
n, o = sin(1, 2), cos((cos()))
f, i = (cos((cos())))

function x()
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
c = "renaming bug"

function a()
  local e, l, n, o, f, i, a, d, r, t, h, s, u, x, k, y, v, p, b, w, g, m, E, N, D, j, q
  return c
end

?a()
l = 0
l = 1
?"END!"
