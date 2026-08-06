--keep: hello
--[[const]] --[[keep:world]] a --[[keep:and]] = --[[keep:you]] 3

print(12)
--keep: g'bye
print(34)

--keep: pre-if
if globally then
    --keep: in-if
    print(1)
    --keep: out-if
else
    --keep: in-else
    print(-1)
    --keep: out-else
end

--keep: pre-if-2
if true then
    --keep: in-if-2
    print(99)
    --keep: out-if-2
else
    --keep: in-else-2
    print(-99)
    --keep: out-else-2
end

--keep: pre-if-3
if false then
    --keep: in-if-3
    print(99)
    --keep: out-if-3
else
    --keep: in-else-3
    print(-99)
    --keep: out-else-3
end

if true then --keep: in-if-4
end

--keep: final comment (add nothing else below)