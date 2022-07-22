__lua__
?"hello ᶜ7there♥ら"
local b="preserved_key"local c={preserved_key=123}
?c[b]
local b="preserved_glob"preserved_glob=123
?_ENV[b]
local b={}b["whatever"]=123
?b.whatever
local b="a"local c={a=123}
?c[b]
local b=split"b,c,d"local c={b=123,c=234,d=345}
?c[b[2]]
local b="a"a=123
?_ENV[b]