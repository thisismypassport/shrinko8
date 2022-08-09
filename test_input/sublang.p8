__lua__
g_some_global = 123
function eval() end
eval--[[language::evally]][[
    circfill 50 50 20 7
    g_another_glob <- pack
    rawset g_another_glob .some_member g_some_global
    rawset g_another_glob .another_member g_same_global
]]
print(g_another_glob)
print(g_another_glob.some_member)
eval--[[language::empty]]""
