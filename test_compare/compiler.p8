pico-8 cartridge // http://www.pico-8.com
version 41
__lua__
function interp(code)end function repl(str)end
local l_local=1
g_global={member=2}
function foo()end
local function bar()end
repl'local my_local=3\nprint"a string"\ng_global.member=foo(l_local)\nif(bar)bar(my_local)'interp[[

,
,nil,true,false,num:0,num:4660.33777,num:-3,str:'hello	!',str:'world\nand bytecode★',setlocal:h,setlocal:g,setlocal:f,setlocal:e,setlocal:d,setlocal:c,setlocal:b,setlocal:a,
,nil,nil,setlocal:b,setlocal:a,
,nil,setlocal:c,
,num:1,num:2,num:3,pop,pop,setlocal:i,
,local:d,local:e,local:f,setlocal:c,setlocal:b,setlocal:a,
,local:h,local:g,setlocal:h,setlocal:g,
,local:a,setglobal:g_newglob,
,global:g_global,setlocal:h,
,local:d,nil,nil,setlocal:c,setlocal:b,setlocal:a,
,num:4,num:5,num:6,pop,pop,setlocal:i,
,global:g_global,member:member,setlocal:i,
,global:g_global,local:d,setmember:member2,
,global:g_global,num:3,num:4,setindex,
,global:g_global,num:3,index,setlocal:j,
,local:a,local:b,add,local:c,local:d,mul,local:e,div,local:f,idiv,local:g,local:h,pow,mod,sub,setlocal:k,
,local:a,local:b,band,local:c,local:d,bxor,local:e,bxor,bor,setlocal:l,
,local:a,local:b,shl,local:c,sar,local:d,shr,local:e,ror,local:f,rol,setlocal:m,
,local:a,local:b,lt,and:1,local:c,local:d,gt,target:1,or:2,local:e,local:f,le,and:3,local:g,local:h,ge,target:3,target:2,setlocal:n,
,local:a,local:b,ne,and:4,local:c,local:d,ne,target:4,or:5,local:e,local:f,eq,target:5,setlocal:o,
,local:a,minus,local:b,bnot,local:c,not,global:g_global,length,local:d,peek,local:e,peek2,local:f,peek4,cat,cat,cat,cat,cat,cat,setlocal:p,
,table,setlocal:q,
,table,dup,num:1,append,dup,num:2,append,dup,num:3,append,dup,num:4,setmember:a,dup,num:5,setmember:b,dup,num:100,num:6,setindex,dup,num:7,append,dup,num:8,append,dup,num:9,setmember:c,dup,local:a,local:b,setindex,setlocal:r,
,global:foo,num:1,num:2,num:3,call:3,pop,
,global:foo,global:foo,vacall:0,call:1&va,pop,
,global:foo,num:1,num:2,num:3,global:foo,str:'z',vacall:1,call:4&va,pop,
,global:foo,global:foo,call:0,call:1,pop,
,global:g_global,method:call,num:1,num:2,call:3,pop,
,global:g_global,method:call,table,dup,num:1,append,dup,num:2,append,call:2,pop,
,global:foo,call:0,setlocal:s,
,global:foo,vacall:0,unpack:3,setlocal:v,setlocal:u,setlocal:t,
,table,dup,num:1,append,dup,global:foo,vacall:0,extend,setlocal:w,
,global:foo,call:0,nil,nil,setlocal:z,setlocal:y,setlocal:x,
,num:1,global:foo,call:0,pop,setlocal:aa,
,func:6,setlocal:p2,setlocal:p1,
,
,local:p1,local:p2,eq,ifnot:7,
,
,ret:0,target:7,
,upval:r,local:p1,index,upval:q,local:p2,index,add,ret:1,target:6,setglobal:f1,
,func:8,setvarargs:-0,
,
,table,dup,num:10,append,dup,num:11,setmember:a,dup,varargs,extend,setupval:a,
,global:print,varargs,unpack:1,call:1,pop,
,upval:f2,upval:a,varargs,tailcall:2&va,target:8,setlocal:f2,
,global:g_global,member:misc,func:9,
,target:9,setmember:f3,
,global:g_global,func:10,setvarargs:-3,setlocal:b,setlocal:a,setlocal:self,
,
,global:print,local:self,call:1,pop,
,num:-1,varargs,unpack:2,setlocal:w,setlocal:v,setlocal:u,
,local:b,local:a,varargs,unpack:1,varargs,ret:4&va,target:10,setmember:call,
,local:b,num:1,add,setlocal:b,
,local:c,num:2,sub,setlocal:c,
,local:d,num:3,mul,setlocal:d,
,local:e,num:4,div,setlocal:e,
,local:f,num:5,idiv,setlocal:f,
,local:g,num:6,mod,setlocal:g,
,local:h,num:7,pow,setlocal:h,
,local:b,num:1,band,setlocal:b,
,local:c,num:2,bor,setlocal:c,
,local:d,num:3,bxor,setlocal:d,
,local:b,num:4,shl,setlocal:b,
,local:c,num:4,sar,setlocal:c,
,local:d,num:5,shr,setlocal:d,
,local:e,num:6,rol,setlocal:e,
,local:f,num:7,ror,setlocal:f,
,global:g_global,num:3,dup2,index,num:1,add,setindex,
,global:g_global,dup,member:x,num:2,sub,setmember:x,
,table,dup,num:1,setmember:member,dup,member:member,num:2,add,setmember:member,
,table,dup,num:1,setmember:member,local:b,local:c,add,dup2,index,num:3,sub,setindex,
,local:a,local:b,eq,ifnot:11,
,
,global:print,str:'eq',call:1,pop,target:11,
,local:a,local:b,ne,ifnot:12,
,
,global:print,str:'ne',call:1,pop,goto:13,target:12,
,
,
,global:print,str:'eq',call:1,pop,target:13,
,local:a,local:b,ne,ifnot:14,
,
,global:print,str:'ne1',call:1,pop,target:14,
,local:a,local:b,ne,ifnot:15,
,
,global:print,str:'ne1',call:1,pop,goto:16,target:15,
,
,
,global:print,str:'eq1',call:1,pop,target:16,
,local:a,local:b,ne,ifnot:17,
,
,global:print,str:'ne1',call:1,pop,goto:18,target:17,
,local:a,local:b,eq,ifnot:19,
,
,global:print,str:'eq1',call:1,pop,goto:20,target:19,
,
,
,global:print,str:'??1',call:1,pop,target:20,target:18,
,target:21,local:c,local:d,eq,ifnot:22,
,
,global:print,str:'stuck',call:1,pop,goto:21,target:22,
,target:23,local:c,local:d,ne,ifnot:24,
,
,global:print,str:'nel',call:1,pop,goto:23,target:24,
,target:25,local:c,local:d,ne,ifnot:26,
,
,local:f,ifnot:27,
,
,goto:26,target:27,goto:25,target:26,
,target:28,
,
,global:print,str:'nel2',call:1,pop,
,local:f,ifnot:30,
,
,goto:29,target:30,local:e,local:f,eq,ifnot:28,target:29,
,num:1,num:10,num:1,forinit:32,target:31,setlocal:i,
,
,global:print,local:i,call:1,pop,fornext:31,target:32,
,num:1,num:-5,num:-1,forinit:34,target:33,setlocal:j,
,
,global:print,local:j,call:1,pop,fornext:33,target:34,
,num:2,setglobal:g_step,
,num:1,num:4,global:g_step,forinit:36,target:35,setlocal:k,
,
,global:print,local:k,call:1,pop,fornext:35,target:36,
,num:2,setglobal:g_step,
,num:1,global:g_step,global:g_step,forinit:38,target:37,setlocal:k,
,
,global:print,local:k,call:1,pop,fornext:37,target:38,
,global:next,global:g_global,nil,gforinit:40,target:39,unpack:1,setlocal:k,
,
,global:print,local:k,call:1,pop,gfornext:39,target:40,
,global:next,num:1,num:2,num:3,global:print,local:k,vacall:1,unpack:0,pop,pop,gforinit:42,target:41,unpack:1,setlocal:k,
,
,global:print,local:k,call:1,pop,gfornext:41,target:42,
,global:all,table,dup,num:1,append,dup,num:2,append,dup,num:3,append,vacall:1,unpack:3,gforinit:44,target:43,unpack:2,setlocal:v,setlocal:k,
,
,global:print,local:k,local:v,cat,call:1,pop,gfornext:43,target:44,
,target:back,
,local:a,ifnot:45,
,
,goto:fwd,goto:46,target:45,
,
,
,goto:back,target:46,
,target:fwd,
,
,
,global:print,str:'ende',call:1,pop]]
print("back in the main code! "..l_local)
