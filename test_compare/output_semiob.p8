__lua__

?"hello ᶜ7there♥ら"


t(stat(band()))


print"this is included"?"$[disable[[this for now/ever]]]"


local c = "preserved_key"
local d = {preserved_key=123}
?d[c] 

local c = "preserved_glob"
preserved_glob = 123
?_ENV[c] 

local c = {}
c["whatever"] = 123
?c.whatever 
function c.subfunc() end
function c:subfunc() end
?c:subfunc()


local c = "key"
local d = {key=123}
?d[c]

local c = split "key1,key2,key3"
local d = {key1=123,key2=234,key3=345}
?d[c[2]]

local c = "e"
e = 123
?_ENV[c]


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
e = setmetatable( {preserved3=3}, o)
?e["preserved3"]

l = {preserved1=1, preserved2=2}
l.preserved1 += 1
?l["preserved1"]
l = setmetatable( {preserved3=3}, o)
?l["preserved3"]

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
local l = {1}, {1,2,3,4}


?1 or 1 or 2 and 3 == 4 >= 4 | 5 ^^ 6 << 1 >>< 1 .. 2 .. 3 - -1^4^1 / 1 & 7
?((~(((((((tonum(((3 or 4) and 5) ~= 2) | 1) ^^ 2) & 3) >> 1) .. 1) - (1 + 3)) * 3)) ^ 2) ^ 1
local l = ({})[1], (function()end)()
local l, e = sin(1,2), cos((cos()))
local l, e = (cos((cos())))
local l = {ord=ord, pal=pal}
local e = ord"123", pal{1,2}, l:ord("ord"), l:pal({1,2}), sin(1)
