__lua__


-- the consts check for a fixed bug where they'd eat the hint
--[[const]] a = 123
--preserve: *=*.*
--[[const]] b = 456
_ENV = setmetatable({print=1, bob=2}, {__index=_ENV})
assert(print + bob == 3, 1)
charlie = _ENV
assert(charlie.bob == 2, 2)
printh("OK")