pico-8 cartridge // http://www.pico-8.com
version 42
__lua__
_ENV=setmetatable({print=1,O=2},{__index=_ENV})assert(print+O==3,1)K=_ENV assert(K.O==2,2)printh"OK"
