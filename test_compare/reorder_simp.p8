pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
l=time
do assert(true)printh"124"end
do assert(true)printh"12"end
function d()return 1,2,3end
do local n,o=d(),4,9printh(3 ..n..4)end
do local n,o=d()printh(3 ..n..o..4)end
do local n=d()assert(true)printh(3 ..n..4)end
do local n,o=d()assert(true)printh(3 ..n..o..4)end
do local n=4,9assert(true)printh"34"end
do local n=?"w/e"
assert(n~=nil)printh"34"end
do printh(4)end
do printh(4)end
do printh(3)end
do printh(3)end
do local n=(function()return 1end)()printh(3 ..n)end
do local n=(function()return 3end)()printh(3 ..n)end
do local o,n local function d()return 6end
n,o=3,4n=2n,o=n+5,o+d()printh(n..o)
end
do local o,n local function d()return n end
n=3o=d()printh(n..o)
end
n,o,e=4,5,6printh(n..o..e)
n,o=o-4,2e=n+1printh(n..o..e)
function d()return n end
n=10o=d()printh(n..o)
n,o=11,function()return d()end o=o()printh(n..o)
do
local n
local print=function(o)n=o end
local o=(function()?45
end)()
printh(n)
end
do
local n,_ENV=printh,{c=13}
local o=c
n(o..c)
end
t={}
t.o,t.d=3,4printh(t.o..t.d)
t.o=3t.o=4printh(t.o)
t.d,t.o=t.o+1,3printh(t.o..t.d)
t.o=5t.d=t["o"]printh(t.o..t.d)
t["a"]=6t.o=7printh(t.o)
a,(printh"one"or{}).e=0,printh"two"
f,(printh"three"or{}).l=0,printh"four"
l()
n,o=sqrt(4),sqrt(9)printh(n..o)
n,o=flr(2.3),flr(3.9)printh(n..o)
function max()return n end
n=4o=max(5,6)printh(n..n)
function u()return n end
n=6o=u()printh(n..n)
r=setmetatable({},{__add=function()return n end})l()
n=20o=r+r printh(n..o)
do
local n,_ENV=printh,setmetatable({o=0},{__newindex=function(n,o,d)rawset(n,o,d+n.o)end})
o=3d=4n(o..d)
end
do
local n=setmetatable({o=0},{__newindex=function(n,o,d)rawset(n,o,d+n.o)end})
n.o=7n.d=8printh(n.o..n.d)
end
printh"over..."
