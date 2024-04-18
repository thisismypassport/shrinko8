pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
stop() -- for pure syntax check
-- neg
?0
?65535
?1
?32768
?32768.00002
?4660.33779
?-false
?-nil
-- abs
?1.3
?65534.70002
?32768.00002
?abs(0x8000)
-- flr
?5
?5
?5
?0
?65531
?65530
?65530
?65535
?32768
-- ceil
?5
?6
?6
?1
?65531
?65531
?65531
?0
?ceil(0x7fff.0001)
-- add
?3
?32768.99999
?.99999
?"1" + "2"
?me + 1
?1 + me
-- sub
?65535
?65535.99999
?"a" - "a"
-- mul
?4.5
?3.29998
?65442.52021
?5535
?60001
?0x4000 * 2
?32768
?123 * 456
?65413 * 456
?1245 * 4253
-- div
?4
?2.4
?12 / 0
?0 / 0
?1008.24614
?100 / 0.001
?65535.6154
?52932.87871
?65535.25
?65535.25
?.75
-- idiv
?4
?2
?65533
?65533
?2
?8
?65527
?4 \ 0
-- mod
?2
?3
?12 % 65531
?65524 % 65531
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
?3 < "4"
-- le
?true
?true
?false
?true
?false
?true
?false <= true
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
?65413
?3
?32768
-- mid
?3
?3
?3
?65533
?123.456
-- bnot
?65535.99999
?65534.99999
?.99999
?~true
?~"x"
?65534.8
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
?65520
-- shr
?.00123
?.00002
?65535.99999
?4660.33777
?0
?65535.99999
?65535.99999
?0xe468.acf
?65533.5
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
?#123
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
?"1" .. false
-- misc
?23
?35
local a = foo()
?a * 3 + 36
local function --[[const]] nocrash() end
local --[[const]] f = max()
?8
printh,tostr=41,42
-- misc2
--[[const]] ; ?61.5
--[[const]] ; ?579
--[[const]] ssog5 = 456, 789; ?579
--[[const]] ; ?123
?nil
foo, foo2 = foo(), foo(); ?123
--[[const]] foo = foo(); ?579
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
?true 
?false
?true 
?false 
?true 
?nil 
?false 
?nil 
?0 
?false 
if foo then ?nil 
else ?false 
end
?nil 
?true 
if foo then ?true 
else?nil
end 
if foo then ?true 
else ?false 
end
if foo then ?true 
else?nil
end 
if foo then ?true
end 
if foo then ?true 
else?nil
end 
if foo then ?true 
else?0
end 
if foo then ?true 
else ?false 
end
if foo then ?true 
elseif bar then ?1 
else?nil
end 
if foo then ?true 
elseif bar then ?1 
else ?false 
end
if foo then ?true 
elseif bar then ?1 
else?nil
end 
if foo then ?true 
elseif bar then ?1
end 
if foo then ?true 
elseif bar then ?1 
else?nil
end 
if foo then ?true 
elseif bar then ?1 
else?0
end 
if foo then ?true 
elseif bar then ?1 
else ?false 
end
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
