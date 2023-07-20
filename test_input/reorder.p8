__lua__
do local a;local b,c=1,2;local d=4 assert(a==nil);printh(b..c..d) end
do local a,b,c=1;local d,e,f=2;assert(b==nil and c==nil and e==nil and f==nil);printh(a..d); end

function f() return 1,2,3 end
do local a=3; local b=f(); local c=4,9; printh(a..b..c); end
do local a=3; local b,c=f(); local d=4; printh(a..b..c..d); end
do local a=3; local b,c=(f()); local d=4; assert(c==nil); printh(a..b..d); end
do local a,b=3; local c,d=f(); local e=4; assert(b==nil); printh(a..c..d..e); end
do local a,b=3; local c=4,9; assert(b==nil); printh(a..c); end

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

-- cases requiring hint (unless safe-only)

x=setmetatable({},{__add=function() return a end}); t()
a=20;--[[no-merge]]b=x+x; printh(a..b)

do
    local printh=printh
    local _ENV = setmetatable({a=0},{__newindex=function(t,k,v) rawset(t, k, v + t.a) end})
    a=3;--[[no-merge]]b=4; printh(a..b)
end

printh("over...")
