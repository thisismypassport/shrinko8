pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
u,n,r=4,5,6printh(u..n..r)
f,c,e=u,n,r printh(f..c..e)
u,n=n-4,2r=u+1printh(u..n..r)
function e()return u end
u=10n=e()printh(u..n)
u,n=11,function()return e()end n=n()printh(u..n)
