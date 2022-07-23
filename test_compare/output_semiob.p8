__lua__

?"hello ᶜ7there♥ら"


t(inext(band()))


print("this is included")?"$[disable[[this for now/ever]]]"


local e = "preserved_key"
local o = {preserved_key=123}
?o[e] 

local e = "preserved_glob"
preserved_glob = 123
?_ENV[e] 

local e = {}
e["whatever"] = 123
?e.whatever 
local e = "key"
local o = {key=123}
?o[e]

local e = split "key1,key2,key3"
local o = {key1=123,key2=234,key3=345}
?o[e[2]]

local e = "l"
l = 123
?_ENV[e]


do
  local _ENV = { assert=assert}
  assert(true)
end
for _ENV in all({{x=1}, {x=2}}) do
  x += 1
end
some_future_pico8_api(1,2,3)


circfill, rectfill = circfill, rectfill
circfill(10,10,20); circfill(90,90,30)
rectfill(0,0,100,100); rectfill(20,20,40,40)
