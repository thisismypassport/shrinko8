pico-8 cartridge // http://www.pico-8.com
version 41
__lua__
for i=0,0x42ff do
if peek(i) != 0 then
print(tostr(i,1).." "..peek(i))
for j=0,0 do flip() end
end
end
print("done")
