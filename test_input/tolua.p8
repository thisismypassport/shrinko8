pico-8 cartridge // http://www.pico-8.com
version 41
__lua__
// comment
print = function (msg, extra)
    if (extra) msg ..= " " .. extra
    printh(msg)
end

local bor = "what a bore"

?"hello from", "?"
print(ord("\*"))print(ord("\#"))
print(ord("\-"))print(ord("\|"))
print(ord("\+"))print(ord("\^0"))
print(ord("²"))print(ord("゛"))
print(ord("⬅️"))print(ord("か"))
b=123x=450e=123
print(b.." "..x.." "..e)

a = 3
print(a | 0x.8)
print(a & 0b10)
print(a ^^ 0x10)
print(a ~ 0x20)
print(a << 1)
print(a >> 1)
print(a >>> 1)
print(a >>< 1)
print(a <<> 1)
print(a \ 2)
print(a != 3)

a += 2
print(a)
a *= 2
print(a)
a \= 3
print(a)
a |= 12
print(a)

poke(0x10, 12)
print(@0x10)
poke2(0x10, 1234)
print(%0x10)
poke4(0x10, 1234.5678)
print($0x10)

b = 10
if (b) print(b)
if (not b) print("not")
if (not b) print("not") else print("yep")

i = 0
while (i < 5) print(i); i += 1

print("Done")

-- known limitations:
--   f().x += b  <- f() will be evaluated twice
--   redefining _ENV or certain used globals will break things
