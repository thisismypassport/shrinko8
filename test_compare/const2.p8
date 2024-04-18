pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
stop() -- for pure syntax check
_ENV["min"]=123
function x()
    ?ssog4
    function max()
    end
    local function min()
    end
    --[[const]] local M,m = max(1,2),min(1,2)
    ?M
    ?m
end
--[[const]] local M = max(1,2)
?M
?1
local M,m = max(1,2),min(1,2)
?M
?m
--[[preserve]]ssog1 = 123; ?ssog1
--[[const]]; ?123
--[[const]]ssog3 = 123; ssog3 += 1; ?ssog3
--[[const]]ssog4 = 4; ?ssog4
--[[const]]ssog5 = ssog5; ?ssog5
--[[const]]ssog6 = 123; --[[const]]ssog6 = 456; ?ssog6
--[[const]] ?2
