__lua__
--[[const]] SPEED = 0.5 -- default value
if DEBUG then
  ?'debug version ' .. (VERSION or '???')
end
hero = 0
function _update()
  hero += SPEED/2
  ?hero
end