pico-8 cartridge // http://www.pico-8.com
version 41
__lua__
d=time
do local o,n,c,l=1,2,4assert(l==nil)printh(o..n..c)end
do local l,c,d,a,o,n=1,2assert(o==nil and n==nil and d==nil and a==nil)printh(l..c)end
function n()return 1,2,3end
do local l,o,n=3,n(),4,9printh(l..o..n)end
do local l,o,n=3,n()local c=4printh(l..o..n..c)end
do local l,o,c,n=3,(n()),4assert(n==nil)printh(l..o..c)end
do local l,o=3local n,c=n()local d=4assert(o==nil)printh(l..n..c..d)end
do local l,o=3local n=4,9assert(o==nil)printh(l..n)end
do local l,l=3,4printh(l)end
do local l,l=3,4printh(l)end
do local l local l=3printh(l)end
do local l local l=3printh(l)end
do local l,o=3,(function()return 1end)()printh(l..o)end
do local l=3local o=(function()return l end)()printh(l..o)end
do local o,l local function n()return 6end
l,o=3,4l=2l,o=l+5,o+n()printh(l..o)
end
do local o,l local function n()return l end
l=3o=n()printh(l..o)
end
l,o,c=4,5,6printh(l..o..c)
l,o=o-4,2c=l+1printh(l..o..c)
function n()return l end
l=10o=n()printh(l..o)
l,o=11,function()return n()end o=o()printh(l..o)
do
local l
local print=function(o)l=o end
local o=(function()?45
end)()
printh(l)
end
do
local l,_ENV=printh,{a=13}
local o=a
l(o..a)
end
t={}
t.l,t.o=3,4printh(t.l..t.o)
t.l=3t.l=4printh(t.l)
t.o,t.l=t.l+1,3printh(t.l..t.o)
t.l=5t.o=t["l"]printh(t.l..t.o)
t["a"]=6t.l=7printh(t.l)
u,(printh"one"or{}).c=0,printh"two"
r,(printh"three"or{}).d=0,printh"four"
d()
l,o=sqrt(4),sqrt(9)printh(l..o)
function max()return l end
l=4o=max(5,6)printh(l..l)
e=setmetatable({},{__add=function()return l end})d()
l=20o=e+e printh(l..o)
do
local n,_ENV=printh,setmetatable({l=0},{__newindex=function(l,o,n)rawset(l,o,n+l.l)end})
l=3o=4n(l..o)
end
do
local l=setmetatable({l=0},{__newindex=function(l,o,n)rawset(l,o,n+l.l)end})
l.l=7l.o=8printh(l.l..l.o)
end
printh"over..."