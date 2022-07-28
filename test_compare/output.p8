__lua__
?"hello ᶜ7there♥ら"
t(stat(band()))
print"this is included"?"$[disable[[this for now/ever]]]"
local r="preserved_key"local a={preserved_key=123}
?a[r]
local r="preserved_glob"preserved_glob=123
?_ENV[r]
local r={}r["whatever"]=123
?r.whatever
function r.subfunc()end function r:subfunc()end
?r:subfunc()
local r="o"local a={o=123}
?a[r]
local r=split"c,d,r"local a={c=123,d=234,r=345}
?a[r[2]]
local r="c"c=123
?_ENV[r]
do local _ENV={assert=assert}assert(true)end for _ENV in all{{l=1},{l=2}}do l+=1end function some_future_pico8_api()end some_future_pico8_api(1,2,3)local c={preserved1=1,preserved2=2}c.preserved1+=1
?c["preserved1"]
c=setmetatable({preserved3=3},d)
?c["preserved3"]
l={preserved1=1,preserved2=2}l.preserved1+=1
?l["preserved1"]
l=setmetatable({preserved3=3},d)
?l["preserved3"]
do local _ENV={assert=assert,add=add}assert(add({},1)==1)end for _ENV in all{{l=1,e=5},{l=2,e=6}}do l+=e+e*l end local l={key1=1,key2=2,a=3}l.key1=l.a e,o=circfill,rectfill e(120,126,3)e(126,120,3)o(120,120,123,123)o(123,123,126,126)
while(1==0);
while(1==0)sin=cos cos=sin
local l={1},{1,2,3,4}
?1or 1or 2and 3==4>=4|5^^6<<1>><1 ..2 ..3- -1^4^1/1&7
?((~(((((((tonum(((3or 4)and 5)~=2)|1)^^2)&3)>>1)..1)-(1+3))*3))^2)^1
local l=({})[1],(function()end)()local l,e=sin(1,2),cos((cos()))local l,e=(cos((cos())))local l={i=ord,s=pal}local e=ord"123",pal{1,2},l:i("ord"),l:s({1,2}),sin(1)