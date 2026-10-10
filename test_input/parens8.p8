__lua__
function globally_print(x) printh(x) end

--$dynamic-include: parens8.interpreter compress

globally_print("outside")

--$switch-compiler: parens8
globally_print("inside")
--$switch-compiler: parens8 rom
globally_print("inside rom")
--$switch-compiler: parens8 rom compress
globally_print("inside compressed rom")
--$switch-compiler: parens8 compress
globally_print("inside compressed")
--$switch-compiler: parens8 dest=my_glob
globally_print("inside my_glob")
--$switch-compiler: none

globally_print("outside again")

--$switch-compiler: parens8
--$switch-compiler: none

--[[$switch-compiler: parens8 rom=0x1000]]--[[$switch-compiler: none]]
--[[$switch-compiler: parens8 rom=0x1000]]globally_print("inside tight")--[[$switch-compiler: none]]

--$def-alias: parens8_myrom = parens8 rom_ranges=0:0x40,0x1000:0x1040,0x2000:0x3000 compress
--$switch-compiler: parens8_myrom
globally_print("inside rom ranges start")
if lets_pad_this_out_a_little then
    for i=1,100 do i += 1 end
end
globally_print("inside rom ranges end")
--$switch-compiler: none
globally_print("outside yet again")
--$switch-compiler: parens8_myrom
globally_print("inside rom ranges #2")
--$switch-compiler: none
globally_print("outside once more")

run_ps8(my_glob)

globally_print("outside finally")
