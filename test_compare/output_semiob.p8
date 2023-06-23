pico-8 cartridge // http://www.pico-8.com
version 38
__lua__
print=printh 
?"hello ᶜ7there♥ら"
🐱,i,d,r,h,x,e,e=11,12,13,14,15,16,17,17

t(stat(band()))


t()



s=0 o=0
o=0

print"this is included"
?"#[disable[[this for now/ever]]]"
local e={1,2,3}
print(
#e
)
print(
#[[#include notaninclude
]]
)

local e = "preserved_key"
local o = {preserved_key=123}
?o[e] 
local e = "preserved_glob"
preserved_glob = 123
?_ENV[e] 
local e = {}
e["whatever"] = 123
?e.whatever 
function e.subfunc() end
function e:subfunc() end
?e:subfunc()

local e = "key"
local o = {key=123}
?o[e]

local e = split "key1,key2,key3,123"
local o = {key1=123,key2=234,key3=345}
?o[e[2]]

local e = "n"
n = 123
?_ENV[e]

local e = "key1:key2#~~key3,", "!key1_still$key2█ア+123-key123\nif\nif◝"

do
  local _ENV = { assert=assert}
  assert(true)
end
for _ENV in all{{x=1}, {x=2}} do
  x += 1
end
function some_future_pico8_api() end
some_future_pico8_api(1,2,3)

local e = {preserved1=1, preserved2=2}
e.preserved1 += 1
?e["preserved1"]
e = setmetatable( {preserved3=3}, f)
?e["preserved3"]

l = {preserved1=1, preserved2=2}
l.preserved1 += 1
?l["preserved1"]
l = setmetatable( {preserved3=3}, f)
?l["preserved3"]

local l = {assert=assert, add=add}
do
  local _ENV = l
  assert(add({}, 1) == 1)
end
do
  local _ENV = {assert=assert, add=add}
  assert(add({}, 1) == 1)
end

for _ENV in all{{x=1,y=5}, {x=2,y=6}} do
  x += y + y*x
end

local l = {key1=1,key2=2, other=3}
l.key1 = l. other

circfill, rectfill = circfill, rectfill
circfill(120,126,3) circfill(126,120,3)
rectfill(120,120,123,123) rectfill(123,123,126,126)

while (1==0);
while (1==0) sin=cos cos=sin
if (1 == 2);
if (1 == 2) sin=cos cos=sin
local l = {1}, {1,2,3,4}

local l = 1 ~= 2
local e = 1, 1.2345, 4660, 4660.33777, -1, -1.2345, -4660.33777, 32776, 0xf000.f, -39322, -65535.99999
local e = "hi", "hello", '"hi"', "'hello'", '"hi"', "'hi'", "", "", "a\nb", "\\", "\0¹²³⁴⁵⁶", "¹²³⁴⁵⁶⁷", "\\\\\\\\\\\\", "\n\n\n\n\n\n", "¹²³⁴⁵⁶]]"
local e = [[]], [[hi]], [['hi']], [["'hi'"]], [["""""'''''hi'''''"""""]], [[♥♥♥♥]], [[]], [[

]]
local e = -256, -256*4, 65280^4, -65280, ~65280
if (not l) l = -1

?1 or 1 or 2 and 3 == 4 >= 4 | 5 ~ 6 << 1 >>< 1 .. 2 .. 3 - -1^4^1 / 1 & 7
?((~(((((((tonum(((3 or 4) and 5) ~= 2) | 1) ~ 2) & 3) >> 1) .. 1) - (1 + 3)) * 3)) ^ 2) ^ 1
local l = ({})[1], (function()end)()
local e, o = sin(1,2), cos((cos()))
local n, f = (cos((cos())))
local l = {ord=ord, pal=pal}
local i = ord"123", pal{1,2}, l:ord("ord"), l:pal({1,2}), sin(1)
local l = {ord"1",[2]=3,x=4,(ord"1")}
i += 1
e, o = sin(1,2), cos((cos()))
n, f = (cos((cos())))
function u() return 1, 2, ord"1", (ord"1") end
if 1 == 2 then elseif 1 == 2 then else end
while 1 == 2 do end
repeat until 1 == 1
for l in (all{}) do end
print("test"..@16 .."str")

c="renaming bug"
function a()
  local l,e,o,n,f,a,i,d,r,t,h,x,s,u,k,y,v,p,b,w,g,m,j,q,z,A,B
  return c
end
?a()
