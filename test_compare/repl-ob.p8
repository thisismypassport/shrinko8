pico-8 cartridge // http://www.pico-8.com
version 38
__lua__
--------------------------------------
-- Please see 'Commented Source Code' section in the BBS
-- for the original commented source code
-- (The below had the comments stripped due to cart size limits)
--------------------------------------
local t,eu,ea=_ENV,{},{}for n,e in pairs(_ENV)do eu[n]=e if(type(e)=="function")ea[n]=true
end local _ENV=eu j,n5=true function f(t,e)for n=1,#e do if(sub(e,n,n)==t)return n
end end function e(t,n)return sub(t,n,n)end local ec,e1=split"a,b,f,n,r,t,v,\\,\",',\n,*,#,-,|,+,^",split"⁷,⁸,ᶜ,\n,\r,	,ᵇ,\\,\",',\n,¹,²,³,⁴,⁵,⁶"local eu={}for n=1,#ec do eu[ec[n]]=e1[n]end function g(n)return n>="0"and n<="9"end function q(n)return n>="A"and n<="Z"or n>="a"and n<="z"or n=="_"or n>="█"or g(n)end function nz(r,n,i,o)local t=""while n<=#r do local l=e(r,n)if(l==i)break
if l=="\\"then n+=1local t=e(r,n)l=eu[t]if t=="x"then t=tonum("0x"..sub(r,n+1,n+2))if(t)n+=2else o"bad hex escape"
l=chr(t)elseif g(t)then local i=n while g(t)and n<i+3do n+=1t=e(r,n)end n-=1t=tonum(sub(r,i,n))if(not t or t>=256)o"bad decimal escape"
l=chr(t)elseif t=="z"then repeat n+=1t=e(r,n)until not f(t," \r	ᶜᵇ\n")if(t=="")o()
l=""n-=1elseif t==""then o()l=""end if(not l)o("bad escape: "..t)l=""
elseif l=="\n"then o"unterminated string"break end t..=l n+=1end if(n>#r)o("unterminated string",true)
return t,n+1end function n6(t,n,l,r)if e(t,n)=="["then n+=1local o=n while(e(t,n)=="=")n+=1
local r="]"..sub(t,o,n-1).."]"local o=#r if e(t,n)=="["then n+=1if(e(t,n)=="\n")n+=1
local e=n while(n<=#t and sub(t,n,n+o-1)~=r)n+=1
if(n>=#t)l()
return sub(t,e,n-1),n+o end end if(r)l"invalid long brackets"
return nil,n end function ng(l,c)local n,s,i=1,1local o,h,b,p,u={},{},{},{}local function d(n,e)if(c)n8(n,i)
u=n and not e end while n<=#l do i=n local t=e(l,n)local a,r if f(t," \r	ᶜᵇ\n")then n+=1a=true if(t=="\n")s+=1
elseif t=="-"and e(l,n+1)=="-"then n+=2if(e(l,n)=="[")r,n=n6(l,n,d)
if not r then while(n<=#l and e(l,n)~="\n")n+=1
end if(c)a=true else add(o,true)
elseif g(t)or t=="."and g(e(l,n+1))then local u,a="0123456789",true if t=="0"and f(e(l,n+1),"xX")then u..="AaBbCcDdEeFf"n+=2elseif t=="0"and f(e(l,n+1),"bB")then u="01"n+=2end while true do t=e(l,n)if t=="."and a then a=false elseif not f(t,u)then break end n+=1end r=sub(l,i,n-1)if(not tonum(r))d"bad number"r="0"
add(o,tonum(r))elseif q(t)then while q(e(l,n))do n+=1end add(o,sub(l,i,n-1))elseif t=="'"or t=='"'then r,n=nz(l,n+1,t,d)add(o,{t=r})elseif t=="["and f(e(l,n+1),"=[")then r,n=n6(l,n,d,true)add(o,{t=r})else n+=1local e,r,u=unpack(split(sub(l,n,n+2),""))if e==t and r==t and f(t,".>")then n+=2if(u=="="and f(t,">"))n+=1
elseif e==t and r~=t and f(t,"<>")and f(r,"<>")then n+=2if(u=="=")n+=1
elseif e==t and f(t,".:^<>")then n+=1if(r=="="and f(t,".^<>"))n+=1
elseif e=="="and f(t,"+-*/\\%^&|<>=~!")then n+=1elseif f(t,"+-*/\\%^&|<>=~#(){}[];,?@$.:")then else d("bad char: "..t)end add(o,sub(l,i,n-1))end if(not a)add(h,s)add(b,i)add(p,n-1)
if(u)o[#o],u=false,false
end return o,h,b,p end function r(t,n)for e=1,#n do if(n[e]==t)return e
end end function c(n)return unpack(n,1,n.n)end function nj(e)local n={}for t,l in next,e do n[t]=l end return n end local n6=split"and,break,do,else,elseif,end,false,for,function,goto,if,in,local,nil,not,or,repeat,return,then,true,until,while"nd={}for n in all(n6)do nd[n]=true end local function n6(n)return type(n)=="string"and e(n,#n)=="="end nk=split"end,else,elseif,until"function n4(n,ni)local o,no,l=ng(n,true)local n,f,s,y,h,nn=1,0,0local t,b local v,d,p,x={}local function i(e)n8(e,l[n-1]or 1)end local function g(n)return function()return n end end local function nt(e)local n=d[e]if n then return function(t)return t[n][e]end else n=d._ENV return function(t)return t[n]._ENV[e]end end end local function nf()local n=d["..."]if(not n or n~=nn)i"unexpected '...'"
return function(e)return c(e[n]["..."])end end local function nl(e)local n=d[e]if n then return function(t)return t[n],e end else n=d._ENV return function(t)return t[n]._ENV,e end end end local function l(e)local t=o[n]n+=1if(t==e)return
if(t==nil)i()
i("expected: "..e)end local function u(t)if(not t)t=o[n]n+=1
if(t==nil)i()
if(type(t)=="string"and q(e(t,1))and not nd[t])return t
if(type(t)=="string")i("invalid identifier: "..t)
i"identifier expected"end local function e(t)if(o[n]==t)n+=1return true
end local function z()d=setmetatable({},{__index=d})f+=1end local function q()d=getmetatable(d).__index f-=1end local function m(r,l)local e={}local n=#l for t=1,n-1do e[t]=l[t](r)end if n>0then local t=pack(l[n](r))if t.n~=1then for l=1,t.n do e[n+l-1]=t[l]end n+=t.n-1else e[n]=t[1]end end e.n=n return e end local function k(t)local n={}add(n,(t()))while e","do add(n,(t()))end return n end local function ne(r,o,i)local n={}if i then add(n,i)elseif not e")"then while true do add(n,(t()))if(e")")break
l","end end if o then return function(e)local t=r(e)return t[o](t,c(m(e,n)))end,true,nil,function(e)local t=r(e)return t[o],pack(t,c(m(e,n)))end else return function(e)return r(e)(c(m(e,n)))end,true,nil,function(e)return r(e),m(e,n)end end end local function nd()local r,d={},{}local c,a=1while not e"}"do a=nil local i,f if e"["then i=t()l"]"l"="f=t()elseif o[n+1]=="="then i=g(u())l"="f=t()else i=g(c)f=t()c+=1a=#r+1end add(r,i)add(d,f)if(e"}")break
if(not e";")l","
end return function(e)local t={}for n=1,#r do if n==a then local o,l=r[n](e),pack(d[n](e))for n=1,l.n do t[o+n-1]=l[n]end else t[r[n](e)]=d[n](e)end end return t end end local function nr(o,a)local n,p,t if o then if a then z()n=u()d[n]=f t=nl(n)else n={u()}while(e".")add(n,u())
if(e":")add(n,u())p=true
if#n==1then t=nl(n[1])else local e=nt(n[1])for t=2,#n-1do local l=e e=function(e)return l(e)[n[t]]end end t=function(t)return e(t),n[#n]end end end end local n,r={}if(p)add(n,"self")
l"("if not e")"then while true do if(e"...")r=true else add(n,u())
if(e")")break
l","if(r)i"unexpected param after '...'"
end end z()for e in all(n)do d[e]=f end if(r)d["..."]=f
local e,i,d=v,h,nn v,h,nn={},s+1,f local u=b()for n in all(v)do n()end v,h,nn=e,i,d l"end"q()return function(e)if(a)add(e,{})
local l=nj(e)local i=#l local f=function(...)local t=pack(...)local e=l if#e~=i then local n={}for t=0,i do n[t]=e[t]end e=n end local l={}for e=1,#n do l[n[e]]=t[e]end if(r)l["..."]=pack(unpack(t,#n+1,t.n))
add(e,l)local n=u(e)deli(e)if n then if(type(n)=="table")return c(n)
return n()end end if(o)local n,l=t(e)n[l]=f else return f
end end local function nn()local e=o[n]n+=1local n if(e==nil)i()
if(e=="nil")return g()
if(e=="true")return g(true)
if(e=="false")return g(false)
if(type(e)=="number")return g(e)
if(type(e)=="table")return g(e.t)
if(e=="{")return nd()
if(e=="(")n=t()l")"return function(e)return(n(e))end,true
if(e=="-")n=t(11)return function(e)return-n(e)end
if(e=="~")n=t(11)return function(e)return~n(e)end
if(e=="not")n=t(11)return function(e)return not n(e)end
if(e=="#")n=t(11)return function(e)return#n(e)end
if(e=="@")n=t(11)return function(e)return@n(e)end
if(e=="%")n=t(11)return function(e)return%n(e)end
if(e=="$")n=t(11)return function(e)return$n(e)end
if(e=="function")return nr()
if(e=="...")return nf()
if(e=="\\")n=u()return function()return nq(n)end,true,function()return en(n)end
if(u(e))return nt(e),true,nl(e)
i("unexpected token: "..e)end local function nl(e,t,l,r)local n if(e=="^"and t<=12)n=r(12)return function(e)return l(e)^n(e)end
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
end local function nf(d,e,a)local i=o[n]n+=1local r,f if a then if(i==".")r=u()return function(n)return e(n)[r]end,true,function(n)return e(n),r end
if(i=="[")r=t()l"]"return function(n)return e(n)[r(n)]end,true,function(n)return e(n),r(n)end
if(i=="(")return ne(e)
if(i=="{"or type(i)=="table")n-=1f=nn()return ne(e,nil,f)
if i==":"then r=u()if(o[n]=="{"or type(o[n])=="table")f=nn()return ne(e,r,f)
l"("return ne(e,r)end end local l=nl(i,d,e,t)if(not l)n-=1
return l end t=function(o)local n,e,t,l=nn()while true do local r,i,f,d=nf(o or 0,n,e)if(not r)break
n,e,t,l=r,i,f,d end return n,t,l end local function nn()local e,n=t()if(not n)i"cannot assign to value"
return n end local function nf()local n=k(nn)l"="local e=k(t)if#n==1and#e==1then return function(t)local l,r=n[1](t)l[r]=e[1](t)end else return function(t)local l,r={},{}for e=1,#n do local o,i=n[e](t)add(l,o)add(r,i)end local o=m(t,e)for e=#n,1,-1do l[e][r[e]]=o[e]end end end end local function nd(e,l)local r=o[n]n+=1local o=sub(r,1,-2)local n=nl(o,0,e,function()return t()end)if(not n)i"invalid compound assignment"
return function(e)local t,r=l(e)t[r]=n(e)end end local function nu()if e"function"then return nr(true,true)else local n=k(u)local l=e"="and k(t)or{}z()for e=1,#n do d[n[e]]=f end if#n==1and#l==1then return function(e)add(e,{[n[1]]=l[1](e)})end else return function(e)local t={}local r=m(e,l)for e=1,#n do t[n[e]]=r[e]end add(e,t)end end end end local function nl(e)local t=no[n-1]x=function()return t~=no[n]end if(not e or x())i(n<=#o and"bad shorthand"or nil)
end local function no()local r=o[n]=="("local o=t()local t,n if e"then"then t,n=b()if e"else"then n=b()l"end"elseif e"elseif"then n=no()else l"end"end else nl(r)t=b()if(not x()and e"else")n=b()
x=nil end return function(e)if o(e)then return t(e)elseif n then return n(e)end end end local function nn(...)local n=y y=s+1local e=b(...)y=n return e end local function ne(n,e)if(n==true)return
return n,e end local function na()local r=o[n]=="("local o=t()local n if e"do"then n=nn()l"end"else nl(r)n=nn()x=nil end return function(e)while o(e)do if(stat(1)>=1)w()
local t,l=n(e)if(t)return ne(t,l)
end end end local function nl()local r=f local o=nn(true)l"until"local l=t()while(f>r)q()
return function(n)repeat if(stat(1)>=1)w()
local e,t=o(n)if(not e)t=l(n)
while(#n>r)deli(n)
if(e)return ne(e,t)
until t end end local function nc()if o[n+1]=="="then local r=u()l"="local o=t()l","local i=t()local u=e","and t()or g(1)l"do"z()d[r]=f local t=nn()l"end"q()return function(n)for e=o(n),i(n),u(n)do if(stat(1)>=1)w()
add(n,{[r]=e})local e,l=t(n)deli(n)if(e)return ne(e,l)
end end else local r=k(u)l"in"local o=k(t)l"do"z()for n in all(r)do d[n]=f end local i=nn()l"end"q()return function(n)local e=m(n,o)while true do local l={}local t={e[1](e[2],e[3])}if(t[1]==nil)break
e[3]=t[1]for n=1,#r do l[r[n]]=t[n]end if(stat(1)>=1)w()
add(n,l)local e,t=i(n)deli(n)if(e)return ne(e,t)
end end end end local function g()if(not y or h and y<h)i"break outside of loop"
return function()return true end end local function y()if(not h and not ni)i"return outside of function"
if o[n]==";"or r(o[n],nk)or x and x()then return function()return pack()end else local r,n,l=t()local n={r}while(e",")add(n,(t()))
if#n==1and l and h then return function(n)local e,t=l(n)if(stat(1)>=1)w()
return function()return e(c(t))end end else return function(e)return m(e,n)end end end end local function z(e)local n=u()l"::"if(p[n]and p[n].e==s)i"label already defined"
p[n]={l=f,e=s,o=e,r=#e}end local function nn()local t=u()local e,l,n=p,f add(v,function()n=e[t]if(not n)i"label not found"
if(h and n.e<h)i"goto outside of function"
local t=e[n.e]or l if(n.l>t and n.r<#n.o)i"goto past local"
end)return function()if(stat(1)>=1)w()
return 0,n end end local function u(f)local r=o[n]n+=1if(r==";")return
if(r=="do")local n=b()l"end"return n
if(r=="if")return no()
if(r=="while")return na()
if(r=="repeat")return nl()
if(r=="for")return nc()
if(r=="break")return g()
if(r=="return")return y(),true
if(r=="local")return nu()
if(r=="goto")return nn()
if(r=="::")return z(f)
if(r=="function"and o[n]~="(")return nr(true)
if r=="?"then local e,l=nt"print",k(t)return function(n)e(n)(c(m(n,l)))end end n-=1local f=n local l,d,r=t()if e","or e"="then n=f return nf()elseif n6(o[n])then return nd(l,d)elseif s<=1and j then return function(e)local n=pack(l(e))if(not(r and n.n==0))add(a,n)
n5=n[1]end else if(not r)i"statement has no effect"
return function(n)l(n)end end end b=function(t)p=setmetatable({},{__index=p})p[s]=f s+=1local d=s local i=t and 32767or f local l={}while n<=#o and not r(o[n],nk)and not(x and x())do local n,t=u(l)if(n)add(l,n)
if(t)e";"break
end while(f>i)q()
s-=1p=getmetatable(p).__index return function(e)local t,n local r,o=1,#l while r<=o do t,n=l[r](e)if t then if(type(t)~="number")break
if(n.e~=d)break
r=n.r while(#e>n.l)deli(e)
t,n=nil end r+=1end while(#e>i)deli(e)
return t,n end end d=j and{_ENV=0,_env=0,_=0}or{_ENV=0}local e=b()if(n<=#o)i"unexpected end"
for n in all(v)do n()end return function(n)local t=j and{_ENV=n,_env=n,_=n5}or{_ENV=n}local n=e{[0]=t}if(n)return c(n)
end end n2,nb=10,false local n5={["\0"]="000",["ᵉ"]="014",["ᶠ"]="015"}for n,e in pairs(eu)do if(not f(n,"'\n"))n5[e]=n
end function ee(n)local t=1while t<=#n do local l=e(n,t)local e=n5[l]if(e)n=sub(n,1,t-1).."\\"..e..sub(n,t+1)t+=#e
t+=1end return'"'..n..'"'end function et(n)if(type(n)~="string")return false
if(nd[n])return false
if(#n==0or g(e(n,1)))return false
for t=1,#n do if(not q(e(n,t)))return false
end return true end function nn(e,t)local n=type(e)if n=="nil"then return"nil"elseif n=="boolean"then return e and"true"or"false"elseif n=="number"then return tostr(e,nb)elseif n=="string"then return ee(e)elseif n=="table"and not t then local n="{"local l=0local r=0for t,o in next,e do if(l==n2)n=n..",<...>"break
if(l>0)n=n..","
local e=nn(o,1)if t==r+1then n=n..e r=t elseif et(t)then n=n..t.."="..e else n=n.."["..nn(t,1).."]="..e end l+=1end return n.."}"else return"<"..tostr(n)..">"end end function el(n,e)if(e==nil)return n
if(not n)n=""
local t=min(21,#e)for l=1,t do if(#n>0)n..="\n"
local t=e[l]if type(t)=="table"then local e=""for n=1,t.n do if(#e>0)e=e..", "
e=e..nn(t[n])end n..=e else n..=t end end local l={}for n=t+1,#e do l[n-t]=e[n]end return n,l end poke(24365,1)cls()d="> "n,s,k="",1,0l,v=1,20u,y={""},1ne=false h,o=0,1nu,na=true,true i={7,4,3,5,6,8,5,12,14,7,11,5}t.print=function(n,...)if(pack(...).n~=0or not nu)return print(n,...)
add(a,tostr(n))end function n9()poke(24368,1)end function nv()return function()if(stat(30))return stat(31)
end end function np(r,i)local t=1local n,l=0,0if(not r)return t,n,l
while t<=#r do local o=e(r,t)local e=o>="█"if(n>=(e and 31or 32))l+=1n=0
if(i)i(t,o,n,l)
if o=="\n"then l+=1n=0else n+=e and 2or 1end t+=1end return t,n,l end function nt(o,l)local n,e=0,0local i,r,t=np(o,function(t,i,r,o)if(l==t)n,e=r,o
end)if(l>=i)n,e=r,t
if(r>0)t+=1
return n,e,t end function nl(i,r,e)local t=1local n=false local o,f,l=np(i,function(o,f,i,l)if(e==l and r==i and not n)t=o n=true
if((e<l or e==l and r<i)and not n)t=o-1n=true
end)if(not n)t=e>=l and o or o-1
if(f>0)l+=1
return t,l end function nw(n,t,l,e)if type(e)=="function"then np(n,function(n,r,o,i)print(r,t+o*4,l+i*6,e(n))end)else print(n and"⁶rw"..n,t,l,e)end end function er(n,o,f)local d,t,u,l=ng(n)local t=1nw(n,o,f,function(o)while t<=#l and l[t]<o do t+=1end local n if(t<=#l and u[t]<=o)n=d[t]
local t=i[5]if n==false then t=i[6]elseif n==true then t=i[7]elseif type(n)~="string"or r(n,{"nil","true","false"})then t=i[8]elseif nd[n]then t=i[9]elseif not q(e(n,1))then t=i[10]elseif ea[n]then t=i[11]end return t end)end function _draw()local u=peek(24357)local c,p=peek2(24360),peek2(24362)camera()local function e(n)cursor(0,127)for e=1,n do rectfill(0,o*6,127,(o+1)*6-1,0)if o<21then o+=1else print""end end end local function w(n,e)for t=1,n do if(o>e)o-=1
rectfill(0,o*6,127,(o+1)*6-1,0)end end local function m(n,e)for t=0,2do local l=pget(n+t,e+5)pset(n+t,e+5,l==0and i[12]or 0)end end local function f(u)local r=d..n.." "local f,t,n=nt(r,#d+l)if n>s then e(n-s)elseif n<s then w(s-n,n)end s=n k=mid(k,0,max(s-21,0))::again::local e=o-s+k if(e+t<0)k+=1goto again
if(e+t>=21)k-=1goto again
local n=e*6rectfill(0,n,127,n+s*6-1,0)if(s>21)rectfill(0,126,127,127,0)
er(r,0,n)print(d,0,n,i[4])if(v>=10and u~=false and not x)m(f*4,n+t*6)
end local function d(t)e(1)o-=1print("[enter] ('esc' to abort)",0,o*6,i[3])while true do flip()n9()for n in nv()do if(n=="•")ne=true b=""a={}return false
if(n=="\r"or n=="\n")h+=t return true
end end end::again::local r,t if a or b then r,t=nl(b,0,h)if t-h<=20and a then b,a=el(b,a)r,t=nl(b,0,h)if(#a==0and not x)a=nil
end end if(not x)camera()
if(h==0and not x)f(not b)
if b then local u=sub(b,r)local r=min(t-h,20)e(r)nw(u,0,(o-r)*6,i[1])if r<t-h then if(d(r))goto again
else local d,u,t=nt(nc,0)e(t)nw(nc,0,(o-t)*6,i[2])if x then h+=r else n,s,k,l,h,b,nc="",0,0,1,0f()end end end if x then e(1)o-=1print(x,0,o*6,i[3])end if z then e(1)o-=1print(z,0,o*6,i[3])z=nil end if n1 then n1-=1if(n1==0)z,n1=""
end v-=1if(v==0)v=20
color(u)camera(c,p)if(o<=20)cursor(0,o*6)
end ns,nr,no=false,false,false ni={}function n8(n,e)m,eo=n,e assert(false,n)end function nx(n,e,l)return n4(n,l)(e or t)end function n3(n,e)return nx("return "..n,e,true)end function ei(t)local l=cocreate(n4)::_::local n,e=coresume(l,t)if(n and not e)goto _
if(not n)e,m=m,false
return n,e end function ef(n,e)local t,l=nt(n,e)return"line "..l+1 .." col "..t+1end function ny(e,l)a,ne,m={},false,false ns,nr,no=false,false,false local t=cocreate(function()nx(e)end)local r,n while true do r,n=coresume(t)if(costatus(t)=="dead")break
if nu and not nr then x="running, press 'esc' to abort"_draw()flip()x=nil else if(na and not nr and not no)flip()
if(not na and holdframe)holdframe()
no=false end for n in nv()do if n=="•"then ne=true else add(ni,n)end end if(ne)n="computation aborted"break
end if m==nil then if(l)n="unexpected end of code"else n,a=nil
end if(m)n,m=m.."\nat "..ef(e,eo)
nc=n ni={}end w=function()ns=true yield()ns=false end t.flip=function(...)local n=pack(flip(...))no=true w()return c(n)end t.coresume=function(n,...)local e=pack(coresume(n,...))while ns do yield()e=pack(coresume(n))end m=false return c(e)end t.stat=function(n,...)if n==30then return#ni>0or stat(n,...)elseif n==31then if#ni>0then return deli(ni,1)else local e=stat(n,...)if(e=="•")ne=true
return e end else return stat(n,...)end end function ed(n)if(_set_fps)_set_fps(n._update60 and 60or 30)
if(n._init)n._init()
nr=true while true do if(_update_buttons)_update_buttons()
if(holdframe)holdframe()
if n._update60 then n._update60()elseif n._update then n._update()end if(n._draw)n._draw()
flip()no=true w()end nr=false end function nq(e)if r(e,{"i","interrupt"})then return nu elseif r(e,{"f","flip"})then return na elseif r(e,{"r","repl"})then return j elseif r(e,{"mi","max_items"})then return n2 elseif r(e,{"h","hex"})then return nb elseif r(e,{"cl","colors"})then return i elseif r(e,{"c","code"})then local e={[0]=n}for n=1,#u-1do e[n]=u[#u-n]end return e elseif r(e,{"cm","compile"})then return function(n)return ei(n)end elseif r(e,{"x","exec"})then return function(n,e)nx(n,e)end elseif r(e,{"v","eval"})then return function(n,e)return n3(n,e)end elseif r(e,{"p","print"})then return function(n,...)t.print(nn(n),...)end elseif r(e,{"ts","tostr"})then return function(n)return nn(n)end elseif r(e,{"rst","reset"})then run()elseif r(e,{"run"})then ed(t)else assert(false,"unknown \\-command")end end function en(e)local function t(n)return n and n~=0and true or false end local n if r(e,{"i","interrupt"})then n=function(n)nu=t(n)end elseif r(e,{"f","flip"})then n=function(n)na=t(n)end elseif r(e,{"r","repl"})then n=function(n)j=t(n)end elseif r(e,{"mi","max_items"})then n=function(n)n2=tonum(n)or-1end elseif r(e,{"h","hex"})then n=function(n)nb=t(n)end elseif r(e,{"cl","colors"})then n=function(n)i=n end else assert(false,"unknown \\-command assign")end local e={__newindex=function(t,l,e)n(e)end}return setmetatable(e,e),0end nh=stat(4)nf,n0=0,false poke(24412,10,2)function p(n)if stat(28,n)then if(n~=nm)nm,nf=n,0
return nf==0or nf>=10and nf%2==0elseif nm==n then nm=nil end end function _update()local t=false local function r(o)local t,e,r=nt(d..n,#d+l)if(n7)t=n7
e+=o if(not(e>=0and e<r))return false
l=max(nl(d..n,t,e)-#d,1)n7=t v=20return true end local function f(r)local e,o=nt(d..n,#d+l)e=r>0and 100or 0l=max(nl(d..n,e,o)-#d,1)t=true end local function c(r)u[y]=n y+=r n=u[y]if r<0then l=#n+1else l=max(nl(d..n,32,0)-#d,1)local t=e(n,l)if(t~=""and t~="\n")l-=1
end t=true end local function d()if#n>0then if(#u>50)del(u,u[1])
u[#u]=n add(u,"")y=#u t=true end end local function s(e)if l+e>0then n=sub(n,1,l+e-1)..sub(n,l+e+1)l+=e t=true end end local function o(e)n=sub(n,1,l-1)..e..sub(n,l)l+=#e t=true end local i=stat(28,224)or stat(28,228)local h=stat(28,225)or stat(28,229)local e=-1if p(80)then if(l>1)l-=1t=true
elseif p(79)then if(l<=#n)l+=1t=true
elseif p(82)then if((i or not r(-1))and y>1)c(-1)
elseif p(81)then if((i or not r(1))and y<#u)c(1)
else local r=stat(31)e=ord(r)if r=="•"then if#n==0then extcmd"pause"else a,nc={}d()end elseif r=="\r"or r=="\n"then if h then o"\n"else ny(n)if(not a)o"\n"else d()
end elseif i and p(40)then ny(n,true)d()elseif r~=""and e>=32and e<154then if(n0 and e>=128)r=chr(e-63)
o(r)elseif e==193then o"\n"elseif e==192then f(-1)elseif e==196then f(1)elseif e==203then n0=not n0 z,n1="shift now selects "..(n0 and"punycase"or"symbols"),40elseif p(74)then if(i)l=1t=true else f(-1)
elseif p(77)then if(i)l=#n+1t=true else f(1)
elseif p(42)then s(-1)elseif p(76)then s(0)end end local r=stat(4)if(r~=nh or e==213)o(r)nh=r
if e==194or e==215then if n~=""and n~=nh then nh=n printh(n,"@clip")if(e==215)n=""l=1
z="press again to put in clipboard"else z=""end end if stat(120)then local n repeat n=serial(2048,24448,128)o(chr(peek(24448,n)))until n==0end if(t)v,n7=20
nf+=1n9()end function n_(n,e)local t,l=coresume(cocreate(e))if not t then printh("error #"..n..": "..l)print("error #"..n.."\npico8 broke something again,\nthis cart may not work.\npress any button to ignore")while(btnp()==0)flip()
cls()end end n_(1,function()assert(pack(n3"(function (...) return ... end)(1,2,nil,nil)").n==4)end)n_(2,function()assert(n3"function() local temp, temp2 = {max(1,3)}, -20;return temp[1] + temp2; end"()==-17)end)printh"finished"stop()while true do if(holdframe)holdframe()
_update()_draw()flip()end
__meta:title__
keep:------------------------------------
keep: Please see 'Commented Source Code' section in the BBS