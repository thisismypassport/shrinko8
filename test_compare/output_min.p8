pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
print=printh
?"hello ᶜ7there♥ら"
🐱,あ,ョ,◝,゛,゜,F,F=11,12,13,14,15,16,17,17
t(stat(band()))
t()
x=0 b=0
b=0
print"this is included"
?"#[disable[[this for now/ever]]]"
local include={1,2,3}
print(
#include
)
print(
#[[#include notaninclude
]]
)
local my_key,my_obj="preserved_key",{preserved_key=123}
?my_obj[my_key]
local my_key="preserved_glob"
preserved_glob=123
?_ENV[my_key]
local preserving_obj={}
preserving_obj["whatever"]=123
?preserving_obj.whatever
function preserving_obj.subfunc()end
function preserving_obj:subfunc()end
?preserving_obj:subfunc()
local my_key,my_obj="key",{key=123}
?my_obj[my_key]
local my_keys,my_obj=split"key1,key2,key3,123",{key1=123,key2=234,key3=345}
?my_obj[my_keys[2]]
local my_key="glob"
glob=123
?_ENV[my_key]
local custom_splits="key1:key2#~~key3,","!key1_still$key2█ア+123-key123\nif\nif◝"
do
local _ENV={assert=assert}
assert(true)
end
for _ENV in all{{x=1},{x=2}}do
x+=1
end
function some_future_pico8_api()end
some_future_pico8_api(1,2,3)
local my_table={preserved1=1,preserved2=2}
my_table.preserved1+=1
?my_table["preserved1"]
my_table=setmetatable({preserved3=3},my_meta)
?my_table["preserved3"]
g_my_table={preserved1=1,preserved2=2}
g_my_table.preserved1+=1
?g_my_table["preserved1"]
g_my_table=setmetatable({preserved3=3},my_meta)
?g_my_table["preserved3"]
local env={assert=assert,add=add}
do
local _ENV=env
assert(add({},1)==1)
end
do
local _ENV={assert=assert,add=add}
assert(add({},1)==1)
end
local deli_result
for _ENV in all{{x=1,y=5},{x=2,y=6}}do
x+=y+y*x
deli_result=deli{2}
end
assert(deli_result==2)
local thing={key1=1,key2=2,other=3}
thing.key1=thing.other
while(1==0);
while(1==0)sin=cos cos=sin
if(1==2);
if(1==2)sin=cos cos=sin
local tbls={1},{1,2,3,4}
local nothing,nums=1~=2,1,1.2345,4660,4660.33777,-1,-1.2345,-4660.33777,32776,0xf000.f,-39322,-65535.99999
local strs="hi","hello",'"hi"',"'hello'",'"hi"',"'hi'","","","a\nb","\\","\0¹²³⁴⁵⁶","¹²³⁴⁵⁶⁷","\\\\\\\\\\\\","\n\n\n\n\n\n","¹²³⁴⁵⁶]]"
local strs2=[[]],[[hi]],[['hi']],[["'hi'"]],[["""""'''''hi'''''"""""]],[[♥♥♥♥]],[[]],[[

]],[==[\\\\\\\\\

]]]=]]===]]==]
local numbug=-256,-256*4,65280^4,-65280,~65280
if(not nothing)nothing=-1
function tokenhell(...)
return 1.2 ..4 .. .....0
end
?tokenhell(3)
?1or 1or 2and 3==4>=4|5~6<<1>><1 ..2 ..3- -1^4^1/1&7
?((~(((((((tonum(((3or 4)and 5)~=2)|1)~2)&3)>>1)..1)-(1+3))*3))^2)^1
local prefix=({})[1],(function()end)()
local calls1,calls2,calls1_,obj,calls2_=sin(1,2),cos((cos())),(cos((cos()))),{ord=ord,pal=pal}
local calls3=ord"123",pal{1,2},obj:ord("ord"),obj:pal({1,2}),sin(1)
local moretests={ord"1",[2]=3,x=4,(ord"1")}
calls3+=1
calls1,calls2,calls1_,calls2_=sin(1,2),cos((cos())),(cos((cos())))
function xxx()return 1,2,ord"1",(ord"1")end
if 1==2then elseif 1==2then else end
while 1==2do end
repeat until 1==1
for a in(all{})do end
print("test"..@16 .."str")
?calls3+(({})[1]and({}).🐱 or...or xxx())+3+-3
if(true)?"sh1"
if true then?"sh2"
end
if(true)if false then else print"sh3"end
if true then if false then else print"sh4"end end
l="renaming bug"
function fff()
local l1,l2,l3,l4,l5,l6,l7,l8,l9,l10,l11,l12,l13,l14,l15,l16,l17,l18,l19,l10,l20,l21,l22,l23,l24,l25,l26
return l
end
?fff()
x=0 x=1
function old_name(old_param,do_rename_this)
return old_param.old_member,do_rename_this.old_member
end
function old_name(old_param,do_rename_this,do_rename_that)
local more_things_to_rename,and_so_on
return old_param.old_member
end
function ggg(p1,p2,p3,p4,p5,p6)
return p1+p2+p3+p4+p5+p6
end
?ggg(1,2,4,8,16,32)
done=?"END!"
