from utils import *
from sdl2_utils import Color

class Memory(bytearray):
    def copy(m):
        return Memory(m[:])

    def replace(m, src):
        m[:] = src

    def size(m):
        return len(m)

    def get8(m, i):
        return m[i]

    def set8(m, i, v):
        m[i] = v
        
    def get_block(m, start, size):
        return m[start:start+size]
        
    def set_block(m, start, src):
        m[start:start+len(src)] = src

    def copy8(m, dest, src, size, src_memory = None):
        m.set_block(dest, (src_memory or m).get_block(src, size))
        
    def fill8(m, dest, value, size):
        m.set_block(dest, bytearray((value,)) * size)
        
    def get16(m, i):
        return m.get8(i) | (m.get8(i + 1) << 8)
    
    def set16(m, i, v):
        m.set8(i, v & 0xff)
        m.set8(i + 1, (v >> 8) & 0xff)

    def get32(m, i):
        return m.get16(i) | (m.get16(i + 2) << 16)

    def set32(m, i, v):
        m.set16(i, v & 0xffff)
        m.set16(i + 2, (v >> 16) & 0xffff)
        
    def get8_bits(m, i, shift, mask):
        return (m.get8(i) >> shift) & mask

    def set8_bits(m, i, shift, mask, v):
        m.set8(i, (m.get8(i) & ~(mask << shift)) | ((v & mask) << shift))

    def get4(m, ix):
        i, high = ix
        return m.get8_bits(i, 4 if high else 0, 0xf)

    def set4(m, ix, value):
        i, high = ix
        m.set8_bits(i, 4 if high else 0, 0xf, value)

def mem_tile_addr(x, y):
    return y * 0x40 + (x >> 1), (x & 1)
    
def mem_map_addr(x, y):
    if y >= 0x20: y -= 0x40  # in effect
    return 0x2000 + y * 0x80 + x

def mem_flag_addr(x, y):
    return 0x3000 + y * 0x80 + x

def mem_music_addr(music, ch):
    return 0x3100 + music * 0x4 + ch
    
def mem_sfx_addr(sound, note):
    return 0x3200 + sound * 0x44 + note * 0x2
    
def mem_sfx_info_addr(sound, i):
    return mem_sfx_addr(sound, 0x20) + i

k_rom_size = 0x4300
k_cart_size = 0x8000
k_code_size = k_cart_size - k_rom_size
k_trailer_size = 0x20

k_palette = [
    Color(0x00, 0x00, 0x00, 0xff), # black
    Color(0x1d, 0x2b, 0x53, 0xff), # dark blue
    Color(0x7e, 0x25, 0x53, 0xff), # magenta
    Color(0x00, 0x87, 0x51, 0xff), # dark green
    Color(0xab, 0x52, 0x36, 0xff), # dark brown
    Color(0x5f, 0x57, 0x4f, 0xff), # dark gray
    Color(0xc2, 0xc3, 0xc7, 0xff), # gray
    Color(0xff, 0xf1, 0xe8, 0xff), # white
    Color(0xff, 0x00, 0x4d, 0xff), # hot pink
    Color(0xff, 0xa3, 0x00, 0xff), # orange
    Color(0xff, 0xec, 0x27, 0xff), # yellow
    Color(0x00, 0xe4, 0x36, 0xff), # green
    Color(0x29, 0xad, 0xff, 0xff), # light blue
    Color(0x83, 0x76, 0x9c, 0xff), # violet
    Color(0xff, 0x77, 0xa8, 0xff), # pink
    Color(0xff, 0xcc, 0xaa, 0xff), # light pink
    # alt. colors
    Color(0x29, 0x18, 0x14, 0xff),
    Color(0x11, 0x1D, 0x35, 0xff),
    Color(0x42, 0x21, 0x36, 0xff),
    Color(0x12, 0x53, 0x59, 0xff),
    Color(0x74, 0x2F, 0x29, 0xff),
    Color(0x49, 0x33, 0x3B, 0xff),
    Color(0xA2, 0x88, 0x79, 0xff),
    Color(0xF3, 0xEF, 0x7D, 0xff),
    Color(0xBE, 0x12, 0x50, 0xff),
    Color(0xFF, 0x6C, 0x24, 0xff),
    Color(0xA8, 0xE7, 0x2E, 0xff),
    Color(0x00, 0xB5, 0x43, 0xff),
    Color(0x06, 0x5A, 0xB5, 0xff),
    Color(0x75, 0x46, 0x65, 0xff),
    Color(0xFF, 0x6E, 0x59, 0xff),
    Color(0xFF, 0x9D, 0x81, 0xff),
]

