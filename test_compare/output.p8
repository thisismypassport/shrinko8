__lua__
?"hello ᶜ7there♥ら"
t(inext(band()))
print("this is included")?"$[disable[[this for now/ever]]]"
local a="preserved_key"local c={preserved_key=123}
?c[a]
local a="preserved_glob"preserved_glob=123
?_ENV[a]
local a={}a["whatever"]=123
?a.whatever
local a="e"local c={e=123}
?c[a]
local a=split"o,a,c"local c={o=123,a=234,c=345}
?c[a[2]]
local a="o"o=123
?_ENV[a]
do local _ENV={assert=assert}assert(true)end for _ENV in all({{l=1},{l=2}})do l+=1end some_future_pico8_api(1,2,3)l,e=circfill,rectfill l(10,10,20)l(90,90,30)e(0,0,100,100)e(20,20,40,40)