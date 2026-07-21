__lua__
function globally_print(x) printh(x) end

--$dynamic-include: parens8.interpreter

globally_print("outside")

--$switch-compiler: parens8
globally_print("inside")
--$switch-compiler: none

globally_print("outside again")

--$switch-compiler: parens8
--$switch-compiler: none

globally_print("outside finally")
