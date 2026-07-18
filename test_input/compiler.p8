pico-8 cartridge // http://www.pico-8.com
version 43
__lua__
print = printh

function execute_raw(code, env)
    -- dummy impl. for test
    print(code)
end

print("hello from outside")

--$switch-compiler: repl

print("hello from repl string")

--$switch-compiler: repl +minify

print("hello from repl minified string")

for i=1,10 do print(i) end

--$switch-compiler: repl +rom +minify

print("hello from repl rom")

while (true) print("zzz")

--$switch-compiler: none

print("hello from outside again")

--$dynamic-include: repl.dummy
