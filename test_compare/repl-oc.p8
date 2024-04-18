pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
--------------------------------------
-- Please see 'Commented Source Code' section in the BBS
-- for the original commented source code
-- (The below had the comments stripped due to cart size limits)
--------------------------------------
local t,█,▒=_ENV,{},{}for n,e in pairs(_ENV)do █[n]=e if(type(e)=="function")▒[n]=true
end local _ENV=█ A,V=true function f(t,e)for n=1,#e do if(sub(e,n,n)==t)return n
end end function e(e,n)return sub(e,n,n)end local 🐱,⬇️,█=split[[a,b,f,n,r,t,v,\,",',
,*,#,-,|,+,^]],split"⁷,⁸,ᶜ,\n,\r,	,ᵇ,\\,\",',\n,¹,²,³,⁴,⁵,⁶",{}for n=1,#🐱 do █[🐱[n]]=⬇️[n]end function g(n)return n>="0"and n<="9"end function z(n)return n>="A"and n<="Z"or n>="a"and n<="z"or n=="_"or n>="█"or g(n)end function か(r,n,i,o)local t=""while n<=#r do local l=e(r,n)if(l==i)break
if l=="\\"then n+=1local t=e(r,n)l=█[t]if t=="x"then t=tonum("0x"..sub(r,n+1,n+2))if(t)n+=2else o"bad hex escape"
l=chr(t)elseif g(t)then local i=n while(g(t)and n<i+3)n+=1t=e(r,n)
n-=1t=tonum(sub(r,i,n))if(not t or t>=256)o"bad decimal escape"
l=chr(t)elseif t=="z"then repeat n+=1t=e(r,n)until not f(t," \r	ᶜᵇ\n")if(t=="")o()
l=""n-=1elseif t==""then o()l=""end if(not l)o("bad escape: "..t)l=""
elseif l=="\n"then o"unterminated string"break end t..=l n+=1end if(n>#r)o("unterminated string",true)
return t,n+1end function W(t,n,l,r)if e(t,n)=="["then n+=1local r=n while(e(t,n)=="=")n+=1
local r="]"..sub(t,r,n-1).."]"local o=#r if e(t,n)=="["then n+=1if(e(t,n)=="\n")n+=1
local e=n while(n<=#t and sub(t,n,n+o-1)~=r)n+=1
if(n>=#t)l()
return sub(t,e,n-1),n+o end end if(r)l"invalid long brackets"
return nil,n end function Y(l,c)local n,s,o,h,b,p,u,i=1,1,{},{},{},{}local function d(n,e)if(c)゛(n,i)
u=n and not e end while n<=#l do i=n local t,a,r=e(l,n)if f(t," \r	ᶜᵇ\n")then n+=1a=true if(t=="\n")s+=1
elseif t=="-"and e(l,n+1)=="-"then n+=2if(e(l,n)=="[")r,n=W(l,n,d)
if not r then while(n<=#l and e(l,n)~="\n")n+=1
end if(c)a=true else add(o,true)
elseif g(t)or t=="."and g(e(l,n+1))then local u,a="0123456789",true if t=="0"and f(e(l,n+1),"xX")then u..="AaBbCcDdEeFf"n+=2elseif t=="0"and f(e(l,n+1),"bB")then u="01"n+=2end while(true)t=e(l,n)if t=="."and a then a=false elseif not f(t,u)then break end n+=1
r=sub(l,i,n-1)if(not tonum(r))d"bad number"r="0"
add(o,tonum(r))elseif z(t)then while(z(e(l,n)))n+=1
add(o,sub(l,i,n-1))elseif t=="'"or t=='"'then r,n=か(l,n+1,t,d)add(o,{t=r})elseif t=="["and f(e(l,n+1),"=[")then r,n=W(l,n,d,true)add(o,{t=r})else n+=1local e,r,u=unpack(split(sub(l,n,n+2),""))if e==t and r==t and f(t,".>")then n+=2if(u=="="and f(t,">"))n+=1
elseif e==t and r~=t and f(t,"<>")and f(r,"<>")then n+=2if(u=="=")n+=1
elseif e==t and f(t,".:^<>")then n+=1if(r=="="and f(t,".^<>"))n+=1
elseif e=="="and f(t,"+-*/\\%^&|<>=~!")then n+=1elseif f(t,"+-*/\\%^&|<>=~#(){}[];,?@$.:")then else d("bad char: "..t)end add(o,sub(l,i,n-1))end if(not a)add(h,s)add(b,i)add(p,n-1)
if(u)o[#o],u=false,false
end return o,h,b,p end function r(t,n)for e=1,#n do if(n[e]==t)return e
end end function c(n)return unpack(n,1,n.n)end function き(e)local n={}for e,t in next,e do n[e]=t end return n end local W=split"and,break,do,else,elseif,end,false,for,function,goto,if,in,local,nil,not,or,repeat,return,then,true,until,while"q={}for n in all(W)do q[n]=true end local function W(n)return type(n)=="string"and e(n,#n)=="="end ゜=split"end,else,elseif,until"function あ(n,F)local o,E,l=Y(n,true)local n,f,s,v,d,p,x,t,b,y,h,B=1,0,0,{}local function i(e)゛(e,l[n-1]or 1)end local function g(n)return function()return n end end local function X(e)local n=d[e]if(n)return function(t)return t[n][e]end else n=d._ENV return function(t)return t[n]._ENV[e]end
end local function j()local n=d["..."]if(not n or n~=B)i"unexpected '...'"
return function(e)return c(e[n]["..."])end end local function C(e)local n=d[e]if(n)return function(t)return t[n],e end else n=d._ENV return function(t)return t[n]._ENV,e end
end local function l(e)local t=o[n]n+=1if(t==e)return
if(t==nil)i()
i("expected: "..e)end local function u(t)if(not t)t=o[n]n+=1
if(t==nil)i()
if(type(t)=="string"and z(e(t,1))and not q[t])return t
if(type(t)=="string")i("invalid identifier: "..t)
i"identifier expected"end local function e(e)if(o[n]==e)n+=1return true
end local function _()d=setmetatable({},{__index=d})f+=1end local function z()d=getmetatable(d).__index f-=1end local function m(l,t)local e,n={},#t for n=1,n-1do e[n]=t[n](l)end if n>0then local t=pack(t[n](l))if(t.n~=1)for l=1,t.n do e[n+l-1]=t[l]end n+=t.n-1else e[n]=t[1]
end e.n=n return e end local function k(t)local n={}add(n,(t()))while(e",")add(n,(t()))
return n end local function Z(r,o,i)local n={}if i then add(n,i)elseif not e")"then while true do add(n,(t()))if(e")")break
l","end end if(o)return function(e)local t=r(e)return t[o](t,c(m(e,n)))end,true,nil,function(e)local t=r(e)return t[o],pack(t,c(m(e,n)))end else return function(e)return r(e)(c(m(e,n)))end,true,nil,function(e)return r(e),m(e,n)end
end local function q()local r,d,c,a={},{},1while not e"}"do a=nil local i,f if e"["then i=t()l"]"l"="f=t()elseif o[n+1]=="="then i=g(u())l"="f=t()else i=g(c)f=t()c+=1a=#r+1end add(r,i)add(d,f)if(e"}")break
if(not e";")l","
end return function(e)local t={}for n=1,#r do if(n==a)local l,n=r[n](e),pack(d[n](e))for e=1,n.n do t[l+e-1]=n[e]end else t[r[n](e)]=d[n](e)
end return t end end local function D(o,a)local n,p,t if o then if a then _()n=u()d[n]=f t=C(n)else n={u()}while(e".")add(n,u())
if(e":")add(n,u())p=true
if(#n==1)t=C(n[1])else local e=X(n[1])for t=2,#n-1do local l=e e=function(e)return l(e)[n[t]]end end t=function(t)return e(t),n[#n]end
end end local n,r={}if(p)add(n,"self")
l"("if not e")"then while true do if(e"...")r=true else add(n,u())
if(e")")break
l","if(r)i"unexpected param after '...'"
end end _()for n in all(n)do d[n]=f end if(r)d["..."]=f
local e,i,d=v,h,B v,h,B={},s+1,f local f=b()for n in all(v)do n()end v,h,B=e,i,d l"end"z()return function(e)if(a)add(e,{})
local l=き(e)local i=#l local n=function(...)local t,e=pack(...),l if(#e~=i)local n={}for t=0,i do n[t]=e[t]end e=n
local l={}for e=1,#n do l[n[e]]=t[e]end if(r)l["..."]=pack(unpack(t,#n+1,t.n))
add(e,l)local n=f(e)deli(e)if n then if(type(n)=="table")return c(n)
return n()end end if(o)local e,t=t(e)e[t]=n else return n
end end local function B()local e=o[n]n+=1local n if(e==nil)i()
if(e=="nil")return g()
if(e=="true")return g(true)
if(e=="false")return g(false)
if(type(e)=="number")return g(e)
if(type(e)=="table")return g(e.t)
if(e=="{")return q()
if(e=="(")n=t()l")"return function(e)return(n(e))end,true
if(e=="-")n=t(11)return function(e)return-n(e)end
if(e=="~")n=t(11)return function(e)return~n(e)end
if(e=="not")n=t(11)return function(e)return not n(e)end
if(e=="#")n=t(11)return function(e)return#n(e)end
if(e=="@")n=t(11)return function(e)return@n(e)end
if(e=="%")n=t(11)return function(e)return%n(e)end
if(e=="$")n=t(11)return function(e)return$n(e)end
if(e=="function")return D()
if(e=="...")return j()
if(e=="\\")n=u()return function()return く(n)end,true,function()return け(n)end
if(u(e))return X(e),true,C(e)
i("unexpected token: "..e)end local function C(e,t,l,r)local n if(e=="^"and t<=12)n=r(12)return function(e)return l(e)^n(e)end
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
end local function j(d,e,a)local i=o[n]n+=1local r,f if a then if(i==".")r=u()return function(n)return e(n)[r]end,true,function(n)return e(n),r end
if(i=="[")r=t()l"]"return function(n)return e(n)[r(n)]end,true,function(n)return e(n),r(n)end
if(i=="(")return Z(e)
if(i=="{"or type(i)=="table")n-=1f=B()return Z(e,nil,f)
if i==":"then r=u()if(o[n]=="{"or type(o[n])=="table")f=B()return Z(e,r,f)
l"("return Z(e,r)end end local e=C(i,d,e,t)if(not e)n-=1
return e end t=function(r)local n,e,t,l=B()while true do local r,o,i,f=j(r or 0,n,e)if(not r)break
n,e,t,l=r,o,i,f end return n,t,l end local function B()local e,n=t()if(not n)i"cannot assign to value"
return n end local function j()local n=k(B)l"="local e=k(t)if(#n==1and#e==1)return function(t)local n,l=n[1](t)n[l]=e[1](t)end else return function(t)local l,r={},{}for e=1,#n do local n,e=n[e](t)add(l,n)add(r,e)end local e=m(t,e)for n=#n,1,-1do l[n][r[n]]=e[n]end end
end local function q(e,l)local r=o[n]n+=1local n=sub(r,1,-2)local n=C(n,0,e,function()return t()end)if(not n)i"invalid compound assignment"
return function(e)local t,l=l(e)t[l]=n(e)end end local function G()if e"function"then return D(true,true)else local n,e=k(u),e"="and k(t)or{}_()for e=1,#n do d[n[e]]=f end if(#n==1and#e==1)return function(t)add(t,{[n[1]]=e[1](t)})end else return function(t)local l,r={},m(t,e)for e=1,#n do l[n[e]]=r[e]end add(t,l)end
end end local function C(e)local t=E[n-1]x=function()return t~=E[n]end if(not e or x())i(n<=#o and"bad shorthand"or nil)
end local function E()local r,o,t,n=o[n]=="(",t()if e"then"then t,n=b()if e"else"then n=b()l"end"elseif e"elseif"then n=E()else l"end"end else C(r)t=b()if(not x()and e"else")n=b()
x=nil end return function(e)if o(e)then return t(e)elseif n then return n(e)end end end local function B(...)local n=y y=s+1local e=b(...)y=n return e end local function Z(n,e)if(n==true)return
return n,e end local function H()local r,t,n=o[n]=="(",t()if(e"do")n=B()l"end"else C(r)n=B()x=nil
return function(e)while t(e)do if(stat(1)>=1)w()
local n,e=n(e)if(n)return Z(n,e)
end end end local function C()local r,e=f,B(true)l"until"local l=t()while(f>r)z()
return function(n)repeat if(stat(1)>=1)w()
local e,t=e(n)if(not e)t=l(n)
while(#n>r)deli(n)
if(e)return Z(e,t)
until t end end local function I()if o[n+1]=="="then local r=u()l"="local o=t()l","local i,e=t(),e","and t()or g(1)l"do"_()d[r]=f local t=B()l"end"z()return function(n)for e=o(n),i(n),e(n)do if(stat(1)>=1)w()
add(n,{[r]=e})local e,t=t(n)deli(n)if(e)return Z(e,t)
end end else local r=k(u)l"in"local e=k(t)l"do"_()for n in all(r)do d[n]=f end local o=B()l"end"z()return function(n)local e=m(n,e)while true do local l,t={},{e[1](e[2],e[3])}if(t[1]==nil)break
e[3]=t[1]for n=1,#r do l[r[n]]=t[n]end if(stat(1)>=1)w()
add(n,l)local e,t=o(n)deli(n)if(e)return Z(e,t)
end end end end local function g()if(not y or h and y<h)i"break outside of loop"
return function()return true end end local function y()if(not h and not F)i"return outside of function"
if o[n]==";"or r(o[n],゜)or x and x()then return function()return pack()end else local n,r,l=t()local n={n}while(e",")add(n,(t()))
if#n==1and l and h then return function(n)local n,e=l(n)if(stat(1)>=1)w()
return function()return n(c(e))end end else return function(e)return m(e,n)end end end end local function _(e)local n=u()l"::"if(p[n]and p[n].e==s)i"label already defined"
p[n]={l=f,e=s,o=e,r=#e}end local function B()local t,e,l,n=u(),p,f add(v,function()n=e[t]if(not n)i"label not found"
if(h and n.e<h)i"goto outside of function"
local e=e[n.e]or l if(n.l>e and n.r<#n.o)i"goto past local"
end)return function()if(stat(1)>=1)w()
return 0,n end end local function u(f)local r=o[n]n+=1if(r==";")return
if(r=="do")local n=b()l"end"return n
if(r=="if")return E()
if(r=="while")return H()
if(r=="repeat")return C()
if(r=="for")return I()
if(r=="break")return g()
if(r=="return")return y(),true
if(r=="local")return G()
if(r=="goto")return B()
if(r=="::")return _(f)
if(r=="function"and o[n]~="(")return D(true)
if(r=="?")local e,t=X"print",k(t)return function(n)e(n)(c(m(n,t)))end
n-=1local r,t,f,l=n,t()if e","or e"="then n=r return j()elseif W(o[n])then return q(t,f)elseif s<=1and A then return function(n)local n=pack(t(n))if(not(l and n.n==0))add(a,n)
V=n[1]end else if(not l)i"statement has no effect"
return function(n)t(n)end end end b=function(t)p=setmetatable({},{__index=p})p[s]=f s+=1local d,i,l=s,t and 32767or f,{}while n<=#o and not r(o[n],゜)and not(x and x())do local n,t=u(l)if(n)add(l,n)
if(t)e";"break
end while(f>i)z()
s-=1p=getmetatable(p).__index return function(e)local r,o,t,n=1,#l while r<=o do t,n=l[r](e)if t then if(type(t)~="number")break
if(n.e~=d)break
r=n.r while(#e>n.l)deli(e)
t,n=nil end r+=1end while(#e>i)deli(e)
return t,n end end d=A and{_ENV=0,_env=0,_=0}or{_ENV=0}local e=b()if(n<=#o)i"unexpected end"
for n in all(v)do n()end return function(n)local n=A and{_ENV=n,_env=n,_=V}or{_ENV=n}local n=e{[0]=n}if(n)return c(n)
end end N,O=10,false local V={["\0"]="000",["ᵉ"]="014",["ᶠ"]="015"}for n,e in pairs(█)do if(not f(n,"'\n"))V[e]=n
end function こ(n)local t=1while t<=#n do local e=e(n,t)local e=V[e]if(e)n=sub(n,1,t-1).."\\"..e..sub(n,t+1)t+=#e
t+=1end return'"'..n..'"'end function さ(n)if(type(n)~="string")return false
if(q[n])return false
if(#n==0or g(e(n,1)))return false
for t=1,#n do if(not z(e(n,t)))return false
end return true end function B(e,t)local n=type(e)if n=="nil"then return"nil"elseif n=="boolean"then return e and"true"or"false"elseif n=="number"then return tostr(e,O)elseif n=="string"then return こ(e)elseif n=="table"and not t then local n,t,r="{",0,0for e,l in next,e do if(t==N)n=n..",<...>"break
if(t>0)n=n..","
local l=B(l,1)if e==r+1then n=n..l r=e elseif さ(e)then n=n..e.."="..l else n=n.."["..B(e,1).."]="..l end t+=1end return n.."}"else return"<"..tostr(n)..">"end end function し(n,e)if(e==nil)return n
if(not n)n=""
local t=min(21,#e)for t=1,t do if(#n>0)n..="\n"
local t=e[t]if type(t)=="table"then local e=""for n=1,t.n do if(#e>0)e=e..", "
e=e..B(t[n])end n..=e else n..=t end end local l={}for n=t+1,#e do l[n-t]=e[n]end return n,l end poke(24365,1)cls()d="> "n,s,k="",1,0l,v=1,20u,y={""},1Z=false h,o=0,1G,H=true,true i={7,4,3,5,6,8,5,12,14,7,11,5}t.print=function(n,...)if(pack(...).n~=0or not G)return print(n,...)
add(a,tostr(n))end function い()poke(24368,1)end function う()return function()if(stat(30))return stat(31)
end end function P(r,o)local t,n,l=1,0,0if(not r)return t,n,l
while t<=#r do local e=e(r,t)local r=e>="█"if(n>=(r and 31or 32))l+=1n=0
if(o)o(t,e,n,l)
if(e=="\n")l+=1n=0else n+=r and 2or 1
t+=1end return t,n,l end function X(t,l)local n,e=0,0local o,r,t=P(t,function(t,i,r,o)if(l==t)n,e=r,o
end)if(l>=o)n,e=r,t
if(r>0)t+=1
return n,e,t end function C(l,r,e)local t,n=1,false local r,o,l=P(l,function(o,f,i,l)if(e==l and r==i and not n)t=o n=true
if((e<l or e==l and r<i)and not n)t=o-1n=true
end)if(not n)t=e>=l and r or r-1
if(o>0)l+=1
return t,l end function Q(n,t,l,e)if(type(e)=="function")P(n,function(n,r,o,i)print(r,t+o*4,l+i*6,e(n))end)else print(n and"⁶rw"..n,t,l,e)
end function す(n,o,f)local d,t,u,l=Y(n)local t=1Q(n,o,f,function(o)while(t<=#l and l[t]<o)t+=1
local n if(t<=#l and u[t]<=o)n=d[t]
local t=i[5]if n==false then t=i[6]elseif n==true then t=i[7]elseif type(n)~="string"or r(n,{"nil","true","false"})then t=i[8]elseif q[n]then t=i[9]elseif not z(e(n,1))then t=i[10]elseif ▒[n]then t=i[11]end return t end)end function _draw()local u,c,p=peek(24357),peek2(24360),peek2(24362)camera()local function e(n)cursor(0,127)for n=1,n do rectfill(0,o*6,127,(o+1)*6-1,0)if(o<21)o+=1else print""
end end local function w(n,e)for n=1,n do if(o>e)o-=1
rectfill(0,o*6,127,(o+1)*6-1,0)end end local function m(n,e)for t=0,2do local l=pget(n+t,e+5)pset(n+t,e+5,l==0and i[12]or 0)end end local function f(f)local r=d..n.." "local l,t,n=X(r,#d+l)if n>s then e(n-s)elseif n<s then w(s-n,n)end s=n k=mid(k,0,max(s-21,0))::n::local n=o-s+k if(n+t<0)k+=1goto n
if(n+t>=21)k-=1goto n
local n=n*6rectfill(0,n,127,n+s*6-1,0)if(s>21)rectfill(0,126,127,127,0)
す(r,0,n)print(d,0,n,i[4])if(v>=10and f~=false and not x)m(l*4,n+t*6)
end local function d(t)e(1)o-=1print("[enter] ('esc' to abort)",0,o*6,i[3])while true do flip()い()for n in う()do if(n=="•")Z=true b=""a={}return false
if(n=="\r"or n=="\n")h+=t return true
end end end::n::local r,t if a or b then r,t=C(b,0,h)if t-h<=20and a then b,a=し(b,a)r,t=C(b,0,h)if(#a==0and not x)a=nil
end end if(not x)camera()
if(h==0and not x)f(not b)
if b then local u,r=sub(b,r),min(t-h,20)e(r)Q(u,0,(o-r)*6,i[1])if r<t-h then if(d(r))goto n
else local d,u,t=X(I,0)e(t)Q(I,0,(o-t)*6,i[2])if(x)h+=r else n,s,k,l,h,b,I="",0,0,1,0f()
end end if(x)e(1)o-=1print(x,0,o*6,i[3])
if(_)e(1)o-=1print(_,0,o*6,i[3])_=nil
if J then J-=1if(J==0)_,J=""
end v-=1if(v==0)v=20
color(u)camera(c,p)if(o<=20)cursor(0,o*6)
end K,D,E=false,false,false F={}function ゛(n,e)m,せ=n,e assert(false,n)end function R(n,e,l)return あ(n,l)(e or t)end function S(n,e)return R("return "..n,e,true)end function そ(n)local e=cocreate(あ)::n::local n,e=coresume(e,n)if(n and not e)goto n
if(not n)e,m=m,false
return n,e end function た(n,e)local n,e=X(n,e)return"line "..e+1 .." col "..n+1end function え(e,l)a,Z,m={},false,false K,D,E=false,false,false local t,r,n=cocreate(function()R(e)end)while true do r,n=coresume(t)if(costatus(t)=="dead")break
if G and not D then x="running, press 'esc' to abort"_draw()flip()x=nil else if(H and not D and not E)flip()
if(not H and holdframe)holdframe()
E=false end for n in う()do if(n=="•")Z=true else add(F,n)
end if(Z)n="computation aborted"break
end if m==nil then if(l)n="unexpected end of code"else n,a=nil
end if(m)n,m=m.."\nat "..た(e,せ)
I=n F={}end w=function()K=true yield()K=false end t.flip=function(...)local n=pack(flip(...))E=true w()return c(n)end t.coresume=function(n,...)local e=pack(coresume(n,...))while(K)yield()e=pack(coresume(n))
m=false return c(e)end t.stat=function(n,...)if n==30then return#F>0or stat(n,...)elseif n==31then if#F>0then return deli(F,1)else local n=stat(n,...)if(n=="•")Z=true
return n end else return stat(n,...)end end function ち(n)if(_set_fps)_set_fps(n._update60 and 60or 30)
if(n._init)n._init()
D=true while true do if(_update_buttons)_update_buttons()
if(holdframe)holdframe()
if n._update60 then n._update60()elseif n._update then n._update()end if(n._draw)n._draw()
flip()E=true w()end D=false end function く(e)if r(e,{"i","interrupt"})then return G elseif r(e,{"f","flip"})then return H elseif r(e,{"r","repl"})then return A elseif r(e,{"mi","max_items"})then return N elseif r(e,{"h","hex"})then return O elseif r(e,{"cl","colors"})then return i elseif r(e,{"c","code"})then local n={[0]=n}for e=1,#u-1do n[e]=u[#u-e]end return n elseif r(e,{"cm","compile"})then return function(n)return そ(n)end elseif r(e,{"x","exec"})then return function(n,e)R(n,e)end elseif r(e,{"v","eval"})then return function(n,e)return S(n,e)end elseif r(e,{"p","print"})then return function(n,...)t.print(B(n),...)end elseif r(e,{"ts","tostr"})then return function(n)return B(n)end elseif r(e,{"rst","reset"})then run()elseif r(e,{"run"})then ち(t)else assert(false,"unknown \\-command")end end function け(e)local function t(n)return n and n~=0and true or false end local n if r(e,{"i","interrupt"})then n=function(n)G=t(n)end elseif r(e,{"f","flip"})then n=function(n)H=t(n)end elseif r(e,{"r","repl"})then n=function(n)A=t(n)end elseif r(e,{"mi","max_items"})then n=function(n)N=tonum(n)or-1end elseif r(e,{"h","hex"})then n=function(n)O=t(n)end elseif r(e,{"cl","colors"})then n=function(n)i=n end else assert(false,"unknown \\-command assign")end local n={__newindex=function(t,l,e)n(e)end}return setmetatable(n,n),0end L=stat(4)j,M=0,false poke(24412,10,2)function p(n)if stat(28,n)then if(n~=T)T,j=n,0
return j==0or j>=10and j%2==0elseif T==n then T=nil end end function _update()local t=false local function r(r)local t,e,o=X(d..n,#d+l)if(U)t=U
e+=r if(not(e>=0and e<o))return false
l=max(C(d..n,t,e)-#d,1)U=t v=20return true end local function f(r)local e,o=X(d..n,#d+l)e=r>0and 100or 0l=max(C(d..n,e,o)-#d,1)t=true end local function c(r)u[y]=n y+=r n=u[y]if r<0then l=#n+1else l=max(C(d..n,32,0)-#d,1)local n=e(n,l)if(n~=""and n~="\n")l-=1
end t=true end local function d()if#n>0then if(#u>50)del(u,u[1])
u[#u]=n add(u,"")y=#u t=true end end local function s(e)if(l+e>0)n=sub(n,1,l+e-1)..sub(n,l+e+1)l+=e t=true
end local function o(e)n=sub(n,1,l-1)..e..sub(n,l)l+=#e t=true end local i,h,e=stat(28,224)or stat(28,228),stat(28,225)or stat(28,229),-1if p(80)then if(l>1)l-=1t=true
elseif p(79)then if(l<=#n)l+=1t=true
elseif p(82)then if((i or not r(-1))and y>1)c(-1)
elseif p(81)then if((i or not r(1))and y<#u)c(1)
else local r=stat(31)e=ord(r)if r=="•"then if(#n==0)extcmd"pause"else a,I={}d()
elseif r=="\r"or r=="\n"then if h then o"\n"else え(n)if(not a)o"\n"else d()
end elseif i and p(40)then え(n,true)d()elseif r~=""and e>=32and e<154then if(M and e>=128)r=chr(e-63)
o(r)elseif e==193then o"\n"elseif e==192then f(-1)elseif e==196then f(1)elseif e==203then M=not M _,J="shift now selects "..(M and"punycase"or"symbols"),40elseif p(74)then if(i)l=1t=true else f(-1)
elseif p(77)then if(i)l=#n+1t=true else f(1)
elseif p(42)then s(-1)elseif p(76)then s(0)end end local r=stat(4)if(r~=L or e==213)o(r)L=r
if e==194or e==215then if n~=""and n~=L then L=n printh(n,"@clip")if(e==215)n=""l=1
_="press again to put in clipboard"else _=""end end if(stat(120))local n repeat n=serial(2048,24448,128)o(chr(peek(24448,n)))until n==0
if(t)v,U=20
j+=1い()end function お(n,e)local e,t=coresume(cocreate(e))if not e then printh("error #"..n..": "..t)print("error #"..n.."\npico8 broke something again,\nthis cart may not work.\npress any button to ignore")while(btnp()==0)flip()
cls()end end お(1,function()assert(pack(S"(function (...) return ... end)(1,2,nil,nil)").n==4)end)お(2,function()assert(S"function() local temp, temp2 = {max(1,3)}, -20;return temp[1] + temp2; end"()==-17)end)printh"finished"stop()while true do if(holdframe)holdframe()
_update()_draw()flip()end
__meta:title__
keep:------------------------------------
keep: Please see 'Commented Source Code' section in the BBS
