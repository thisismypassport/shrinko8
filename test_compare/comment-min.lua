--keep: hello
 --[[keep:world]] --[[keep:and]] --[[keep:you]] ?12
--keep: g'bye
?34

--keep: pre-if
if e do
    --keep: in-if
    ?1
    --keep: out-if
else
    --keep: in-else
    ?-1
    --keep: out-else
end

--keep: pre-if-2
 --keep: in-if-2
    ?99
    --keep: out-if-2
 --keep: pre-if-3
 --keep: in-else-3
    ?-99
    --keep: out-else-3
 
--keep: in-if-4


--keep: final comment (add nothing else below)