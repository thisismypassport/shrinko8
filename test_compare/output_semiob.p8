pico-8 cartridge // http://www.pico-8.com
version 41
__lua__
print=printh 
?"hello ᶜ7there♥ら"
🐱,d,r,h,s,u,n,n=11,12,13,14,15,16,17,17

t(stat(band()))


t()



l=0 o=0
o=0

print"this is included"
?"#[disable[[this for now/ever]]]"
local n={1,2,3}
print(
#n
)
print(
#[[#include notaninclude
]]
)

local n,o = "preserved_key",{preserved_key=123}
?o[n] 
local n = "preserved_glob"
preserved_glob = 123
?_ENV[n] 
local n = {}
n["whatever"] = 123
?n.whatever 
function n.subfunc() end
function n:subfunc() end
?n:subfunc()

local n,o = "key",{key=123}
?o[n]

local n,o = split "key1,key2,key3,123",{key1=123,key2=234,key3=345}
?o[n[2]]

local n = "f"
f = 123
?_ENV[n]

local n = "key1:key2#~~key3,", "!key1_still$key2█ア+123-key123\nif\nif◝"

do
  local _ENV = { assert=assert}
  assert(true)
end
for _ENV in all{{x=1}, {x=2}} do
  x += 1
end
function some_future_pico8_api() end
some_future_pico8_api(1,2,3)

local n = {preserved1=1, preserved2=2}
n.preserved1 += 1
?n["preserved1"]
n = setmetatable( {preserved3=3}, i)
?n["preserved3"]

e = {preserved1=1, preserved2=2}
e.preserved1 += 1
?e["preserved1"]
e = setmetatable( {preserved3=3}, i)
?e["preserved3"]

local e = {assert=assert, add=add}
do
  local _ENV = e
  assert(add({}, 1) == 1)
end
do
  local _ENV = {assert=assert, add=add}
  assert(add({}, 1) == 1)
end

local e
for _ENV in all{{x=1,y=5}, {x=2,y=6}} do
  x += y + y*x
  e = deli{2} 
end
assert(e == 2) 
local e = {key1=1,key2=2, other=3}
e.key1 = e. other

circfill, rectfill = circfill, rectfill
circfill(120,126,3) circfill(126,120,3)
rectfill(120,120,123,123) rectfill(123,123,126,126)

while (1==0);
while (1==0) sin=cos cos=sin
if (1 == 2);
if (1 == 2) sin=cos cos=sin
local e = {1}, {1,2,3,4}

local e,n = 1 ~= 2,1,1.2345,4660,4660.33777,-1,-1.2345,-4660.33777,32776,0xf000.f,-39322,-65535.99999
local n = "hi", "hello", '"hi"', "'hello'", '"hi"', "'hi'", "", "", "a\nb", "\\", "\0¹²³⁴⁵⁶", "¹²³⁴⁵⁶⁷", "\\\\\\\\\\\\", "\n\n\n\n\n\n", "¹²³⁴⁵⁶]]"
local n = [[]], [[hi]], [['hi']], [["'hi'"]], [["""""'''''hi'''''"""""]], [[♥♥♥♥]], [[]], [[

]]
local n = -256, -256*4, 65280^4, -65280, ~65280
if (not e) e = -1

?1 or 1 or 2 and 3 == 4 >= 4 | 5 ~ 6 << 1 >>< 1 .. 2 .. 3 - -1^4^1 / 1 & 7
?((~(((((((tonum(((3 or 4) and 5) ~= 2) | 1) ~ 2) & 3) >> 1) .. 1) - (1 + 3)) * 3)) ^ 2) ^ 1
local e = ({})[1], (function()end)()
local n, o,f,e,i = sin(1,2), cos((cos())),(cos((cos()))),{ord=ord,pal=pal}
local e = ord"123", pal{1,2}, e:ord("ord"), e:pal({1,2}), sin(1)
local d = {ord"1",[2]=3,x=4,(ord"1")}
e += 1
n, o = sin(1,2), cos((cos()))
f, i = (cos((cos())))
function x() return 1, 2, ord"1", (ord"1") end
if 1 == 2 then elseif 1 == 2 then else end
while 1 == 2 do end
repeat until 1 == 1
for e in (all{}) do end
print("test"..@16 .."str")

if(true) ?"sh1"
if true then ?"sh2"
end
if(true) if false then else print"sh3" end
if true then if false then else print"sh4" end end

c="renaming bug"
function a()
  local e,l,n,o,f,i,a,d,r,t,h,s,u,x,k,y,v,p,b,w,g,m,E,N,D,j,q
  return c
end
?a()
l=0l=1

k=?"END!"