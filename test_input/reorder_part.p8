pico-8 cartridge // http://www.pico-8.com
version 42
__lua__

a=4;b=5;c=6 printh(a..b..c)
d=a;e=b;f=c printh(d..e..f)
a=b-4;b=2;c=a+1 printh(a..b..c)

function f() return a end
a=10;b=f() printh(a..b)

a=11;b=function() return f() end;b=b() printh(a..b)

-- no _ENV, to verify we can still roerder globals in safe-minify-only
