__lua__

?"hello ᶜ7there♥ら"


t(stat(band()))


print("this is included")?"$[disable[[this for now/ever]]]"


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
for _ENV in all({{x=1}, {x=2}}) do
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

for _ENV in all({{x=1,y=5}, {x=2,y=6}}) do
  x += y + y*x
end


local e = {key1=1,key2=2, other=3}
e.key1 = e. other


circfill, rectfill = circfill, rectfill
circfill(120,126,3); circfill(126,120,3)
rectfill(120,120,123,123); rectfill(123,123,126,126)
