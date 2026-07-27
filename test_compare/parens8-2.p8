pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
function c(n)return function()return n end end function n(d,l)local o,u,n,r,e,c={},1,2,0,0,split",3,7,15,31,63,127,255,511,1023,2047,4095,8191,16383,32767,-1"local function t(e)add(o,e)if(#o+1>=1<<n)n+=1
end for n in all(l)do t(n)end local function l()while(e<n)r<<=8r|=ord(d,u)>>>16e+=8u+=1
e-=n local n=r>>>e-16&c[n]if(n~=0)return n
end local n=o[l()]local e=n for r in l do e=(function(n)if(n)t(e..n[1])return n
n=e..e[1]t(n)return n end)(o[r])n..=e end return n end function u(r)local e=0local function n()e+=1return ord(r,e)end local function t()return n()>>>16|n()>>>8|n()|n()<<8end return function()local n,o=n()o,n=n&252~=252and n>>>2&63,n%4if(n==0)return o and o-31or t()
if(n==3)return({true,false})[o]
local n=o or t()<<16e+=n return sub(r,e-n+1,e)end end do local n,r={function()local n=l()return function()return d[n]end end},split"1,0,0,2,2,2,2,1,3,2"function e(e)d,l,o={},u(e),function()d,l,o=nil end return n[l()]()(o())()(_ENV)end local function t(a,b,c)local n=o function o()a,b,c=a(),b(),c()return n()end return function()return a end,function()end,function(f)return f end,function(f)return a(f)==b(f)end,function(f)return a(f)(b(f))end,function(f)a(f)return b(f)end,function(f)local u={__index=a({},f)}return function(...)return b(setmetatable({...},u))end end,function(f)return f[a]end,function(f)f[b][c]=a(f)end,function(f)return f[a][b]end end for o,u in inext,split"0,0,0,2,2,2,2,0,1,0"do local function e(e)return e<u and n[l()]()or c(e<r[o]and l())end add(n,function()return c(add(d,(select(o,t(e(0),e(1),e(2))))))end)end end e(n(chr(peek(0,38)),"う☉▤さ█⁵e⬆️そ」asrt…d░ᶠpinh■o"))
__gfx__
8068244f7cc02854823bc0c13df8c84611a411240b755ce381acc45d51c185982760a078a3000000000000000000000000000000000000000000000000000000
__meta:title__

note: this test can only switch compiler once!
