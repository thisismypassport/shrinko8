
-- comment
print = function(msg, extra)
  if extra then
    msg = msg .. " " .. extra
  end
  printh(msg)
end
local bor = "what a bore"
print("hello from", "?")
print(ord("\1"))
print(ord("\2"))
print(ord("\3"))
print(ord("\4"))
print(ord("\5"))
print(ord("\0060"))
print(ord("\2"))
print(ord("\30"))
print(ord("\139"))
print(ord("\159"))
b = 123
x = 450
e = 123
print(b .. " " .. x .. " " .. e)
a = 3
print(_ENV.bor(a, 0x.8))
print(band(a, 0x2))
print(bxor(a, 0x10))
print(bxor(a, 0x20))
print(shl(a, 1))
print(shr(a, 1))
print(lshr(a, 1))
print(rotr(a, 1))
print(rotl(a, 1))
print(flr(a / 2))
print(a ~= 3)
a = a + 2
print(a)
a = a * 2
print(a)
a = flr(a / 3)
print(a)
a = _ENV.bor(a, 12)
print(a)
poke(0x10, 12)
print(peek(0x10))
poke2(0x10, 1234)
print(peek2(0x10))
poke4(0x10, 1234.5678)
print(peek4(0x10))
b = 10
if b then
  print(b)
end
if not b then
  print("not")
end
if not b then
  print("not")
else
  print("yep")
end
i = 0
while i < 5 do
  print(i)
  i = i + 1
end
print("Done")
-- known limitations:
--   f().x += b  <- f() will be evaluated twice
--   redefining _ENV or certain used globals will break things