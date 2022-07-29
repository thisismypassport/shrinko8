__lua__
?"hello ᶜ7there♥ら"
t(stat(band()))print"this is included"
?"#[disable[[this for now/ever]]]"
local r={1,2,3}print(#r)print(#[[
#include notaninclude
]])local r="preserved_key"local a={preserved_key=123}
?a[r]
local r="preserved_glob"preserved_glob=123
?_ENV[r]
local r={}r["whatever"]=123
?r.whatever
function r.subfunc()end function r:subfunc()end
?r:subfunc()
local r="o"local a={o=123}
?a[r]
local r=split"d,c,r"local a={d=123,c=234,r=345}
?a[r[2]]
local r="n"n=123
?_ENV[r]
do local _ENV={assert=assert}assert(true)end for _ENV in all{{e=1},{e=2}}do e+=1end function some_future_pico8_api()end some_future_pico8_api(1,2,3)local n={preserved1=1,preserved2=2}n.preserved1+=1
?n["preserved1"]
n=setmetatable({preserved3=3},d)
?n["preserved3"]
e={preserved1=1,preserved2=2}e.preserved1+=1
?e["preserved1"]
e=setmetatable({preserved3=3},d)
?e["preserved3"]
do local _ENV={assert=assert,add=add}assert(add({},1)==1)end for _ENV in all{{e=1,l=5},{e=2,l=6}}do e+=l+l*e end local e={key1=1,key2=2,a=3}e.key1=e.a l,o=circfill,rectfill l(120,126,3)l(126,120,3)o(120,120,123,123)o(123,123,126,126)
while(1==0);
while(1==0)sin=cos cos=sin
if(1==2);
if(1==2)sin=cos cos=sin
local e={1},{1,2,3,4}
?1or 1or 2and 3==4>=4|5^^6<<1>><1 ..2 ..3- -1^4^1/1&7
?((~(((((((tonum(((3or 4)and 5)~=2)|1)^^2)&3)>>1)..1)-(1+3))*3))^2)^1
local e=({})[1],(function()end)()local l,o=sin(1,2),cos((cos()))local n,d=(cos((cos())))local e={i=ord,t=pal}local r=ord"123",pal{1,2},e:i("ord"),e:t({1,2}),sin(1)local e={ord"1",[2]=3,e=4,(ord"1")}r+=1l,o=sin(1,2),cos((cos()))n,d=(cos((cos())))function c()return 1,2,ord"1",(ord"1")end if 1==2then elseif 1==2then else end while 1==2do end repeat until 1==1for e in(pairs{})do end