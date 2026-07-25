pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
function f(n)return function()return n end end function d(c,l)local o,u,n,r,e,d={},1,2,0,0,split",3,7,15,31,63,127,255,511,1023,2047,4095,8191,16383,32767,-1"local function t(e)add(o,e)if(#o+1>=1<<n)n+=1
end for n in all(l)do t(n)end local function l()while(e<n)r<<=8r|=ord(c,u)>>>16e+=8u+=1
e-=n local n=r>>>e-16&d[n]if(n~=0)return n
end local n=o[l()]local e=n for r in l do e=(function(n)if(n)t(e..n[1])return n
n=e..e[1]t(n)return n end)(o[r])n..=e end return n end function n(e)e=all(split(e,16384,false))local n,o,t=16384,{}local function c()if(n==16384)t,n=e(),0
end local function e()c()n+=1return ord(t,n)end local function u()return e()|e()<<8end local function d()return e()>>>16|e()>>>8|u()end local function r()local function i(n)n=n or add(o,{})for e,o in function()local n=r()return n,n~=nil and r()end do n[e]=o end return n end local l=e()local e=l&252~=252and l>>>2&63return select(l%4+1,function()return e and e-31or d()end,function()local e,r=e and e>>>16or d(),""repeat c()local o=min(e,16384-n>>>16)<<16r..=sub(t,n+1,n+o)n+=o e-=o>>16until e<=0return add(o,r)end,function()local n=add(o,{})for e=1,e or u()do n[e]=r()end return i(n)end,function()return select(e,f(),f(true),f(false),function()local n=u()return o[n]end,i)()end)()end return r()end function u(e,n,o,r)if(e>0)return l[n[1]](unpack(n,2)),u(e-1,o,r)
return f(n),f(o),f(r)end function c(n)o,e={},f return u(1,n)(e())()(_ENV)end l={function(n)return function()return o[n]end end}for n,e in inext,split"0,0,0,2,2,2,2,0,1,0"do add(l,function(...)return f(add(o,(select(n,r(u(e,...))))))end)end function r(a,b,c)local n=e function e()a,b,c=a(),b(),c()return n()end return function()return a end,function()end,function(f)return f end,function(f)return a(f)==b(f)end,function(f)return a(f)(b(f))end,function(f)a(f)return b(f)end,function(f)local u={__index=a({},f)}return function(...)return b(setmetatable({...},u))end end,function(f)return f[a]end,function(f)f[b][c]=a(f)end,function(f)return f[a][b]end end c(n(d(chr(peek(0,89)),"ᵉう⁶☉⁷▤□さ\n█⁵u⁙\0coelr⬆️そ」ast…ᶜ░‖pinh■d")))
__gfx__
40024c4111780229a8412acc2a2ad0c2cef42ddb9fc2386cec8119489f98821f503986400a212ab87103069833a2d02541438d0e0aec50cc6a280d75f2d0b398
86c83d8e3dc287994f600558210788c8041881419fec12cc00000000000000000000000000000000000000000000000000000000000000000000000000000000
__meta:title__

note: this test can only switch compiler once!
