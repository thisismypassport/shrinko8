pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
function d(n)return function()return n end end function n(c,u)local e,t,n,r,o,d={},1,2,0,0,split",3,7,15,31,63,127,255,511,1023,2047,4095,8191,16383,32767,-1"local function l(o)add(e,o)if(#e+1>=1<<n)n+=1
end for n in all(u)do l(n)end local function u()while(o<n)r<<=8r|=ord(c,t)>>>16o+=8t+=1
o-=n local n=r>>>o-16&d[n]if(n~=0)return n
end local n=e[u()]local o=n for r in u do o=(function(n)if(n)l(o..n[1])return n
n=o..o[1]l(n)return n end)(e[r])n..=o end return n end function l(e)local n=0local function o()n+=1return ord(e,n)end local function r()return o()>>>16|o()>>>8|o()|o()<<8end return function()local o=o()local o,l=o&252~=252and o\4,o%4if(l==1)return o and o-31or r()
if(l==0)return({true,false})[o]
local o=o or r()<<16n+=o return sub(e,n-o+1,n)end end do local n,r={function()local n=u()return function()return c[n]end end},split"b,a,a,c,c,c,c,b,d,c"function o(o)c,u,e={},l(o),function()c,u,e=nil end return n[u()]()(e())()(_ENV)end local function l(a,b,c)local n=e function e()a,b,c=a(),b(),c()return n()end return function()return a end,function()end,function(f)return f end,function(f)return a(f)==b(f)end,function(f)return a(f)(b(f))end,function(f)a(f)return b(f)end,function(f)local u={__index=a({},f)}return function(...)return b(setmetatable({...},u))end end,function(f)return f[a]end,function(f)f[b][c]=a(f)end,function(f)return f[a][b]end end for e,t in inext,split"a,a,a,c,c,c,c,a,b,a"do local function o(o)return o<t and n[u()]()or d(o<r[e]and u())end add(n,function()return d(add(c,(select(e,l(o"a",o"b",o"c")))))end)end end o(n(chr(peek(0,38)),"え웃▥し▒⁶oˇた¥asert➡️c✽\0pinh□d"))
__gfx__
8068248f3c681422499568a1178e84239272011aa5c2201a415882275a787942068c273cf4000000000000000000000000000000000000000000000000000000
__meta:title__

note: this test can only switch compiler once!
