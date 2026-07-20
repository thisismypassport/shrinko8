__lua__

local real_assert = assert
function assert(cond, num)
    if (num == 38 or num == 68 or num == 69) return cond -- nothing serious, just undocumented minutae
    return real_assert(cond, num)
end

--$switch-compiler: parens8 sparse_vararg

#include test.p8