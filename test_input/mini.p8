__lua__
-- ideally, the minifier shouldn't add spaces below (as of writing this it does...)
function test1(a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,y,z)
    a=0c=0d=0e=0f=0g=0h=0i=0j=0k=0l=0m=0n=0o=0p=0q=0r=0s=0t=0u=0v=0w=0y=0z=0
end
-- these should not conflict with pre-defined globals
test2=0test3=0test4=0test5=0test6=0test7=0test8=0test9=0test0=0test10=0test11=0test12=0test13=0test14=0test15=0
a()b()c()d()e()f()g()h()i()j()k()l()m()n()o()p()q()r()s()t()u()v()w()x()y()z()
for index in whatever do
    if (index) a()b()c()d()e()f()g()h()i()j()k()l()m()n()o()p()q()r()s()t()u()v()w()x()y()z()
end