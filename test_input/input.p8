__lua__
-- special characters
?"hello ᶜ7there♥ら"

-- various globals
t(stat(band()))

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
function preserving_obj.subfunc() end
function preserving_obj:subfunc() end
?preserving_obj:subfunc()

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

-- member/global/preserve on identifier
do
  local _ENV = {--[[global]]assert=assert}
  assert(true)
end
for _ENV in all({{x=1}, {x=2}}) do
  --[[member]]x += 1
end
function --[[preserve]]some_future_pico8_api() end
--[[preserve]]some_future_pico8_api(1,2,3)

-- global/preserve-keys
local --[[preserve-keys]]my_table = {preserved1=1, preserved2=2}
my_table.preserved1 += 1
?my_table["preserved1"]
my_table = setmetatable(--[[preserve-keys]]{preserved3=3}, my_meta)
?my_table["preserved3"]

--[[preserve-keys]]g_my_table = {preserved1=1, preserved2=2}
g_my_table.preserved1 += 1
?g_my_table["preserved1"]
g_my_table = setmetatable(--[[preserve-keys]]{preserved3=3}, my_meta)
?g_my_table["preserved3"]

do
  local _ENV = --[[global-keys]]{assert=assert, add=add}
  assert(add({}, 1) == 1)
end

for --[[member-keys]]_ENV in all({{x=1,y=5}, {x=2,y=6}}) do
  x += y + y*x
end

-- overrides
local --[[preserve-keys]]thing = {key1=1,key2=2,--[[member]]other=3}
thing.key1 = thing.--[[member]]other

-- semi-automatic pico8 global renaming
circfill, rectfill = --[[preserve]]circfill, --[[preserve]]rectfill
circfill(120,126,3); circfill(126,120,3)
rectfill(120,120,123,123); rectfill(123,123,126,126)
