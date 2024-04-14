from utils import *
from pico_defs import decode_p8str

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
    tab_stop = 's',
    wrap = 'r',
    ch_width = 'x',
    ch_height = 'y',
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
    width = 4; height = 6; wide_width = 8; tab_width = 16
    width_adjusts = (); is_custom = True

k_pico_font = PicoFont(is_custom=False)

def get_p8scii_param(str, pos):
    ch = str_get(str, pos, '')
    if '0' <= ch <= '9':
        return ord(ch) - ord('0')
    elif ch >= 'a': # all the way up
        return ord(ch) - ord('a') + 10
    else:
        return 0

# WARNING: a lot of this is not tested yet
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

        start = end
        cch = str[start]
        pos = start + 1
        length = 0

        if cch == k_ctrl_chars.end:
            yield start, Dynamic(type=cch, rest=str[pos:])
            return

        elif cch == k_ctrl_chars.rep:
            val = get_p8scii_param(str, pos)
            ch = str_get(str, pos + 1, '')
            length = 2
            yield start, Dynamic(type=cch, count=val, char=ch)

        elif cch in (k_ctrl_chars.bg, k_ctrl_chars.fg):
            val = get_p8scii_param(str, pos)
            length = 1
            yield start, Dynamic(type=cch, color=val)

        elif cch == k_ctrl_chars.horz:
            val = get_p8scii_param(str, pos) - 16
            length = 1
            yield start, Dynamic(type=cch, horz=val, vert=0)

        elif cch == k_ctrl_chars.vert:
            val = get_p8scii_param(str, pos) - 16
            length = 1
            yield start, Dynamic(type=cch, horz=0, vert=val)

        elif cch == k_ctrl_chars.move:
            hval = get_p8scii_param(str, pos) - 16
            vval = get_p8scii_param(str, pos + 1) - 16
            length = 2
            yield start, Dynamic(type=cch, horz=hval, vert=vval)

        elif cch == k_ctrl_chars.decor:
            val = get_p8scii_param(str, pos)
            ch = str_get(str, pos + 1, '')
            length = 2
            hval, vval = (val & 0x3) - 2, (val >> 2) - 8
            yield start, Dynamic(type=cch, horz=hval, vert=vval, char=ch)

        elif cch == k_ctrl_chars.audio:
            endpos = pos
            while endpos < len(str) and str[endpos] not in " \n": # TODO: inexact...
                endpos += 1
            yield start, Dynamic(type=cch, sound=str[pos:endpos])
            length = endpos + 1 - pos

        elif cch == k_ctrl_chars.cmd:
            cmd = str_get(str, pos)
            if cmd in (k_ctrl_cmds.delay, k_ctrl_cmds.tab_stop, k_ctrl_chars.ch_width, k_ctrl_chars.ch_height):
                val = get_p8scii_param(str, pos + 1)
                length = 2
                yield start, Dynamic(type=cmd, count=val)
            elif cmd == k_ctrl_cmds.clear:
                val = get_p8scii_param(str, pos + 1)
                length = 2
                yield start, Dynamic(type=cmd, color=val)
            elif cmd == k_ctrl_cmds.jump:
                hval = get_p8scii_param(str, pos + 1) * 4
                vval = get_p8scii_param(str, pos + 2) * 4
                length = 3
                yield start, Dynamic(type=cmd, horz=hval, vert=vval)
            elif cmd == k_ctrl_cmds.wrap:
                val = get_p8scii_param(str, pos + 1) * 4
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

class P8sciiFlags(Bitmask):
    wide = tall = pinball = custom_font = wrapped = ... # corresponds to pico8 state
    # invert = border = solid = stripe = ... (this pico8 state doesn't matter)
    word_wrap = ... # custom flags
    none = 0

class MeasurerHookBase:
    def on_line_end(m, measurer, pos):
        pass

