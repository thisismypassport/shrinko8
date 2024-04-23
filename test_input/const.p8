pico-8 cartridge // http://www.pico-8.com
version 36
__lua__
--[[non-const]] local ERROR = false
function print(value)
    printh(tostr(value, true))
end
-- neg
?-(0)
?-(1)
?-(-1)
?-(0x8000)
?-(0x7fff.ffff)
?-(0xedcb.a987)
if (ERROR) ?-false
if (ERROR) ?-nil
-- abs
?abs(1.3)
?abs(-1.3)
?abs(0x8000.0001)
?abs(0x8000)
-- flr
?flr(5)
?flr(5.2)
?flr(5.9)
?flr(0.1)
?flr(-5)
?flr(-5.2)
?flr(-5.9)
?flr(-0.1)
?flr(0x8000.0001)
-- ceil
?ceil(5)
?ceil(5.2)
?ceil(5.9)
?ceil(0.1)
?ceil(-5)
?ceil(-5.2)
?ceil(-5.9)
?ceil(-0.1)
?ceil(0x7fff.0001)
-- add
?1 + 2
?0x7fff.ffff+1
?0xffff.ffff+1
?"1" + "2"
if (ERROR) ?me + 1
if (ERROR) ?1 + me
-- sub
?1 - 2
?0 - 0x.0001
if (ERROR) ?"a" - "a"
-- mul
?3 * 1.5
?3 * 1.1
?-12.3 * 7.6
?123 * 45
?123 * -45
?0x4000 * 2
?-0x4000 * 2
?123 * 456
?-123 * 456
?1245 * 4253
-- div
?12 / 3
?12 / 5
?12 / 0
?0 / 0
?1 / 0.001
?100 / 0.001
?-1 / 2.6
?0x8000 / 2.6
?-3 / 4
?3 / -4
?-3 / -4
-- idiv
?12 \ 3
?12 \ 5
?-12 \ 5
?12 \ -5
?-12 \ -5
?10.5 \ 1.3
?-10.5 \ 1.3
?4 \ 0
-- mod
?12 % 5
?-12 % 5
?12 % -5
?-12 % -5
?12 % 0
?5.6 % 3.4
?-5.6 % 3.4
?12 % 0.3
?0.3 % 12
-- eq
?3 == 4
?3.1 == 3.1
?3 == "3"
?"3" == "3"
?1 == true
?false == false
?3 == me
-- neq
?3 != 0x3.0001
?4 ~= 4
?"04" != "4"
?4 != "4"
?false != true
?nil != nil
?"" ~= {}
-- lt
?3 < 3
?3 < 4
?4 < 3
?-3 < 4
?"3" < "4"
?"3" < "30"
if (ERROR) ?3 < "4"
-- le
?3 <= 3
?3 <= 4
?4 <= 3
?-3 <= 4
?"\xe8" <= "z"
?"3" <= "3"
if (ERROR) ?false <= true
-- gt
?3 > 3
?3 > 4
?4 > 3
?-3 > 4
?"3" > ""
?"" > ""
?"3\0" > "3"
?"\x80" > "a"
-- ge
?3 >= 3
?3 >= 4
?4 >= 3
?-3 >= 4
?"3" >= ""
?"" >= ""
?"\xff" >= "\xfe"
-- max
?max(-123, 23)
?max(23.3, 3)
?max(0x8000, 1)
?max(4)
-- min
?min(-123, 23)
?min(23.3, 3)
?min(0x8000, 1)
-- mid
?mid(3,0,5)
?mid(0,3,5)
?mid(5,3,0)
?mid(-5,-3,0)
?mid(0x8000,0x7fff,123.456)
-- bnot
?~(0)
?~(1)
?~(0xffff)
if (ERROR) ?~true
if (ERROR) ?~"x"
?bnot(1.2)
?bnot(1,2)
-- band
?0x1234.5678&0xaaaa.5555
?band(0x1234.5678,0x.ffff)
?band()
-- bor
?0x1234.5678|0xaaaa.5555
?bor(1,2)
?bor(1)
-- bxor
?0x1234.5678^^0xaaaa.5555
?0xffff~0xffff.ffff
?bxor(0x1234.5678, 0x1234.5679)
-- shl
?0x5 << 0xc
?0x.0001 << 31
?0x1234.5678 << 0
?0x1234.5678 << 32
?0x1234.5678 << 0x7fff
?0x1234.5678 << -1
?0x1234.5678 << 0.9
?shl(-1, 4)
-- shr
?0x5 >> 0xc
?0x4000 >> 30
?0x8000 >> 31
?0x1234.5678 >> 0
?0x1234.5678 >> 32
?0xf234.5678 >> 32
?0xf234.5678 >> 0x7fff
?0xf234.5678 >> -1
?shr(-0x5,1)
-- lshr
?0x5 >>> 0xc
?0x8000 >>> 31
?0x1234.5678 >>> 32
?0xf234.5678 >>> 32
?0xf234.5678 >>> 0x7fff
?0xf234.5678 >>> -1
?lshr(-0x5,1)
-- rotl
?0x5.3 <<> 16
?0x5.3 <<> 33
?0x5.3 <<> 0x7fff
?4 <<> 0
?4 <<> 0.5
?4 <<> -1
-- rotr
?0x5.3 >>< 16
?0x5.3 >>< 33
?0x5.3 >>< 0x7fff
?4 >>< 0
?4 >>< 0.5
?4 >>< -1
-- not
?not nil
?not false
?not true
?not 0
-- and
?3 and 4
?nil and 4
?false and 4
?3 and me
?nil and me
?it and me
?it and 4
-- or
?true or 4
?3 or 4
?nil or 4
?nil or me
?3 or me
?it or me
?it or 4
-- len
if (ERROR) ?#123
?#""
?#"123"
?#"123➡️✽…"
-- cat
?"1" .. "2"
?"bla" .. "\xff\xe0\r\n\1\0"
?1 .. "2"
?"1" .. 2
?0x8000 .. -2
?"1" .. 2.3
if (ERROR) ?"1" .. false
-- misc
function foo() return 10 end
?3 + 4 * 5
?(3 + 4) * 5
local a, --[[const]] b = foo(), 3 * 4
local --[[const]] c = 1 | 2
?a * c + b * c
local function --[[const]] nocrash() end
local --[[const]] d, --[[const]] e = nil, false
local --[[const]] f = max()
?3 + max(4, 5)
menuitem,chr=41,42
-- misc1.5
local --[[non-const]] ncval = 4
local --[[const]] cval = -3
?(1-4)*ncval
?(1-4)^ncval
?ncval^(1-4)
?cval^2
?-cval^2
?2^cval
?-cval
?~cval
?not cval
if (ERROR) ?#cval
-- misc2
--[[const]] ssog1 = 123; ?ssog1/2
--[[const]] ssog2, --[[const]] ssog3 = 123, 456; ?ssog2+ssog3
--[[const]] ssog4, --[[const]] ssog5 = 123, 456, 789; ?ssog4+ssog5
--[[const]] ssog6, --[[const]] ssog7 = 123; ?ssog6
?ssog7
bar, --[[const]] ssog11, bar2 = foo(), 123, foo(); ?ssog11
--[[const]] ssog12, bar, --[[const]] ssog13 = 123, foo(), 456; ?ssog12+ssog13
--[[const]] ssog14, --[[const]] ssog15 = foo(); ?ssog15
--[[const]] ssog21, --[[const]] ssog22 = max(4,5); ?ssog21
ssog22=1
--[[const]] ssog23, --[[const]] ssog24 = max(4,5); ?ssog23
?ssog24
local ssog25, ssog26 = max(4,5); ?ssog25
ssog26=1
local ssog27, ssog28 = 5; ?ssog27
?ssog28
local ssog30, ssog31; ssog31=ssog31,ssog31; ssog31,ssog31=ssog31; ?ssog30
-- misc3
local a0, a1 = foo(), 1
({}).x=foo()
--[[const]]ssogmisc3,({}).x=2,foo()
local a2 = 44
({}).x=foo()
?foo()
--[[const]]ssoga3, ({}).x = 3, 4
-- if
if (1==1) print(true) else ?false
if (1==2) print(true) else ?false
if 1==1 then print(true) else print(false) end
if 1==2 then print(true) else print(false) end
if 1==1 then print(true) elseif 1==1 then print(nil) else print(false) end
if 1==2 then print(true) elseif 1==1 then print(nil) else print(false) end
if 1==2 then print(true) elseif 1==3 then print(nil) else print(false) end
if 1==2 then print(true) elseif 1==1 then print(nil) elseif 1==1 then print(0) else print(false) end
if 1==2 then print(true) elseif 1==3 then print(nil) elseif 1==1 then print(0) else print(false) end
if 1==2 then print(true) elseif 1==3 then print(nil) elseif 1==4 then print(0) else print(false) end
if 1==2 then print(true) elseif foo then print(nil) else print(false) end
if 1==2 then print(true) elseif 1==1 then print(nil) end
if 1==2 then print(true) elseif 1==2 then print(nil) end
if 1==1 then print(true) end
if 1==2 then print(true) end
if foo then print(true) elseif 1==1 then print(nil) else print(false) end
if foo then print(true) elseif 1==2 then print(nil) else print(false) end
if foo then print(true) elseif 1==1 then print(nil) end
if foo then print(true) elseif 1==2 then print(nil) end
if foo then print(true) elseif 1==1 then print(nil) elseif 1==1 then print(0) else print(false) end
if foo then print(true) elseif 1==3 then print(nil) elseif 1==1 then print(0) else print(false) end
if foo then print(true) elseif 1==3 then print(nil) elseif 1==4 then print(0) else print(false) end
if foo then print(true) elseif bar then print(1) elseif 1==1 then print(nil) else print(false) end
if foo then print(true) elseif bar then print(1) elseif 1==2 then print(nil) else print(false) end
if foo then print(true) elseif bar then print(1) elseif 1==1 then print(nil) end
if foo then print(true) elseif bar then print(1) elseif 1==2 then print(nil) end
if foo then print(true) elseif bar then print(1) elseif 1==1 then print(nil) elseif 1==1 then print(0) else print(false) end
if foo then print(true) elseif bar then print(1) elseif 1==3 then print(nil) elseif 1==1 then print(0) else print(false) end
if foo then print(true) elseif bar then print(1) elseif 1==3 then print(nil) elseif 1==4 then print(0) else print(false) end
?""
-- if misc
?""
if 1==1 then --[[non-const]] local a=3 end ?a
if 1==2 then --[[non-const]] local a=3 end ?a
if 1==1 then if foo then --[[non-const]] local a=3 end end ?a
if 1==2 then if foo then --[[non-const]] local a=3 end end ?a
if 1==1 then local function a() end end ?a
if 1==2 then local function a() end end ?a
do if 1==1 then ::a:: end goto a end ::a::
do if 1==2 then ::b:: end goto b end ::b::
if 1==1 then return end ?3