k_palette_map = {color: i for i, color in enumerate(k_palette)}

k_charset = [
    None, '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '	', '\n', 'ᵇ', 'ᶜ', '\r', 'ᵉ', 'ᶠ',
    '▮', '■', '□', '⁙', '⁘', '‖', '◀', '▶', '「', '」', '¥', '•', '、', '。', '゛', '゜'
]
for i in range(0x20, 0x7f):
    k_charset.append(chr(i))
k_charset += [
    '○',
    '█','▒','🐱','⬇️','░','✽','●','♥','☉','웃','⌂','⬅️','😐','♪','🅾️','◆','…','➡️','★','⧗','⬆️','ˇ','∧','❎','▤','▥',
    'あ','い','う','え','お','か','き','く','け','こ','さ','し','す','せ','そ','た','ち','つ','て','と','な','に','ぬ','ね','の','は','ひ','ふ','へ','ほ',
    'ま','み','む','め','も','や','ゆ','よ','ら','り','る','れ','ろ','わ','を','ん','っ','ゃ','ゅ','ょ','ア','イ','ウ','エ','オ','カ','キ','ク','ケ','コ','サ',
    'シ','ス','セ','ソ','タ','チ','ツ','テ','ト','ナ','ニ','ヌ','ネ','ノ','ハ','ヒ','フ','ヘ','ホ','マ','ミ','ム','メ','モ','ヤ','ユ','ヨ','ラ','リ','ル','レ',
    'ロ','ワ','ヲ','ン','ッ','ャ','ュ','ョ','◜','◝'
]
assert len(k_charset) == 0x100

k_charset_map = {ch[0]: i for i, ch in enumerate(k_charset) if ch != None}

k_variant_char = '\uFE0F'

k_unicap_chars = ['𝘢','𝘣','𝘤','𝘥','𝘦','𝘧','𝘨','𝘩','𝘪','𝘫','𝘬','𝘭','𝘮','𝘯','𝘰','𝘱','𝘲','𝘳','𝘴','𝘵','𝘶','𝘷','𝘸','𝘹','𝘺','𝘻']

k_charset_map.update((ch, i) for i, ch in enumerate(k_unicap_chars, start=ord('A')))

k_unicap_charset = k_charset[:ord('A')] + k_unicap_chars + k_charset[ord('Z')+1:]
assert len(k_unicap_charset) == 0x100

def to_pico_chars(text):
    result = []
    for ch in text:
        if ord(ch) < 0x80:
            result.append(ch)
        elif ch in k_charset_map:
            result.append(chr(k_charset_map[ch]))
        elif ch == k_variant_char:
            pass
        else:
            raise Exception("invalid char: %s (%s)" % (ch, ord(ch)))
    return "".join(result)

def from_pico_chars(text, unicaps=False):
    charset = k_unicap_charset if unicaps else k_charset
    return "".join(charset[ord(ch)] for ch in text)

k_version_tuples = {
    29: (0,2,1,0),
    30: (0,2,2,0),
    31: (0,2,2,1),
    32: (0,2,2,2),
    33: (0,2,3,0),
    34: (0,2,4,0),
    35: (0,2,4,1),
    36: (0,2,4,2),
    37: (0,2,5,0),
    38: (0,2,5,2),
    39: (0,2,5,4),
    40: (0,2,5,5),
    41: (0,2,5,6),
}

k_default_version_id = maybe_int(os.getenv("PICO8_VERSION_ID"), 38) # TODO - update as newer versions get more common
k_default_platform = os.getenv("PICO8_PLATFORM_CHAR", 'w' if os.name == 'nt' else 'x' if sys.platform == 'darwin' else 'l')

def get_version_tuple(id):
    version = k_version_tuples.get(id)
    if version is None:
        if id >= 29:
            eprint("warning - unknown version id %d, outputting wrong version number (should be benign)" % id)
            version = k_version_tuples.get(k_default_version_id, (0,0,0,0)) # better than nothing?
        elif id >= 19:
            version = (0,2,0,0)
        elif id >= 8:
            version = (0,1,5+id,0) # 13 .. 23
        else:
            version = (0,0,0,0)
    return version