# WARNING: a lot of this is not tested yet
class P8sciiMeasurer:
    def __init__(m, *, pos=Point.zero, flags=P8sciiFlags.none, wrap_width=None, font=k_pico_font, hook=None):
        m.start_x, m.start_y = pos.x, pos.y
        m.x, m.y = pos.x, pos.y
        m.max_x, m.max_y = pos.x, pos.y
        m.custom_font = font
        m.flags = flags
        m.wrap_w = 128 if flags.wrapped else sys.maxsize
        m.word_wrap_w = default(wrap_width, 128) if flags.word_wrap else sys.maxsize
        m.word_wrap = flags.word_wrap
        m.wraps = []
        m.saved_wrap = None
        m.hook = hook
        m.update_font(m.cutsom_font if m.flags.custom_font else k_pico_font)
        m.update_wide()
        m.curr_ch_h = m.ch_h
    
    def update_font(m, font):
        m.font = font
        m.ch_w, m.ch_h = font.width, font.height
        m.big_ch_w = font.wide_width
        m.last_ch_w = m.ch_w
        m.tab_w = font.tab_width
    
    def update_wide(m):
        m.wide_x = m.flags.wide or m.flags.pinball
        m.wide_y = m.flags.tall or m.flags.pinball

    def advance_line(m, pos):
        if m.hook:
            m.hook.on_line_end(m, pos)
        
        m.x = m.start_x
        m.y += m.curr_ch_h
        m.curr_ch_h = m.ch_h
        m.max_y = max(m.y, m.max_y)

    def process_rawch(m, pos, ch_w, ch_h):
        if m.wide_x:
            ch_w *= 2
        if m.wide_y:
            ch_h *= 2

        m.last_ch_w = ch_w
        m.x += ch_w

        if m.word_wrap and m.x > m.word_wrap_w:
            # prepare manual wrapping (won't work well with curr_ch_h currently...)
            if m.saved_wrap:
                wrap_pos, wrap_x, replace = m.saved_wrap
                m.wraps.append((wrap_pos, replace))
                m.saved_wrap = None
            else:
                wrap_x = m.x - ch_w
                m.wraps.append((pos, False))
            
            post_wrap_w = m.x - wrap_x
            m.x = wrap_x # just for the line hook
            m.advance_line(pos)
            m.x += post_wrap_w

        elif m.x > m.wrap_w:
            m.advance_line(pos)
            m.x += ch_w
        
        m.max_x = max(m.x, m.max_x)
        m.curr_ch_h = max(m.curr_ch_h, ch_h)

    def process_rawline(m, start, line):
        for i, ch in enumerate(line):
            pos = start + i

            ch_w = m.big_ch_w if ord(ch) >= 128 else m.ch_w
            if m.font.width_adjusts:
                ch_w += list_get(m.font.width_adjusts, ord(ch), 0)
            
            if m.word_wrap and ch == ' ':
                m.saved_wrap = pos, m.x + ch_w, True
            
            m.process_rawch(pos, ch_w, m.ch_h)

    def move_to(m, x, y):
        m.x, m.y = x, y
        m.max_x = max(m.x, m.max_x)
        m.max_y = max(m.y, m.max_y)
    
    def process(m, text):
        for start, cmd in parse_p8scii(text):
            if isinstance(cmd, str):
                m.process_rawline(start, cmd)
            elif cmd.type == k_ctrl_chars.rep:
                m.process_rawline(cmd.char * cmd.count)
            elif cmd.type == (k_ctrl_chars.horz, k_ctrl_chars.vert, k_ctrl_chars.move):
                m.move_to(m.x + cmd.horz, m.y + cmd.vert)
            elif cmd.type == k_ctrl_chars.back:
                m.x -= m.last_ch_w
            elif cmd.type == k_ctrl_chars.tab:
                tab_delta = m.tab_w - m.x % m.tab_w
                m.move_to(m.x + tab_delta, m.y)
            elif cmd.type == k_ctrl_chars.line:
                m.advance_line(start)
            elif cmd.type == k_ctrl_chars.ret:
                m.x = m.start_x
            elif cmd.type == k_ctrl_chars.cfont:
                m.update_font(m.custom_font)
            elif cmd.type == k_ctrl_chars.dfont:
                m.update_font(k_pico_font)
            elif cmd.type == k_ctrl_cmds.home:
                m.x, m.y = m.start_x, m.start_y
            elif cmd.type == k_ctrl_cmds.jump:
                m.move_to(cmd.horz, cmd.vert)
            elif cmd.type == k_ctrl_cmds.tab_stop:
                m.tab_w = cmd.count
            elif cmd.type == k_ctrl_cmds.wrap:
                m.wrap_w = cmd.count
            elif cmd.type == k_ctrl_cmds.ch_width:
                m.ch_w = cmd.count
                m.big_ch_w = cmd.count + m.font.wide_width - m.font.width
            elif cmd.type == k_ctrl_cmds.ch_height:
                m.ch_h = cmd.count
            elif cmd.type in (k_ctrl_cmds.char, k_ctrl_cmds.hexchar):
                m.process_rawch(start, 8, 8)
            elif cmd.type == k_ctrl_cmds.wide:
                m.flags.wide = cmd.enable
                m.update_wide()
            elif cmd.type == k_ctrl_cmds.tall:
                m.flags.tall = cmd.enable
                m.update_wide()
            elif cmd.type == k_ctrl_cmds.pinball:
                m.flags.pinball = cmd.enable
                m.update_wide()
        
        if m.word_wrap:
            delta = 0
            for pos, replace in m.wraps:
                pos += delta
                if replace:
                    text = str_replace_at(text, pos, 1, "\n")
                else:
                    text = str_insert(text, pos, "\n")
                    delta += 1

            m.wraps.clear()
            if m.x > m.start_x:
                m.saved_wrap = 0, m.x, False
            return text
        # else, nothing to return

    def finish(m):
        m.advance_line(0)
        return Point(m.max_x, m.max_y)

def measure_p8scii(text, **opts): # see P8sciiMeasurer's ctor for params
    measurer = P8sciiMeasurer(**opts)
    text = measurer.process(text)
    if e(text):
        return measurer.finish(), text
    else:
        return measurer.finish()

def bytes_to_string_contents(bytes):
    """convert a bytes objects to a pico8 string literal, without the surrounding "-s"""
    from pico_output import format_string_literal # already implemented here...
    return format_string_literal(decode_p8str(bytes), long=False, quote='"')[1:-1]
