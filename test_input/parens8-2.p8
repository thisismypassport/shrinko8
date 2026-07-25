__lua__

-- note: this test can only switch compiler once!
--$def-alias: go = parens8 rom compress
--$switch-compiler: go

-- (automatic full cleanup):
assert(ps8_inst == nil)
assert(ps8_runtime == nil)

printh("done")
