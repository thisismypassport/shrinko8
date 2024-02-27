__lua__
sep = time -- just used as a "separator" to avoid merging

do local a;local b,c=1,2;local d=4 assert(a==nil);printh(b..c..d) end
do local a,b,c=1;local d,e,f=2;assert(b==nil and c==nil and e==nil and f==nil);printh(a..d); end

function f() return 1,2,3 end
do local a=3; local b=f(); local c=4,9; printh(a..b..c); end
do local a=3; local b,c=f(); local d=4; printh(a..b..c..d); end
do local a=3; local b,c=(f()); local d=4; assert(c==nil); printh(a..b..d); end
do local a,b=3; local c,d=f(); local e=4; assert(b==nil); printh(a..c..d..e); end
do local a,b=3; local c=4,9; assert(b==nil); printh(a..c); end

--[[ no longer works in 0.2.6b:
do local a,b=3; local c,d=?"w/e"
   local e=4; assert(b==nil and c!=nil and d!=nil); printh(a..e); end
]]
do local a,b=3; local c=?"w/e"
   local e=4; assert(b==nil and c!=nil); printh(a..e); end

-- (the output might look like a problem, but it isn't - while assign order gets reversed, this doesn't affect which local ends up ahead in scope)
do local a=3;local b=4; printh(b)end
do local a=3;local a=4; printh(a)end

do local a;local b=3;printh(b) end
do local a;local a=3;printh(a) end

do local a=3;local b=(function () return 1 end)(); printh(a..b) end
do local a=3;local b=(function () return a end)(); printh(a..b) end

do local a; local b; local function c() return 6 end
    a=3; b=4; a=2; a=a+5; b=b+c(); printh(a..b);
end
do local a; local b; local function c() return a end
    a=3; b=c(); printh(a..b);
end

a=4;b=5;c=6 printh(a..b..c)
a=b-4;b=2;c=a+1 printh(a..b..c)

function f() return a end
a=10;b=f() printh(a..b)

a=11;b=function() return f() end;b=b() printh(a..b)

do 
    local result
    local print=function(x) result=x end;
    local what=(function() ?45
    end)();
    printh(result)
end
do
    local printh=printh
    local _ENV={z=13}
    local y=z
    printh(y..z)
end

t={}
t.a=3;t.b=4;printh(t.a..t.b)
t.a=3;t.a=4;printh(t.a)
t.b=t.a+1;t.a=3;printh(t.a..t.b)
t.a=5;t.b=t[--[[member]]'a'];printh(t.a..t.b)
t['a']=6;t.a=7;printh(t.a)

-- note: the _u/_v are just to avoid requiring semicolons. (which would also currently prevent merge - but this isn't intended)
_u,(printh("one") or {}).x = 0,printh("two")
_v,(printh("three") or {}).y = 0,printh("four")
sep()

a=sqrt(4);b=sqrt(9);printh(a..b)
a=flr(2.3);b=flr(3.9);printh(a..b)
function max() return a end
a=4;b=max(5,6);printh(a..a)
function custom() return a end
a=6;b=custom();printh(a..a)

-- cases requiring hint (unless safe-only)

x=setmetatable({},{__add=function() return a end}); sep()
a=20;--[[no-merge]]b=x+x; printh(a..b)

do
    local printh=printh
    local --[[member-keys]]_ENV = setmetatable({a=0},{__newindex=function(t,k,v) rawset(t, k, v + t.a) end})
    a=3;--[[no-merge]]b=4; printh(a..b)
end

do
    local t=setmetatable({a=0},{__newindex=function(t,k,v) rawset(t, k, v + t.a) end})
    t.a=7;--[[no-merge]]t.b=8;printh(t.a..t.b)
end

printh("over...")
