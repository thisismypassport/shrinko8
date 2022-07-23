__lua__
?"hello ᶜ7there♥ら"
t(stat(band()))
print("this is included")?"$[disable[[this for now/ever]]]"
local n="preserved_key"local c={preserved_key=123}
?c[n]
local n="preserved_glob"preserved_glob=123
?_ENV[n]
local n={}n["whatever"]=123
?n.whatever
function n.subfunc()end function n:subfunc()end
?n:subfunc()
local n="o"local c={o=123}
?c[n]
local n=split"d,r,c"local c={d=123,r=234,c=345}
?c[n[2]]
local n="d"d=123
?_ENV[n]
do local _ENV={assert=assert}assert(true)end for _ENV in all({{e=1},{e=2}})do e+=1end function some_future_pico8_api()end some_future_pico8_api(1,2,3)local d={preserved1=1,preserved2=2}d.preserved1+=1
?d["preserved1"]
d=setmetatable({preserved3=3},r)
?d["preserved3"]
e={preserved1=1,preserved2=2}e.preserved1+=1
?e["preserved1"]
e=setmetatable({preserved3=3},r)
?e["preserved3"]
do local _ENV={assert=assert,add=add}assert(add({},1)==1)end for _ENV in all({{e=1,l=5},{e=2,l=6}})do e+=l+l*e end local e={key1=1,key2=2,a=3}e.key1=e.a l,o=circfill,rectfill l(120,126,3)l(126,120,3)o(120,120,123,123)o(123,123,126,126)