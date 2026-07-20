__lua__
print = printh

--$dynamic-include: parens8.interpreter

print("outside")

--$switch-compiler: parens8
print("inside")
--$switch-compiler: none

print("outside again")

--$switch-compiler: parens8
--$switch-compiler: none

print("outside finally")
