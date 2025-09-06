__lua__

--deflanguage: bigsplit = split (global.members)=(members.strings)s

g_goo = {sun=1,moon=2,mars=3}
unrelated = {spot=-1}
bigsplit--[[language::bigsplit]]"g_goo.sun.moon.mars=sun.spot.moon.top.mars.stop"
bigsplit--[[language::bigsplit]]"g_goo=sun.frost.mars==moon=mars.frost"

minisplit--[[language::split (member=string)s,]]"sun=soon,moon=loon,mars=toon"
minisplit--[[language::split global\((member\wq(global\\member))]]"unrelated(marsqunrelated\\mars"
