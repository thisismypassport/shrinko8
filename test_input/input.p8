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

-- nameof/memberof
local my_key = --[[memberof]]"key"
local my_obj = {key=123}
?my_obj[my_key]

local my_keys = split --[[memberof]]"key1,key2,key3"
local my_obj = {key1=123,key2=234,key3=345}
?my_obj[my_keys[2]]

local my_key = --[[nameof]]"glob"
glob = 123
?_ENV[my_key]
