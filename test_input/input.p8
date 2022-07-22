__lua__
-- special characters
?"hello ᶜ7there♥ら"

-- various globals
t(inext(band()))

-- include
#include included.lua
?"$[disable[[this for now/ever]]]"

-- preserve
local my_key = "preserved_key"
local my_obj = {preserved_key=123}
?my_obj[my_key] -- requires preserve of '*.preserved_key'

local my_key = "preserved_glob"
preserved_glob = 123
?_ENV[my_key] -- requires preserve of 'preserved_glob'

local preserving_obj = {}
preserving_obj["whatever"] = 123
?preserving_obj.whatever -- requires preserve of 'preserving_obj.*'

-- member/global on string
local my_key = --[[member]]"key"
local my_obj = {key=123}
?my_obj[my_key]

local my_keys = split --[[member]]"key1,key2,key3"
local my_obj = {key1=123,key2=234,key3=345}
?my_obj[my_keys[2]]

local my_key = --[[global]]"glob"
glob = 123
?_ENV[my_key]

-- member/global on identifier
do
  local _ENV = {--[[global]]assert=assert}
  assert(true)
end
for _ENV in all({{x=1}, {x=2}}) do
  --[[member]]x += 1
end
--[[preserve]]some_future_pico8_api(1,2,3)

-- semi-automatic pico8 global renaming
circfill, rectfill = --[[preserve]]circfill, --[[preserve]]rectfill
circfill(10,10,20); circfill(90,90,30)
rectfill(0,0,100,100); rectfill(20,20,40,40)
