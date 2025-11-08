foo=1 --lint: used::foo

-- initialize table from string of key/value pairs
function kv2tab(kvstr)
 local out={}
 local kvs=split(kvstr)
 for kev in all(kvs) do
   local k,v=unpack(split(kev,"="))
   out[k]=v
 end
 return out
end

function _draw()
 cls(1)
 local t=kv2tab(--[[language::split (member=string)s,]]"beans=1,franks=\"foo\"")
 print("beans="..t.beans)
 print("franks="..t.franks)
end
--preserve: *=*.*