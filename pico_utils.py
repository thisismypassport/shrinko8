from utils import *

k_ctrl_chars = Dynamic(
    end=chr(0),
    rep=chr(1),
    bg=chr(2),
    horz=chr(3),
    vert=chr(4),
    move=chr(5),
    cmd=chr(6),
    audio=chr(7),
    back=chr(8),
    tab=chr(9),
    line=chr(10),
    decor=chr(11),
    fg=chr(12),
    ret=chr(13),
    cfont=chr(14),
    dfont=chr(15),
)

k_ctrl_cmds = Dynamic(
    skips = "123456789",
    clear = 'c',
    delay = 'd',
    home = 'g',
    jump = 'j',
    stop = 's',
    wrap = 'r',
    width = 'x',
    height = 'y',
    wide = 'w',
    tall = 't',
    stripe = '=',
    pinball = 'p',
    invert = 'i',
    border = 'b',
    solid = '#',
    disable = '-',
    poke = '@',
    endpoke = '!',
    char = '.',
    hexchar = ':',
)

k_ctrl_flag_cmds = (k_ctrl_cmds.wide, k_ctrl_cmds.tall, k_ctrl_cmds.stripe, k_ctrl_cmds.pinball, k_ctrl_cmds.invert, k_ctrl_cmds.border, k_ctrl_cmds.solid)

class PicoFont(Tuple):
    fields = ("width", "height", "wide_width", "tab_width", "char_widths", "default_attrs", "is_custom")
    defaults = (4, 6, 8, 16, None, None, True)

k_pico_font = PicoFont(is_custom=False)

def get_p8scii_param(ch):
    if '0' <= ch <= '9':
        return ord(ch) - ord('0')
    elif ch >= 'a': # all the way up
        return ord(ch) - ord('a') + 10
    else:
        return 0

# I wrote this whole thing up and probably didn't actually run it even once - don't use it yet!
def parse_p8scii(str):
    start = 0
    while start < len(str):
        end = start
        while end < len(str) and str[end] >= chr(16):
            end += 1

        if end > start:
            yield start, str[start:end]
        if end >= len(str):
            break

        cch = str[end]
        pos = end + 1
        length = 0

        if cch == k_ctrl_chars.end:
            yield start, Dynamic(type=cch, rest=str[pos:])
            return

        elif cch == k_ctrl_chars.rep:
            val = get_p8scii_param(str_get(str, pos))
            ch = str_get(str, pos + 1)
            length = 2
            yield start, Dynamic(type=cch, count=val, char=ch)

        elif cch in (k_ctrl_chars.bg, k_ctrl_chars.fg):
            val = get_p8scii_param(str_get(str, pos))
            length = 1
            yield start, Dynamic(type=cch, color=val)

        elif cch in (k_ctrl_chars.horz, k_ctrl_chars.vert):
            val = get_p8scii_param(str_get(str, pos)) - 16
            length = 1
            yield start, Dynamic(type=cch, count=val)

        elif cch == k_ctrl_chars.move:
            hval = get_p8scii_param(str_get(str, pos)) - 16
            vval = get_p8scii_param(str_get(str, pos + 1)) - 16
            length = 2
            yield start, Dynamic(type=cch, horz=hval, vert=vval)

        elif cch == k_ctrl_chars.decor:
            val = get_p8scii_param(str_get(str, pos))
            ch = str_get(str, pos + 1)
            length = 2
            hval, vval = (val & 0x3) - 2, (val >> 2) - 8
            yield start, Dynamic(type=cch, horz=hval, vert=vval, char=ch)

        elif cch == k_ctrl_chars.audio:
            endpos = pos
            while endpos < len(str) and str[endpos] not in " \n":
                endpos += 1
            yield start, Dynamic(type=cch, sound=str[pos:endpos])
            length = endpos + 1 - pos

        elif cch == k_ctrl_chars.cmd:
            cmd = str_get(str, pos)
            if cmd in (k_ctrl_cmds.delay, k_ctrl_cmds.stop, k_ctrl_chars.width, k_ctrl_chars.height):
                val = get_p8scii_param(str_get(str, pos + 1))
                length = 2
                yield start, Dynamic(type=cmd, count=val)
            elif cmd == k_ctrl_cmds.clear:
                val = get_p8scii_param(str_get(str, pos + 1))
                length = 2
                yield start, Dynamic(type=cmd, color=val)
            elif cmd == k_ctrl_cmds.jump:
                hval = get_p8scii_param(str_get(str, pos + 1)) * 4
                vval = get_p8scii_param(str_get(str, pos + 2)) * 4
                length = 3
                yield start, Dynamic(type=cmd, horz=hval, vert=vval)
            elif cmd == k_ctrl_cmds.wrap:
                val = get_p8scii_param(str_get(str, pos + 1)) * 4
                length = 2
                yield start, Dynamic(type=cmd, count=val)
            elif cmd in k_ctrl_flag_cmds:
                length = 1
                yield start, Dynamic(type=cmd, enable=True)
            elif cmd == k_ctrl_cmds.disable:
                cmd2 = str_get(str, pos + 1)
                cmd = cmd2 if cmd in k_ctrl_flag_cmds else cmd
                length = 2
                yield start, Dynamic(type=cmd, enable=False)
            elif cmd == k_ctrl_cmds.poke:
                addr = maybe_int(str[pos + 1 : pos + 5], base=16)
                count = maybe_int(str[pos + 5 : pos + 9], base=16)
                data_len = default(count, 0)
                data = str[pos + 9 : pos + 9 + data_len]
                length = 9 + data_len
                yield start, Dynamic(type=cmd, addr=addr, count=count, data=data)
            elif cmd == k_ctrl_cmds.endpoke:
                addr = maybe_int(str[pos + 1 : pos + 5], base=16)
                data = str[pos + 5 :]
                yield start, Dynamic(type=cmd, addr=addr, data=data)
                return
            elif cmd == k_ctrl_cmds.char:
                data = str[pos + 1 : pos + 9]
                length = 9
                yield start, Dynamic(type=cmd, data=data)
            elif cmd == k_ctrl_cmds.hexchar:
                data = str[pos + 1 : pos + 17]
                length = 17
                yield start, Dynamic(type=cmd, data=data)
            else:
                length = 1
                yield start, Dynamic(type=cmd)

        else:
            yield start, Dynamic(type=cch)

        start = pos + length
            
def bytes_to_string_contents(bytes): # TODO: just use format_string_literal... 
    data = []

    esc_map = {
        "\0": "\\0",
        "\r": "\\r",
        "\n": "\\n",
        "\"": "\\\"",
        "\\": "\\\\",
    }

    for i, b in enumerate(bytes):
        ch = chr(b)
        ch = esc_map.get(ch, ch)
        if b == 0 and ord('0') <= list_get(bytes, i + 1) <= ord('9'):
            ch += "00"
        data.append(ch)

    return "".join(data)
    