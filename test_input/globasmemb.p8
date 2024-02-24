__lua__
_ENV = setmetatable({print=1, bob=2}, {__index=_ENV})
assert(print + bob == 3, 1)
charlie = _ENV
assert(charlie.bob == 2, 2)
printh("OK")
--preserve: *=*.*