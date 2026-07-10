-- meant for lua 5.2 (unclear if higher versions will help or hinder)
-- can be loaded before a lua script (e.g. one created via `-U --unminify-plain-lua`) in order to let it access some deal of lua builtins
-- (TBD: extend with more stuff)
-- (TBD: implement more pico-specific semantics)
-- UNRESOLVED QUESTION: why did I do all this instead of taking one of 100 better existing p8 libraries

do
    local _ENV = _ENV
    local math, table, string, bit32 = math, table, string, bit32
    local tostring = tostring

    ---- MATH

    -- very best-effort (aka least-result)
    function band(a, b)
        return bit32.band(a * 0x10000, b * 0x10000) / 0x10000
    end
    function bor(a, b)
        return bit32.bor(a * 0x10000, b * 0x10000) / 0x10000
    end
    function bxor(a, b)
        return bit32.bxor(a * 0x10000, b * 0x10000) / 0x10000
    end
    function shl(a, b)
        local res = bit32.lshift(a * 0x10000, b) / 0x10000
        if a < 0 and res >= 0x8000 then res = res - 0x10000 end
        return res
    end
    function shr(a, b)
        local res = bit32.arshift(a * 0x10000, b) / 0x10000
        if a < 0 and res >= 0x8000 then res = res - 0x10000 end
        return res
    end
    function lshr(a, b)
        return bit32.rshift(a * 0x10000, b) / 0x10000
    end
    function rotl(a, b)
        return bit32.lrotate(a * 0x10000, b) / 0x10000
    end
    function rotr(a, b)
        return bit32.rrotate(a * 0x10000, b) / 0x10000
    end

    abs = math.abs
    flr = math.floor
    ceil = math.ceil
    min = math.min
    max = math.max
    sqrt = math.sqrt

    function mid(a, b, c)
        local minbc, maxbc = min(b, c), max(b, c)
        if a < minbc then return minbc
        elseif a > maxbc then return maxbc
        else return a end
    end

    ---- TABLES

    pack = table.pack
    unpack = table.unpack

    function add(tbl, val, idx)
        if type(tbl) ~= "table" then return end
        if idx then
            table.insert(tbl, idx, val)
        else
            table.insert(tbl, val)
        end
        return val
    end

    function deli(tbl, idx)
        if type(tbl) ~= "table" then return end
        return table.remove(tbl, idx)
    end

    function all(tbl)
        local idx, prev = 1
        return function()
            while true do
                if idx > #tbl then return end
                local val = tbl[idx]
                if prev and val == prev then
                    idx = idx + 1
                    val = tbl[idx]
                end
                if val then
                    prev = val
                    return val
                end
                idx = idx + 1
            end
        end
    end

    function foreach(tbl, func)
        for val in all(tbl) do
            func(val)
        end
    end

    function count(tbl, ...)
        if type(tbl) ~= "table" then return end
        if select('#', ...) == 0 then return #tbl end

        local num = 0
        for i=1,#tbl do
            if tbl[i] == ... then num = num + 1 end
        end
        return num
    end

    ---- STRINGS

    getmetatable("").__index = function(str, key)
        if type(key) == "number" then
            key = math.floor(key)
            local sub = string.sub(str, key, key)
            if sub == "" then sub = nil end
            return sub
        end
    end

    function tostr(val, flag)
        local ty = type(val)
        if ty == "number" then
            local hex, long
            if flag then
                hex = true
                if type(flag) == "number" then
                    hex = band(flag, 1) > 0
                    long = band(flag, 2) > 0
                end
            end
            if hex then
                if val < 0 then val = val + 0x10000 end
                if long then
                    return string.format("0x%08x", val * 0x10000)
                else
                    return string.format("0x%04x.%04x", math.floor(val), bit32.band(val * 0x10000, 0xffff))
                end
            else
                if long then
                    return string.format("%d", val * 0x10000)
                else
                    local res = string.format("%.4f", val)
                    return (string.gsub(res, "%.?0+$", ""))
                end
            end
        elseif (ty == "table" or ty == "function" or ty == "thread") and not flag then
            return "["..ty.."]"
        end
        return tostring(val)
    end

    function tonum(val, flag)
        local hex, long, zero
        if flag then
            hex = band(flag, 1) > 0
            long = band(flag, 2) > 0
            zero = band(flag, 4) > 0
        end

        local ty = type(val)
        if ty == "string" then
            if hex then
                val = tonumber(val, 16)
            else
                val = tonumber(val)
            end
            if val then
                if long then
                    return math.floor(val) / 0x10000
                else
                    return math.floor(val * 0x10000) / 0x10000
                end
            end
        elseif ty == "number" then
            return val
        elseif ty == "boolean" then
            return val and 1 or 0
        end

        if zero then return 0 end
    end

    sub = string.sub
    ord = string.byte

    function chr(...)
        local bytes = {...}
        for i=1,#bytes do
            bytes[i] = bit32.band(math.floor(bytes[i]), 0xff)
        end
        return string.char(table.unpack(bytes))
    end

    function split(str, sep, asnum)
        if not sep then sep = "," end
        if not asnum then asnum = true end

        local pattern
        local result = {}
        if type(sep) == "number" then
            local i, n = 1, #str
            while i + sep <= n do
                table.insert(result, string.sub(str, i, i+sep-1))
                i = i + sep
            end
            if i <= n then table.insert(result, string.sub(str, i)) end
        else
            str = str .. sep
            if string.find(sep, "%w") then
                pattern = "(.-)"..sep
            else
                pattern = "(.-)%"..sep
            end

            for val in string.gmatch(str, pattern) do
                if asnum then
                    num = tonum(val)
                    if num then val = num end
                end
                table.insert(result, val)
            end
        end
        return result
    end

    ---- MEMORY

    _p8mem = {}

    function peek(addr, n)
        if n then
            if n == 0 then return end
            return peek(addr), peek(addr + 1, n - 1)
        end
        addr = bit32.band(math.floor(addr), 0xffff)
        return _p8mem[addr] or 0
    end
    function peek2(addr, n)
        if n then
            if n == 0 then return end
            return peek2(addr), peek2(addr + 2, n - 1)
        end
        return peek(addr) + bit32.lshift(peek(addr + 1), 8)
    end
    function peek4(addr, n)
        if n then
            if n == 0 then return end
            return peek4(addr), peek4(addr + 4, n - 1)
        end
        return peek2(addr) + (peek2(addr + 2) / 0x10000)
    end

    function poke(addr, v, ...)
        if ... then
            poke(addr, v)
            return poke(addr + 1, ...)
        end
        addr = bit32.band(math.floor(addr), 0xffff)
        _p8mem[addr] = bit32.band(math.floor(v), 0xff)
    end
    function poke2(addr, v, ...)
        if ... then
            poke2(addr, v)
            return poke2(addr + 2, ...)
        end
        poke(addr, v)
        poke(addr + 1, bit32.rshift(v, 8))
    end
    function poke4(addr, v, ...)
        if ... then
            poke4(addr, v)
            return poke4(addr + 4, ...)
        end
        poke2(addr, v)
        poke2(addr + 2, v * 0x10000)
    end

    ---- IO

    function printh(msg, fname, overwrite)
        local fh = fname and io.open(fname, overwrite and "w" or "a") or io.output()
        assert(fh, "printh -> io.open")
        fh:write(tostr(msg) .. "\n")
        if fname then fh:close() end
    end

    function cstore(dest, src, len, fname)
        -- we store binary roms only
        local fh = io.open(fname, "r+b")
        if not fh then fh = io.open(fname, "w+b") end
        assert(fh, "cstore -> io.open")
        fh:seek("set", dest)
        fh:write(chr(peek(src, len)))
        fh:close()
    end
end

local env, pairs = _ENV, pairs
_ENV = {}
for k, v in pairs(env) do _ENV[k] = v end
