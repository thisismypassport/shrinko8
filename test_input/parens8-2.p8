__lua__

-- note: this test can only switch compiler once!
--$switch-compiler: parens8 rom

-- (automatic full cleanup):
assert(ps8_inst == nil)
assert(ps8_runtime == nil)

printh("done")
