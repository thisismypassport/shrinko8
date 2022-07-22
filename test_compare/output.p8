__lua__
?"hello ᶜ7there♥ら"
t(inext(band()))
print("this is included")?"$[disable[[this for now/ever]]]"
local e="preserved_key"local o={preserved_key=123}
?o[e]
local e="preserved_glob"preserved_glob=123
?_ENV[e]
local e={}e["whatever"]=123
?e.whatever
local e="e"local o={e=123}
?o[e]
local e=split"o,a,c"local o={o=123,a=234,c=345}
?o[e[2]]
local e="l"l=123
?_ENV[e]
do local _ENV={assert=assert}assert(true)end for _ENV in all({{l=1},{l=2}})do l+=1end some_future_pico8_api(1,2,3)