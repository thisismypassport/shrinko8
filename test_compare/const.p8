pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
--[[non-const]] local ERROR = false
function print(value)
    printh(tostr(value, true))
end
-- neg
?0
?-1
?1
?32768
?32768.00002
?4660.33779
if (ERROR) ?-false
if (ERROR) ?-nil
-- abs
?1.3
?1.3
?32767.99999
?abs(0x8000)
-- flr
?5
?5
?5
?0
?-5
?-6
?-6
?-1
?32768
-- ceil
?5
?6
?6
?1
?-5
?-5
?-5
?0
?ceil(0x7fff.0001)
-- add
?3
?~32767
?.99999
?"1" + "2"
if (ERROR) ?me + 1
if (ERROR) ?1 + me
-- sub
?-1
?~0
if (ERROR) ?"a" - "a"
-- mul
?4.5
?3.29998
?-93.4798
?5535
?60001
?0x4000 * 2
?32768
?123 * 456
?-123 * 456
?1245 * 4253
-- div
?4
?2.4
?12 / 0
?0 / 0
?1008.24614
?100 / 0.001
?~.3846
?52932.87871
?-.75
?-.75
?.75
-- idiv
?4
?2
?-3
?-3
?2
?8
?-9
?4 \ 0
-- mod
?2
?3
?12 % -5
?-12 % -5
?12 % 0
?2.2
?1.2
?.0005
?.3
-- eq
?false
?true
?false
?true
?false
?true
?3 == me
-- neq
?true
?false
?true
?true
?true
?false
?"" ~= {}
-- lt
?false
?true
?false
?true
?true
?true
if (ERROR) ?3 < "4"
-- le
?true
?true
?false
?true
?false
?true
if (ERROR) ?false <= true
-- gt
?false
?false
?true
?false
?true
?false
?true
?true
-- ge
?true
?false
?true
?false
?true
?true
?true
-- max
?23
?23.3
?1
?max(4)
-- min
?-123
?3
?32768
-- mid
?3
?3
?3
?-3
?123.456
-- bnot
?~0
?~1
?.99999
if (ERROR) ?~true
if (ERROR) ?~"x"
?~1.2
?bnot(1,2)
-- band
?544.32935
?.33777
?band()
-- bor
?47806.34176
?3
?bor(1)
-- bxor
?47262.01241
?.99999
?.00002
-- shl
?20480
?32768
?4660.33777
?0
?0
?2330.16889
?0x1234.5678 << 0.9
?-16
-- shr
?.00123
?.00002
?~0
?4660.33777
?0
?~0
?~0
?0xe468.acf
?-2.5
-- lshr
?.00123
?.00002
?0
?0
?0
?0xe468.acf
?32765.5
-- rotl
?12288.00008
?0xa.6
?0x2.98
?4
?4 <<> 0.5
?2
-- rotr
?12288.00008
?0x2.98
?0xa.6
?4
?4 >>< 0.5
?8
-- not
?true
?true
?false
?false
-- and
?4
?nil
?false
? me
?nil
?it and me
?it and 4
-- or
?true
?3
?4
? me
?3
?it or me
?it or 4
-- len
if (ERROR) ?#123
?0
?3
?6
-- cat
?"12"
?"bla◝ナ\r\n¹\0"
?"12"
?"12"
?"-32768-2"
?"1" .. 2.3
if (ERROR) ?"1" .. false
-- misc
function foo() return 10 end
?23
?35
local a = foo()
?a * 3 + 36
local function --[[const]] nocrash() end
local --[[const]] f = max()
?8
menuitem,chr=41,42
-- misc1.5
local --[[non-const]] ncval = 4
?(-3)*ncval
?(-3)^ncval
?ncval^(-3)
?65533^2
?-65533^2
?2^-3
?3
?2.99999
?false
if (ERROR) ?#65533
-- misc2
--[[const]] ; ?61.5
--[[const]] ; ?579
--[[const]] ssog5 = 456, 789; ?579
--[[const]] ; ?123
?nil
bar, bar2 = foo(), foo(); ?123
--[[const]] bar = foo(); ?579
--[[const]] ssog14, --[[const]] ssog15 = foo(); ?ssog15
--[[const]] ssog22 =nil ; ?5
ssog22=1
--[[const]] ; ?5
?nil
local ssog26 ; ?5
ssog26=1
; ?5
?nil
local ssog31; ssog31=ssog31,ssog31; ssog31,ssog31=ssog31; ?nil
-- misc3
local a0 = foo() ;({}).x=foo() ;({}).x=foo() ;({}).x=foo()
?foo() 
;({}).x = 4
-- if
print(true) 
?false
print(true) 
print(false) 
print(true) 
print(nil) 
print(false) 
print(nil) 
print(0) 
print(false) 
if foo then print(nil) else print(false) end
print(nil) 
print(true) 
if foo then print(true) else print(nil)end 
if foo then print(true) else print(false) end
if foo then print(true) else print(nil)end 
if foo then print(true)end 
if foo then print(true) else print(nil)end 
if foo then print(true) else print(0)end 
if foo then print(true) else print(false) end
if foo then print(true) elseif bar then print(1) else print(nil)end 
if foo then print(true) elseif bar then print(1) else print(false) end
if foo then print(true) elseif bar then print(1) else print(nil)end 
if foo then print(true) elseif bar then print(1)end 
if foo then print(true) elseif bar then print(1) else print(nil)end 
if foo then print(true) elseif bar then print(1) else print(0)end 
if foo then print(true) elseif bar then print(1) else print(false) end
?""
-- if misc
?"" 
do local a=3end ?a
?a
if foo then --[[non-const]] local a=3 end ?a
?a 
do local function a() end end ?a
?a
do do::a::end goto a end ::a::
do goto b end ::b:: do return end ?3
