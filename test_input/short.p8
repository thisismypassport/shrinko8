__lua__

if true then
    printh("K")
else
    printh("NOPE")
end
-- don't put anything else between these
while true do
    printh("K")
    break
end

if x==0 then
    ?1
else
    ?2
end

?((function() if x==0 then x=1 end end)())
?((function() if (x==0) x=1 end)())
