pico-8 cartridge // http://www.pico-8.com
version 38
__lua__
print=printh?"hello ᶜ7there♥ら"
🐱,r,h,x,s,u,n,n=11,12,13,14,15,16,17,17t(stat(band()))t()k=0f=0f=0print"this is included"?"#[disable[[this for now/ever]]]"
local n={1,2,3}print(#n)print(#[[#include notaninclude
]])local n="preserved_key"local f={preserved_key=123}?f[n]
local n="preserved_glob"preserved_glob=123?_ENV[n]
local n={}n["whatever"]=123?n.whatever
function n.subfunc()end function n:subfunc()end?n:subfunc()
local n="i"local f={i=123}?f[n]
local n=split"o,f,c,123"local f={o=123,f=234,c=345}?f[n[2]]
local n="c"c=123?_ENV[n]
local n="o:f#~~c,","!t$h+123-x\nif\ns"do local _ENV={assert=assert}assert(true)end for _ENV in all{{l=1},{l=2}}do l+=1end function some_future_pico8_api()end some_future_pico8_api(1,2,3)local n={preserved1=1,preserved2=2}n.preserved1+=1?n["preserved1"]
n=setmetatable({preserved3=3},i)?n["preserved3"]
l={preserved1=1,preserved2=2}l.preserved1+=1?l["preserved1"]
l=setmetatable({preserved3=3},i)?l["preserved3"]
do local _ENV={assert=assert,add=add}assert(add({},1)==1)end for _ENV in all{{l=1,e=5},{l=2,e=6}}do l+=e+e*l end local l={key1=1,key2=2,a=3}l.key1=l.a e,o=circfill,rectfill e(120,126,3)e(126,120,3)o(120,120,123,123)o(123,123,126,126)while(1==0);
while(1==0)sin=cos cos=sin
if(1==2);
if(1==2)sin=cos cos=sin
local l={1},{1,2,3,4}local l=1~=2local e=1,1.2345,4660,4660.33777,-1,-1.2345,-4660.33777,32776,0xf000.f,-39322,-65535.99999local e="hi","hello",'"hi"',"'hello'",'"hi"',"'hi'","","","a\nb","\\","\0¹²³⁴⁵⁶","¹²³⁴⁵⁶⁷","\\\\\\\\\\\\","\n\n\n\n\n\n","¹²³⁴⁵⁶]]"local e=[[]],[[hi]],[['hi']],[["'hi'"]],[["""""'''''hi'''''"""""]],[[♥♥♥♥]],[[]],[[

]]local e=-256,-256*4,65280^4,-65280,~65280if(not l)l=-1
?1or 1or 2and 3==4>=4|5~6<<1>><1 ..2 ..3- -1^4^1/1&7
?((~(((((((tonum(((3or 4)and 5)~=2)|1)~2)&3)>>1)..1)-(1+3))*3))^2)^1
local l=({})[1],(function()end)()local e,o=sin(1,2),cos((cos()))local n,f=(cos((cos())))local l={d=ord,r=pal}local c=ord"123",pal{1,2},l:d("ord"),l:r({1,2}),sin(1)local l={ord"1",[2]=3,l=4,(ord"1")}c+=1e,o=sin(1,2),cos((cos()))n,f=(cos((cos())))function y()return 1,2,ord"1",(ord"1")end if 1==2then elseif 1==2then else end while 1==2do end repeat until 1==1for l in(all{})do end print("test"..@16 .."str")a="renaming bug"function d()local l,e,o,n,f,c,i,d,r,t,h,x,s,u,k,y,v,p,b,w,g,m,j,q,z,A,B return a end?d()