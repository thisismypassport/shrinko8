pico-8 cartridge // http://www.pico-8.com
version 36
__lua__
u=123function f()end f"circfill 50 50 20 7\nn <- pack\nrawset n f u\nrawset n u c"print(n)print(n.f)f""