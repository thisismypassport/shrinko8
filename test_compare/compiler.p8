pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
print=printh function o(o,e)print(o)end print"hello from outside"o('\nprint("hello from repl string")',_ENV)o('print("hello from repl minified string")for o=1,10do print(o)end',_ENV)o(chr(peek(0,51)),_ENV)print"hello from outside again"print(o(123,nil))
__gfx__
072796e64782228656c6c6f6026627f6d602275607c60227f6d62292778696c656824727575692072796e6478222a7a7a7229200000000000000000000000000
