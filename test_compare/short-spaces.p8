pico-8 cartridge // http://www.pico-8.com
version 42
__lua__

if (true) printh"K" else printh"NOPE"
while (true) printh"K" break
if e==0 then
    ?1
else
    ?2
end

?((function() if e==0 then e=1 end end)())
?((function() if (e==0) e=1 end)())
