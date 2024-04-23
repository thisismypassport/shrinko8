pico-8 cartridge // http://www.pico-8.com
version 42
__lua__

print = printh
-- note: most of this test is NOT covered in print/printh - check output as well (as always)
-- special characters
?"hello ᶜ7there♥ら"
🐱, あ, ョ, ◝, ゛, ゜, F, F = 11, 12, 13, 14, 15, 16, 17, 17
-- various globals
t(stat(band()))
-- comment removal
--keep: this one comment, i do want!
t()
--[[
  (also, testing comment removal)
]]
x = 0
--[[]]b = 0
--
b = 0
-- include
-- no header needed
print("this is included")
?"#[disable[[this for now/ever]]]"
local include = {1, 2, 3}
print(#include)
print(#[[
#include notaninclude
]])
-- preserve
local my_key = "preserved_key"
local my_obj = {preserved_key = 123}
?my_obj[my_key]
-- requires preserve of '*.preserved_key'
local my_key = "preserved_glob"
preserved_glob = 123
?_ENV[my_key]
-- requires preserve of 'preserved_glob'
local preserving_obj = {}
preserving_obj["whatever"] = 123
?preserving_obj.whatever

-- requires preserve of 'preserving_obj.*'
function preserving_obj.subfunc()
end

function preserving_obj:subfunc()
end

?preserving_obj:subfunc()
-- member/global on string
local my_key = --[[member]]"key"
local my_obj = {key = 123}
?my_obj[my_key]
local my_keys = split --[[member]]"key1,key2,key3,123"
local my_obj = {key1 = 123, key2 = 234, key3 = 345}
?my_obj[my_keys[2]]
local my_key = --[[global]]"glob"
glob = 123
?_ENV[my_key]
local custom_splits = --[[member]]"key1:key2#~~key3,", --[[member]]"!key1_still$key2\x80\xcc+123-key123\nif\nif\xff"
-- member/global/preserve on identifier
do
    local _ENV = {--[[global]]assert = assert}
    assert(true)
end
for _ENV in all({{x = 1}, {x = 2}}) do
    --[[member]]x += 1
end

function --[[preserve]]some_future_pico8_api()
end

--[[preserve]]some_future_pico8_api(1, 2, 3)
-- global/preserve-keys
local --[[preserve-keys]]my_table = {preserved1 = 1, preserved2 = 2}
my_table.preserved1 += 1
?my_table["preserved1"]
my_table = setmetatable(--[[preserve-keys]]{preserved3 = 3}, my_meta)
?my_table["preserved3"]
--[[preserve-keys]]g_my_table = {preserved1 = 1, preserved2 = 2}
g_my_table.preserved1 += 1
?g_my_table["preserved1"]
g_my_table = setmetatable(--[[preserve-keys]]{preserved3 = 3}, my_meta)
?g_my_table["preserved3"]
local env = --[[global-keys]]{assert = assert, add = add}
do
    local _ENV = env
    assert(add({}, 1) == 1)
end
do
    local _ENV = {assert = assert, add = add}
    assert(add({}, 1) == 1)
end
local deli_result
for --[[member-keys]]_ENV in all({{x = 1, y = 5}, {x = 2, y = 6}}) do
    x += y + y * x
    deli_result = deli({2})
-- works due to top-level locals added by pico8
end
assert(deli_result == 2)
-- (but assert wouldn't work inside)
-- overrides
local --[[preserve-keys]]thing = {key1 = 1, key2 = 2, --[[member]]other = 3}
thing.key1 = thing.--[[member]]other
-- punct removal
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
local tbls = {1,}, {1; 2, 3; 4;}
-- token replacement
local nothing = 1 != 2
local nums = 1, 1.2345, 0x1234, 0x1234.5678, -1, -1.2345, -0x1234.5678, 0x8008, 0xf000.f000, -0x999a, -0xffff.ffff
local strs = "hi", 'hello', '"hi"', "'hello'", "\"hi\"", '\'hi\'', "", '', "a\nb", "\\", "\0\1\2\3\4\5\6", "\1\2\3\4\5\6\7", "\\\\\\\\\\\\", "\n\n\n\n\n\n", "\1\2\3\4\5\6]]"
local strs2 = [[]], [[hi]], [['hi']], [["'hi'"]], [["""""'''''hi'''''"""""]], [[♥♥♥♥]], [[
]], [[

]], [==[\\\\\\\\\

]]]=]]===]]==]
local numbug = 0xff00, 0xff00 * 4, 0xff00 ^ 4, -0xff00, ~0xff00
if not nothing then
    nothing = 0xffff
end

function tokenhell(...)
    return 1.2 .. 4 .. ... .. 0
end

?tokenhell(3)
-- paren removal
?(((1 or 1) or (2 and ((3 == 4) >= (4 | (5 ^^ (((6 << 1) >>< (1 .. (2 .. (3 - ((-(1 ^ (4 ^ 1))) / 1))))) & 7)))))))
?((~(((((((tonum(((3 or 4) and 5) != 2) | 1) ^^ 2) & 3) >> 1) .. 1) - (1 + 3)) * 3)) ^ 2) ^ 1
local prefix = ({})[1], (function()
end)()
local calls1, calls2 = (sin((1), (2))), (cos((cos())))
local calls1_, calls2_ = (cos((cos())))
local obj = {ord = ord, pal = pal}
local calls3 = ord("123"), pal({1, 2}), obj:ord("ord"), obj:pal({1, 2}), sin(1)
local moretests = {(ord("1")), [(2)] = (3), x = (4), (ord("1"))}
calls3 += (1)
calls1, calls2 = (sin((1), (2))), (cos((cos())))
calls1_, calls2_ = (cos((cos())))

function xxx()
    return (1), (2), (ord("1")), (ord("1"))
end

if (1 == 2) then
elseif (1 == 2) then
else
end
while (1 == 2) do
end
repeat
until (1 == 1)
for a in (all({})) do
end
print("test" .. (@16) .. "str")
?(calls3) + ((({})[1]) and (({}).🐱) or (...) or (xxx())) + (3) + (-3)
-- shorthands
if true then
    ?"sh1"
end
if true then
    ?"sh2"
end
if true then
    if false then
    else
        print("sh3")
    end
end
if true then
    if false then
    else
        print("sh4")
    end
end
-- renaming bugs
l = "renaming bug"

function fff()
    local l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13, l14, l15, l16, l17, l18, l19, l10, l20, l21, l22, l23, l24, l25, l26
    return l
end

?fff()
x = 0.
x = 1

-- explicit rename
function --[[rename::new_name]]old_name(old_param, do_rename_this)
    return --[[rename::new_name]]old_param.old_member, do_rename_this.old_member
end

function old_name(--[[rename::new_name2]]old_param, do_rename_this, do_rename_that)
    local more_things_to_rename, and_so_on
    return old_param.--[[rename::new_member]]old_member
end

function ggg(--[[rename::l]]p1, --[[rename::e]]p2, --[[rename::f]]p3, p4, p5, p6)
    return p1 + p2 + p3 + p4 + p5 + p6
end

?ggg(1, 2, 4, 8, 16, 32)
done = ?"END!"

