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
--$switch-compiler: none

globally_print("outside again")

--$switch-compiler: parens8
--$switch-compiler: none

--[[$switch-compiler: parens8 rom=0x1000]]--[[$switch-compiler: none]]
--[[$switch-compiler: parens8 rom=0x1000]]globally_print("inside tight")--[[$switch-compiler: none]]

globally_print("outside finally")
