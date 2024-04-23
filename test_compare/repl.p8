pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
--------------------------------------
-- Please see 'Commented Source Code' section in the BBS
-- for the original commented source code
-- (The below had the comments stripped due to cart size limits)
--------------------------------------
local e,n,l=_ENV,{},{}for e,t in pairs(_ENV)do n[e]=t if(type(t)=="function")l[e]=true
end local _ENV=n J,nt=true function p(t,e)for n=1,#e do if(sub(e,n,n)==t)return n
end end function b(e,n)return sub(e,n,n)end local n,t,o=split"a,b,f,n,r,t,v,\\,\",',\n,*,#,-,|,+,^",split"⁷,⁸,ᶜ,\n,\r,	,ᵇ,\\,\",',\n,¹,²,³,⁴,⁵,⁶",{}for e=1,#n do o[n[e]]=t[e]end function y(n)return n>="0"and n<="9"end function D(n)return n>="A"and n<="Z"or n>="a"and n<="z"or n=="_"or n>="█"or y(n)end function nc(l,n,i,r)local e=""while n<=#l do local t=b(l,n)if(t==i)break
if t=="\\"then n+=1local e=b(l,n)t=o[e]if e=="x"then e=tonum("0x"..sub(l,n+1,n+2))if(e)n+=2else r"bad hex escape"
t=chr(e)elseif y(e)then local o=n while y(e)and n<o+3do n+=1e=b(l,n)end n-=1e=tonum(sub(l,o,n))if(not e or e>=256)r"bad decimal escape"
t=chr(e)elseif e=="z"then repeat n+=1e=b(l,n)until not p(e," \r	ᶜᵇ\n")if(e=="")r()
t=""n-=1elseif e==""then r()t=""end if(not t)r("bad escape: "..e)t=""
elseif t=="\n"then r"unterminated string"break end e..=t n+=1end if(n>#l)r("unterminated string",true)
return e,n+1end function Z(e,n,t,l)if b(e,n)=="["then n+=1local l=n while(b(e,n)=="=")n+=1
local l="]"..sub(e,l,n-1).."]"local r=#l if b(e,n)=="["then n+=1if(b(e,n)=="\n")n+=1
local o=n while(n<=#e and sub(e,n,n+r-1)~=l)n+=1
if(n>=#e)t()
return sub(e,o,n-1),n+r end end if(l)t"invalid long brackets"
return nil,n end function nl(t,u)local n,a,r,c,s,h,f,o=1,1,{},{},{},{}local function i(n,e)if(u)nr(n,o)
f=n and not e end while n<=#t do o=n local e,d,l=b(t,n)if p(e," \r	ᶜᵇ\n")then n+=1d=true if(e=="\n")a+=1
elseif e=="-"and b(t,n+1)=="-"then n+=2if(b(t,n)=="[")l,n=Z(t,n,i)
if not l then while(n<=#t and b(t,n)~="\n")n+=1
end if(u)d=true else add(r,true)
elseif y(e)or e=="."and y(b(t,n+1))then local f,d="0123456789",true if e=="0"and p(b(t,n+1),"xX")then f..="AaBbCcDdEeFf"n+=2elseif e=="0"and p(b(t,n+1),"bB")then f="01"n+=2end while true do e=b(t,n)if e=="."and d then d=false elseif not p(e,f)then break end n+=1end l=sub(t,o,n-1)if(not tonum(l))i"bad number"l="0"
add(r,tonum(l))elseif D(e)then while D(b(t,n))do n+=1end add(r,sub(t,o,n-1))elseif e=="'"or e=='"'then l,n=nc(t,n+1,e,i)add(r,{t=l})elseif e=="["and p(b(t,n+1),"=[")then l,n=Z(t,n,i,true)add(r,{t=l})else n+=1local l,f,d=unpack(split(sub(t,n,n+2),""))if l==e and f==e and p(e,".>")then n+=2if(d=="="and p(e,">"))n+=1
elseif l==e and f~=e and p(e,"<>")and p(f,"<>")then n+=2if(d=="=")n+=1
elseif l==e and p(e,".:^<>")then n+=1if(f=="="and p(e,".^<>"))n+=1
elseif l=="="and p(e,"+-*/\\%^&|<>=~!")then n+=1elseif p(e,"+-*/\\%^&|<>=~#(){}[];,?@$.:")then else i("bad char: "..e)end add(r,sub(t,o,n-1))end if(not d)add(c,a)add(s,o)add(h,n-1)
if(f)r[#r],f=false,false
end return r,c,s,h end function q(t,n)for e=1,#n do if(n[e]==t)return e
end end function H(n)return unpack(n,1,n.n)end function n1(e)local n={}for e,t in next,e do n[e]=t end return n end local n=split"and,break,do,else,elseif,end,false,for,function,goto,if,in,local,nil,not,or,repeat,return,then,true,until,while"L={}for n in all(n)do L[n]=true end local function Z(n)return type(n)=="string"and b(n,#n)=="="end no=split"end,else,elseif,until"function ni(n,X)local r,B,t=nl(n,true)local n,i,u,x,f,s,h,e,c,m,a,v=1,0,0,{}local function o(e)nr(e,t[n-1]or 1)end local function p(n)return function()return n end end local function _(e)local n=f[e]if(n)return function(t)return t[n][e]end else n=f._ENV return function(t)return t[n]._ENV[e]end
end local function C()local n=f["..."]if(not n or n~=v)o"unexpected '...'"
return function(e)return H(e[n]["..."])end end local function A(e)local n=f[e]if(n)return function(t)return t[n],e end else n=f._ENV return function(t)return t[n]._ENV,e end
end local function t(e)local t=r[n]n+=1if(t==e)return
if(t==nil)o()
o("expected: "..e)end local function d(e)if(not e)e=r[n]n+=1
if(e==nil)o()
if(type(e)=="string"and D(b(e,1))and not L[e])return e
if(type(e)=="string")o("invalid identifier: "..e)
o"identifier expected"end local function l(e)if(r[n]==e)n+=1return true
end local function g()f=setmetatable({},{__index=f})i+=1end local function k()f=getmetatable(f).__index i-=1end local function b(l,t)local e,n={},#t for n=1,n-1do e[n]=t[n](l)end if n>0then local t=pack(t[n](l))if(t.n~=1)for l=1,t.n do e[n+l-1]=t[l]end n+=t.n-1else e[n]=t[1]
end e.n=n return e end local function w(e)local n={}add(n,(e()))while l","do add(n,(e()))end return n end local function y(r,o,i)local n={}if i then add(n,i)elseif not l")"then while true do add(n,(e()))if(l")")break
t","end end if(o)return function(e)local t=r(e)return t[o](t,H(b(e,n)))end,true,nil,function(e)local t=r(e)return t[o],pack(t,H(b(e,n)))end else return function(e)return r(e)(H(b(e,n)))end,true,nil,function(e)return r(e),b(e,n)end
end local function D()local o,u,c,a={},{},1while not l"}"do a=nil local i,f if l"["then i=e()t"]"t"="f=e()elseif r[n+1]=="="then i=p(d())t"="f=e()else i=p(c)f=e()c+=1a=#o+1end add(o,i)add(u,f)if(l"}")break
if(not l";")t","
end return function(e)local t={}for n=1,#o do if(n==a)local l,n=o[n](e),pack(u[n](e))for e=1,n.n do t[l+e-1]=n[e]end else t[o[n](e)]=u[n](e)
end return t end end local function z(s,h)local n,b,e if s then if h then g()n=d()f[n]=i e=A(n)else n={d()}while(l".")add(n,d())
if(l":")add(n,d())b=true
if(#n==1)e=A(n[1])else local t=_(n[1])for e=2,#n-1do local l=t t=function(t)return l(t)[n[e]]end end e=function(e)return t(e),n[#n]end
end end local n,r={}if(b)add(n,"self")
t"("if not l")"then while true do if(l"...")r=true else add(n,d())
if(l")")break
t","if(r)o"unexpected param after '...'"
end end g()for n in all(n)do f[n]=i end if(r)f["..."]=i
local l,o,f=x,a,v x,a,v={},u+1,i local i=c()for n in all(x)do n()end x,a,v=l,o,f t"end"k()return function(t)if(h)add(t,{})
local l=n1(t)local o=#l local n=function(...)local t,e=pack(...),l if(#e~=o)local n={}for t=0,o do n[t]=e[t]end e=n
local l={}for e=1,#n do l[n[e]]=t[e]end if(r)l["..."]=pack(unpack(t,#n+1,t.n))
add(e,l)local n=i(e)deli(e)if n then if(type(n)=="table")return H(n)
return n()end end if(s)local e,t=e(t)e[t]=n else return n
end end local function v()local l=r[n]n+=1local n if(l==nil)o()
if(l=="nil")return p()
if(l=="true")return p(true)
if(l=="false")return p(false)
if(type(l)=="number")return p(l)
if(type(l)=="table")return p(l.t)
if(l=="{")return D()
if(l=="(")n=e()t")"return function(e)return(n(e))end,true
if(l=="-")n=e(11)return function(e)return-n(e)end
if(l=="~")n=e(11)return function(e)return~n(e)end
if(l=="not")n=e(11)return function(e)return not n(e)end
if(l=="#")n=e(11)return function(e)return#n(e)end
if(l=="@")n=e(11)return function(e)return@n(e)end
if(l=="%")n=e(11)return function(e)return%n(e)end
if(l=="$")n=e(11)return function(e)return$n(e)end
if(l=="function")return z()
if(l=="...")return C()
if(l=="\\")n=d()return function()return ns(n)end,true,function()return nh(n)end
if(d(l))return _(l),true,A(l)
o("unexpected token: "..l)end local function A(e,t,l,r)local n if(e=="^"and t<=12)n=r(12)return function(e)return l(e)^n(e)end
if(e=="*"and t<10)n=r(10)return function(e)return l(e)*n(e)end
if(e=="/"and t<10)n=r(10)return function(e)return l(e)/n(e)end
if(e=="\\"and t<10)n=r(10)return function(e)return l(e)\n(e)end
if(e=="%"and t<10)n=r(10)return function(e)return l(e)%n(e)end
if(e=="+"and t<9)n=r(9)return function(e)return l(e)+n(e)end
if(e=="-"and t<9)n=r(9)return function(e)return l(e)-n(e)end
if(e==".."and t<=8)n=r(8)return function(e)return l(e)..n(e)end
if(e=="<<"and t<7)n=r(7)return function(e)return l(e)<<n(e)end
if(e==">>"and t<7)n=r(7)return function(e)return l(e)>>n(e)end
if(e==">>>"and t<7)n=r(7)return function(e)return l(e)>>>n(e)end
if(e=="<<>"and t<7)n=r(7)return function(e)return l(e)<<>n(e)end
if(e==">><"and t<7)n=r(7)return function(e)return l(e)>><n(e)end
if(e=="&"and t<6)n=r(6)return function(e)return l(e)&n(e)end
if(e=="^^"and t<5)n=r(5)return function(e)return l(e)~n(e)end
if(e=="|"and t<4)n=r(4)return function(e)return l(e)|n(e)end
if(e=="<"and t<3)n=r(3)return function(e)return l(e)<n(e)end
if(e==">"and t<3)n=r(3)return function(e)return l(e)>n(e)end
if(e=="<="and t<3)n=r(3)return function(e)return l(e)<=n(e)end
if(e==">="and t<3)n=r(3)return function(e)return l(e)>=n(e)end
if(e=="=="and t<3)n=r(3)return function(e)return l(e)==n(e)end
if((e=="~="or e=="!=")and t<3)n=r(3)return function(e)return l(e)~=n(e)end
if(e=="and"and t<2)n=r(2)return function(e)return l(e)and n(e)end
if(e=="or"and t<1)n=r(1)return function(e)return l(e)or n(e)end
end local function C(u,l,a)local i=r[n]n+=1local o,f if a then if(i==".")o=d()return function(n)return l(n)[o]end,true,function(n)return l(n),o end
if(i=="[")o=e()t"]"return function(n)return l(n)[o(n)]end,true,function(n)return l(n),o(n)end
if(i=="(")return y(l)
if(i=="{"or type(i)=="table")n-=1f=v()return y(l,nil,f)
if i==":"then o=d()if(r[n]=="{"or type(r[n])=="table")f=v()return y(l,o,f)
t"("return y(l,o)end end local e=A(i,u,l,e)if(not e)n-=1
return e end e=function(r)local n,e,t,l=v()while true do local r,o,i,f=C(r or 0,n,e)if(not r)break
n,e,t,l=r,o,i,f end return n,t,l end local function v()local e,n=e()if(not n)o"cannot assign to value"
return n end local function C()local n=w(v)t"="local e=w(e)if(#n==1and#e==1)return function(t)local n,l=n[1](t)n[l]=e[1](t)end else return function(t)local l,r={},{}for e=1,#n do local n,e=n[e](t)add(l,n)add(r,e)end local e=b(t,e)for n=#n,1,-1do l[n][r[n]]=e[n]end end
end local function D(t,l)local r=r[n]n+=1local n=sub(r,1,-2)local n=A(n,0,t,function()return e()end)if(not n)o"invalid compound assignment"
return function(e)local t,l=l(e)t[l]=n(e)end end local function E()if l"function"then return z(true,true)else local n,e=w(d),l"="and w(e)or{}g()for e=1,#n do f[n[e]]=i end if(#n==1and#e==1)return function(t)add(t,{[n[1]]=e[1](t)})end else return function(t)local l,r={},b(t,e)for e=1,#n do l[n[e]]=r[e]end add(t,l)end
end end local function A(e)local t=B[n-1]h=function()return t~=B[n]end if(not e or h())o(n<=#r and"bad shorthand"or nil)
end local function B()local r,o,e,n=r[n]=="(",e()if l"then"then e,n=c()if l"else"then n=c()t"end"elseif l"elseif"then n=B()else t"end"end else A(r)e=c()if(not h()and l"else")n=c()
h=nil end return function(t)if o(t)then return e(t)elseif n then return n(t)end end end local function v(...)local n=m m=u+1local e=c(...)m=n return e end local function y(n,e)if(n==true)return
return n,e end local function F()local r,o,n=r[n]=="(",e()if(l"do")n=v()t"end"else A(r)n=v()h=nil
return function(e)while o(e)do if(stat(1)>=1)I()
local n,e=n(e)if(n)return y(n,e)
end end end local function A()local l,r=i,v(true)t"until"local o=e()while(i>l)k()
return function(n)repeat if(stat(1)>=1)I()
local e,t=r(n)if(not e)t=o(n)
while(#n>l)deli(n)
if(e)return y(e,t)
until t end end local function j()if r[n+1]=="="then local r=d()t"="local o=e()t","local d,e=e(),l","and e()or p(1)t"do"g()f[r]=i local l=v()t"end"k()return function(n)for e=o(n),d(n),e(n)do if(stat(1)>=1)I()
add(n,{[r]=e})local e,t=l(n)deli(n)if(e)return y(e,t)
end end else local l=w(d)t"in"local e=w(e)t"do"g()for n in all(l)do f[n]=i end local o=v()t"end"k()return function(n)local e=b(n,e)while true do local r,t={},{e[1](e[2],e[3])}if(t[1]==nil)break
e[3]=t[1]for n=1,#l do r[l[n]]=t[n]end if(stat(1)>=1)I()
add(n,r)local e,t=o(n)deli(n)if(e)return y(e,t)
end end end end local function p()if(not m or a and m<a)o"break outside of loop"
return function()return true end end local function m()if(not a and not X)o"return outside of function"
if r[n]==";"or q(r[n],no)or h and h()then return function()return pack()end else local n,r,t=e()local n={n}while(l",")add(n,(e()))
if#n==1and t and a then return function(n)local n,e=t(n)if(stat(1)>=1)I()
return function()return n(H(e))end end else return function(e)return b(e,n)end end end end local function g(e)local n=d()t"::"if(s[n]and s[n].e==u)o"label already defined"
s[n]={l=i,e=u,o=e,r=#e}end local function v()local t,e,l,n=d(),s,i add(x,function()n=e[t]if(not n)o"label not found"
if(a and n.e<a)o"goto outside of function"
local e=e[n.e]or l if(n.l>e and n.r<#n.o)o"goto past local"
end)return function()if(stat(1)>=1)I()
return 0,n end end local function d(f)local i=r[n]n+=1if(i==";")return
if(i=="do")local n=c()t"end"return n
if(i=="if")return B()
if(i=="while")return F()
if(i=="repeat")return A()
if(i=="for")return j()
if(i=="break")return p()
if(i=="return")return m(),true
if(i=="local")return E()
if(i=="goto")return v()
if(i=="::")return g(f)
if(i=="function"and r[n]~="(")return z(true)
if(i=="?")local e,t=_"print",w(e)return function(n)e(n)(H(b(n,t)))end
n-=1local i,e,f,t=n,e()if l","or l"="then n=i return C()elseif Z(r[n])then return D(e,f)elseif u<=1and J then return function(n)local n=pack(e(n))if(not(t and n.n==0))add(G,n)
nt=n[1]end else if(not t)o"statement has no effect"
return function(n)e(n)end end end c=function(e)s=setmetatable({},{__index=s})s[u]=i u+=1local a,f,o=u,e and 32767or i,{}while n<=#r and not q(r[n],no)and not(h and h())do local n,e=d(o)if(n)add(o,n)
if(e)l";"break
end while(i>f)k()
u-=1s=getmetatable(s).__index return function(e)local l,r,t,n=1,#o while l<=r do t,n=o[l](e)if t then if(type(t)~="number")break
if(n.e~=a)break
l=n.r while(#e>n.l)deli(e)
t,n=nil end l+=1end while(#e>f)deli(e)
return t,n end end f=J and{_ENV=0,_env=0,_=0}or{_ENV=0}local e=c()if(n<=#r)o"unexpected end"
for n in all(x)do n()end return function(n)local n=J and{_ENV=n,_env=n,_=nt}or{_ENV=n}local n=e{[0]=n}if(n)return H(n)
end end S,T=10,false local t={["\0"]="000",["ᵉ"]="014",["ᶠ"]="015"}for n,e in pairs(o)do if(not p(n,"'\n"))t[e]=n
end function n0(n)local e=1while e<=#n do local l=b(n,e)local t=t[l]if(t)n=sub(n,1,e-1).."\\"..t..sub(n,e+1)e+=#t
e+=1end return'"'..n..'"'end function n2(n)if(type(n)~="string")return false
if(L[n])return false
if(#n==0or y(b(n,1)))return false
for e=1,#n do if(not D(b(n,e)))return false
end return true end function f(e,t)local n=type(e)if n=="nil"then return"nil"elseif n=="boolean"then return e and"true"or"false"elseif n=="number"then return tostr(e,T)elseif n=="string"then return n0(e)elseif n=="table"and not t then local n,t,r="{",0,0for e,l in next,e do if(t==S)n=n..",<...>"break
if(t>0)n=n..","
local l=f(l,1)if e==r+1then n=n..l r=e elseif n2(e)then n=n..e.."="..l else n=n.."["..f(e,1).."]="..l end t+=1end return n.."}"else return"<"..tostr(n)..">"end end function nb(n,e)if(e==nil)return n
if(not n)n=""
local t=min(21,#e)for t=1,t do if(#n>0)n..="\n"
local t=e[t]if type(t)=="table"then local e=""for n=1,t.n do if(#e>0)e=e..", "
e=e..f(t[n])end n..=e else n..=t end end local l={}for n=t+1,#e do l[n-t]=e[n]end return n,l end poke(24365,1)cls()h="> "a,x,_="",1,0c,A=1,20w,z={""},1X=false m,u=0,1M,N=true,true s={7,4,3,5,6,8,5,12,14,7,11,5}e.print=function(n,...)if(pack(...).n~=0or not M)return print(n,...)
add(G,tostr(n))end function nf()poke(24368,1)end function nd()return function()if(stat(30))return stat(31)
end end function U(l,r)local e,n,t=1,0,0if(not l)return e,n,t
while e<=#l do local l=b(l,e)local o=l>="█"if(n>=(o and 31or 32))t+=1n=0
if(r)r(e,l,n,t)
if(l=="\n")t+=1n=0else n+=o and 2or 1
e+=1end return e,n,t end function C(t,l)local n,e=0,0local o,r,t=U(t,function(t,i,r,o)if(l==t)n,e=r,o
end)if(l>=o)n,e=r,t
if(r>0)t+=1
return n,e,t end function E(l,r,e)local t,n=1,false local r,o,l=U(l,function(o,f,i,l)if(e==l and r==i and not n)t=o n=true
if((e<l or e==l and r<i)and not n)t=o-1n=true
end)if(not n)t=e>=l and r or r-1
if(o>0)l+=1
return t,l end function V(n,t,l,e)if(type(e)=="function")U(n,function(n,r,o,i)print(r,t+o*4,l+i*6,e(n))end)else print(n and"⁶rw"..n,t,l,e)
end function np(n,r,o)local i,e,f,t=nl(n)local e=1V(n,r,o,function(r)while e<=#t and t[e]<r do e+=1end local n if(e<=#t and f[e]<=r)n=i[e]
local e=s[5]if n==false then e=s[6]elseif n==true then e=s[7]elseif type(n)~="string"or q(n,{"nil","true","false"})then e=s[8]elseif L[n]then e=s[9]elseif not D(b(n,1))then e=s[10]elseif l[n]then e=s[11]end return e end)end function _draw()local r,o,i=peek(24357),peek2(24360),peek2(24362)camera()local function n(n)cursor(0,127)for n=1,n do rectfill(0,u*6,127,(u+1)*6-1,0)if(u<21)u+=1else print""
end end local function f(n,e)for n=1,n do if(u>e)u-=1
rectfill(0,u*6,127,(u+1)*6-1,0)end end local function d(n,e)for t=0,2do local l=pget(n+t,e+5)pset(n+t,e+5,l==0and s[12]or 0)end end local function l(r)local l=h..a.." "local o,t,e=C(l,#h+c)if e>x then n(e-x)elseif e<x then f(x-e,e)end x=e _=mid(_,0,max(x-21,0))::n::local n=u-x+_ if(n+t<0)_+=1goto n
if(n+t>=21)_-=1goto n
local n=n*6rectfill(0,n,127,n+x*6-1,0)if(x>21)rectfill(0,126,127,127,0)
np(l,0,n)print(h,0,n,s[4])if(A>=10and r~=false and not v)d(o*4,n+t*6)
end local function f(e)n(1)u-=1print("[enter] ('esc' to abort)",0,u*6,s[3])while true do flip()nf()for n in nd()do if(n=="•")X=true g=""G={}return false
if(n=="\r"or n=="\n")m+=e return true
end end end::n::local t,e if G or g then t,e=E(g,0,m)if e-m<=20and G then g,G=nb(g,G)t,e=E(g,0,m)if(#G==0and not v)G=nil
end end if(not v)camera()
if(m==0and not v)l(not g)
if g then local r,t=sub(g,t),min(e-m,20)n(t)V(r,0,(u-t)*6,s[1])if t<e-m then if(f(t))goto n
else local r,o,e=C(O,0)n(e)V(O,0,(u-e)*6,s[2])if(v)m+=t else a,x,_,c,m,g,O="",0,0,1,0l()
end end if(v)n(1)u-=1print(v,0,u*6,s[3])
if(B)n(1)u-=1print(B,0,u*6,s[3])B=nil
if P then P-=1if(P==0)B,P=""
end A-=1if(A==0)A=20
color(r)camera(o,i)if(u<=20)cursor(0,u*6)
end r,d,F=false,false,false j={}function nr(n,e)i,nw=n,e assert(false,n)end function W(n,t,l)return ni(n,l)(t or e)end function Y(n,e)return W("return "..n,e,true)end function nx(n)local e=cocreate(ni)::n::local n,e=coresume(e,n)if(n and not e)goto n
if(not n)e,i=i,false
return n,e end function n3(n,e)local n,e=C(n,e)return"line "..e+1 .." col "..n+1end function nu(e,l)G,X,i={},false,false r,d,F=false,false,false local t,r,n=cocreate(function()W(e)end)while true do r,n=coresume(t)if(costatus(t)=="dead")break
if M and not d then v="running, press 'esc' to abort"_draw()flip()v=nil else if(N and not d and not F)flip()
if(not N and holdframe)holdframe()
F=false end for n in nd()do if(n=="•")X=true else add(j,n)
end if(X)n="computation aborted"break
end if i==nil then if(l)n="unexpected end of code"else n,G=nil
end if(i)n,i=i.."\nat "..n3(e,nw)
O=n j={}end I=function()r=true yield()r=false end e.flip=function(...)local n=pack(flip(...))F=true I()return H(n)end e.coresume=function(n,...)local e=pack(coresume(n,...))while r do yield()e=pack(coresume(n))end i=false return H(e)end e.stat=function(n,...)if n==30then return#j>0or stat(n,...)elseif n==31then if#j>0then return deli(j,1)else local n=stat(n,...)if(n=="•")X=true
return n end else return stat(n,...)end end function nm(n)if(_set_fps)_set_fps(n._update60 and 60or 30)
if(n._init)n._init()
d=true while true do if(_update_buttons)_update_buttons()
if(holdframe)holdframe()
if n._update60 then n._update60()elseif n._update then n._update()end if(n._draw)n._draw()
flip()F=true I()end d=false end function ns(n)if q(n,{"i","interrupt"})then return M elseif q(n,{"f","flip"})then return N elseif q(n,{"r","repl"})then return J elseif q(n,{"mi","max_items"})then return S elseif q(n,{"h","hex"})then return T elseif q(n,{"cl","colors"})then return s elseif q(n,{"c","code"})then local n={[0]=a}for e=1,#w-1do n[e]=w[#w-e]end return n elseif q(n,{"cm","compile"})then return function(n)return nx(n)end elseif q(n,{"x","exec"})then return function(n,e)W(n,e)end elseif q(n,{"v","eval"})then return function(n,e)return Y(n,e)end elseif q(n,{"p","print"})then return function(n,...)e.print(f(n),...)end elseif q(n,{"ts","tostr"})then return function(n)return f(n)end elseif q(n,{"rst","reset"})then run()elseif q(n,{"run"})then nm(e)else assert(false,"unknown \\-command")end end function nh(e)local function t(n)return n and n~=0and true or false end local n if q(e,{"i","interrupt"})then n=function(n)M=t(n)end elseif q(e,{"f","flip"})then n=function(n)N=t(n)end elseif q(e,{"r","repl"})then n=function(n)J=t(n)end elseif q(e,{"mi","max_items"})then n=function(n)S=tonum(n)or-1end elseif q(e,{"h","hex"})then n=function(n)T=t(n)end elseif q(e,{"cl","colors"})then n=function(n)s=n end else assert(false,"unknown \\-command assign")end local n={__newindex=function(t,l,e)n(e)end}return setmetatable(n,n),0end Q=stat(4)K,R=0,false poke(24412,10,2)function k(n)if stat(28,n)then if(n~=nn)nn,K=n,0
return K==0or K>=10and K%2==0elseif nn==n then nn=nil end end function _update()local e=false local function t(t)local e,n,l=C(h..a,#h+c)if(ne)e=ne
n+=t if(not(n>=0and n<l))return false
c=max(E(h..a,e,n)-#h,1)ne=e A=20return true end local function o(t)local n,l=C(h..a,#h+c)n=t>0and 100or 0c=max(E(h..a,n,l)-#h,1)e=true end local function f(n)w[z]=a z+=n a=w[z]if n<0then c=#a+1else c=max(E(h..a,32,0)-#h,1)local n=b(a,c)if(n~=""and n~="\n")c-=1
end e=true end local function i()if#a>0then if(#w>50)del(w,w[1])
w[#w]=a add(w,"")z=#w e=true end end local function d(n)if(c+n>0)a=sub(a,1,c+n-1)..sub(a,c+n+1)c+=n e=true
end local function l(n)a=sub(a,1,c-1)..n..sub(a,c)c+=#n e=true end local r,u,n=stat(28,224)or stat(28,228),stat(28,225)or stat(28,229),-1if k(80)then if(c>1)c-=1e=true
elseif k(79)then if(c<=#a)c+=1e=true
elseif k(82)then if((r or not t(-1))and z>1)f(-1)
elseif k(81)then if((r or not t(1))and z<#w)f(1)
else local t=stat(31)n=ord(t)if t=="•"then if(#a==0)extcmd"pause"else G,O={}i()
elseif t=="\r"or t=="\n"then if u then l"\n"else nu(a)if(not G)l"\n"else i()
end elseif r and k(40)then nu(a,true)i()elseif t~=""and n>=32and n<154then if(R and n>=128)t=chr(n-63)
l(t)elseif n==193then l"\n"elseif n==192then o(-1)elseif n==196then o(1)elseif n==203then R=not R B,P="shift now selects "..(R and"punycase"or"symbols"),40elseif k(74)then if(r)c=1e=true else o(-1)
elseif k(77)then if(r)c=#a+1e=true else o(1)
elseif k(42)then d(-1)elseif k(76)then d(0)end end local t=stat(4)if(t~=Q or n==213)l(t)Q=t
if n==194or n==215then if a~=""and a~=Q then Q=a printh(a,"@clip")if(n==215)a=""c=1
B="press again to put in clipboard"else B=""end end if(stat(120))local n repeat n=serial(2048,24448,128)l(chr(peek(24448,n)))until n==0
if(e)A,ne=20
K+=1nf()end function na(n,e)local e,t=coresume(cocreate(e))if not e then printh("error #"..n..": "..t)print("error #"..n.."\npico8 broke something again,\nthis cart may not work.\npress any button to ignore")while(btnp()==0)flip()
cls()end end na(1,function()assert(pack(Y"(function (...) return ... end)(1,2,nil,nil)").n==4)end)na(2,function()assert(Y"function() local temp, temp2 = {max(1,3)}, -20;return temp[1] + temp2; end"()==-17)end)printh"finished"stop()while true do if(holdframe)holdframe()
_update()_draw()flip()end
__meta:title__
keep:------------------------------------
keep: Please see 'Commented Source Code' section in the BBS
