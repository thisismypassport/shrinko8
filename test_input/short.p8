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

print("bla");print("bla",1,2,3,4);print("bla",1,2,3,4)
prout = print("bla")
prout, prout2 = print("bla2")
