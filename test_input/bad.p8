__lua__

-- undef
function f0()
  band(u, v)
  x, y, t = 1, 2, 3
  function f1() end
  local function f12() end
end
function f2()
  return t()
end
function f2d1()
  function band() end
end
local this_is_ok = bor
function bor() return this_is_ok() end

-- unused
function fx()
  local a, b, c = 3, 4, 5
  b = 6; b += 7; b <<= 2
  c = 6; c += 7; c <<= 2; print(c)
end
function ff(d,e,f)
  d = 1
end

-- dups
g_a = 3
local uu = 1
function f3()
  local z, g_a, uu = 4, 4
  for i=1,10 do
  for i=1,5 do
    local i = 3
    local function finner(z)
    end
  end
  end
end

