__lua__
?"hello ᶜ7there♥ら"
t(stat(band()))print"this is included"
?"#[disable[[this for now/ever]]]"
local d={1,2,3}print(#d)print(#[[
#include notaninclude
]])local d="preserved_key"local i={preserved_key=123}
?i[d]
local d="preserved_glob"preserved_glob=123
?_ENV[d]
local d={}d["whatever"]=123
?d.whatever
function d.subfunc()end function d:subfunc()end
?d:subfunc()
local d="o"local i={o=123}
?i[d]
local d=split"c,a,d"local i={c=123,a=234,d=345}
?i[d[2]]
local d="n"n=123
?_ENV[d]
do local _ENV={assert=assert}assert(true)end for _ENV in all{{l=1},{l=2}}do l+=1end function some_future_pico8_api()end some_future_pico8_api(1,2,3)local n={preserved1=1,preserved2=2}n.preserved1+=1
?n["preserved1"]
n=setmetatable({preserved3=3},c)
?n["preserved3"]
l={preserved1=1,preserved2=2}l.preserved1+=1
?l["preserved1"]
l=setmetatable({preserved3=3},c)
?l["preserved3"]
do local _ENV={assert=assert,add=add}assert(add({},1)==1)end for _ENV in all{{l=1,e=5},{l=2,e=6}}do l+=e+e*l end local l={key1=1,key2=2,i=3}l.key1=l.i e,o=circfill,rectfill e(120,126,3)e(126,120,3)o(120,120,123,123)o(123,123,126,126)
while(1==0);
while(1==0)sin=cos cos=sin
if(1==2);
if(1==2)sin=cos cos=sin
local l={1},{1,2,3,4}local l=1~=2local l=1,1.2345,4660,4660.33777,-1,-1.2345,-4660.33777,32776,0xf000.f,-39322,-65535.99999local l="hi","hello",'"hi"',"'hello'","\"hi\"","\'hi\'","","","a\nb","\\","\0\1\2\3","\1\2\3\4","\\\\\\\\","\n\n\n\n","\1\2\3]]"local l=[[]],[[hi]],[['hi']],[["'hi'"]],[[""''hi''""]],[[♥♥♥♥]]
?1or 1or 2and 3==4>=4|5^^6<<1>><1 ..2 ..3- -1^4^1/1&7
?((~(((((((tonum(((3or 4)and 5)~=2)|1)^^2)&3)>>1)..1)-(1+3))*3))^2)^1
local l=({})[1],(function()end)()local e,o=sin(1,2),cos((cos()))local n,c=(cos((cos())))local l={r=ord,f=pal}local d=ord"123",pal{1,2},l:r("ord"),l:f({1,2}),sin(1)local l={ord"1",[2]=3,l=4,(ord"1")}d+=1e,o=sin(1,2),cos((cos()))n,c=(cos((cos())))function a()return 1,2,ord"1",(ord"1")end if 1==2then elseif 1==2then else end while 1==2do end repeat until 1==1for l in(pairs{})do end