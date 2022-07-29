__lua__

?"hello ᶜ7there♥ら"


t(stat(band()))


print"this is included"
?"#[disable[[this for now/ever]]]"
local d={1,2,3}
print(
#d
)


local d = "preserved_key"
local r = {preserved_key=123}
?r[d] 

local d = "preserved_glob"
preserved_glob = 123
?_ENV[d] 

local d = {}
d["whatever"] = 123
?d.whatever 
function d.subfunc() end
function d:subfunc() end
?d:subfunc()


local d = "key"
local r = {key=123}
?r[d]

local d = split "key1,key2,key3"
local r = {key1=123,key2=234,key3=345}
?r[d[2]]

local d = "l"
l = 123
?_ENV[d]


do
  local _ENV = { assert=assert}
  assert(true)
end
for _ENV in all{{x=1}, {x=2}} do
  x += 1
end
function some_future_pico8_api() end
some_future_pico8_api(1,2,3)


local l = {preserved1=1, preserved2=2}
l.preserved1 += 1
?l["preserved1"]
l = setmetatable( {preserved3=3}, o)
?l["preserved3"]

e = {preserved1=1, preserved2=2}
e.preserved1 += 1
?e["preserved1"]
e = setmetatable( {preserved3=3}, o)
?e["preserved3"]

do
  local _ENV = {assert=assert, add=add}
  assert(add({}, 1) == 1)
end

for _ENV in all{{x=1,y=5}, {x=2,y=6}} do
  x += y + y*x
end


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


?1 or 1 or 2 and 3 == 4 >= 4 | 5 ^^ 6 << 1 >>< 1 .. 2 .. 3 - -1^4^1 / 1 & 7
?((~(((((((tonum(((3 or 4) and 5) ~= 2) | 1) ^^ 2) & 3) >> 1) .. 1) - (1 + 3)) * 3)) ^ 2) ^ 1
local e = ({})[1], (function()end)()
local l, o = sin(1,2), cos((cos()))
local d, r = (cos((cos())))
local e = {ord=ord, pal=pal}
local c = ord"123", pal{1,2}, e:ord("ord"), e:pal({1,2}), sin(1)
local e = {ord"1",[2]=3,x=4,(ord"1")}
c += 1
l, o = sin(1,2), cos((cos()))
d, r = (cos((cos())))
function n() return 1, 2, ord"1", (ord"1") end
if 1 == 2 then elseif 1 == 2 then else end
while 1 == 2 do end
repeat until 1 == 1
for e in (pairs{}) do end
