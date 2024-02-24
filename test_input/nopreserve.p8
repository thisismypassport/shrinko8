__lua__
-- semi-automatic pico8 global renaming
circfill, rectfill = --[[preserve]]circfill, --[[preserve]]rectfill
--[[preserve]]circfill, --[[preserve]]rectfill = nil
circfill(120,126,3); circfill(126,120,3)
rectfill(120,120,123,123); rectfill(123,123,126,126)
printh("yep")