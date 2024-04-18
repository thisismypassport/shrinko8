from utils import *
from sdl2_utils import Color

class Memory(bytearray):
    """A block pico8 memory - a bytearray with some convenience functions like get/set16, get/set4, etc."""

    def copy(m):
        return Memory(m)

    def replace(m, src):
        m[:] = src
    
    def clear(m):
        m.fill8(0, 0, len(m))

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
    
    def copyfrom8(m, addr, size, src_memory):
        m.copy8(addr, addr, size, src_memory)
        
    def fill8(m, dest, value, size):
        m.set_block(dest, bytearray((value,)) * size)
        
    def cmpeq8(m, src1, src2, size, other_memory = None):
        return m.get_block(src1, size) == (other_memory or m).get_block(src2, size)
    
    def cmpeqwith8(m, src, size, other_memory = None):
        return m.cmpeq8(src, src, size, other_memory)
        
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

k_mem_sprites_addr = 0
k_mem_map_addr = 0x2000
k_mem_flag_addr = 0x3000
k_mem_music_addr = 0x3100
k_mem_sfx_addr = 0x3200

def mem_sprite_addr(x, y):
    """Convert an (x,y) coord to a sprite address, for use with Memory.get/set4"""
    return k_mem_sprites_addr + y * 0x40 + (x >> 1), (x & 1)
    
def mem_map_addr(x, y):
    """Convert an (x,y) coord to a map address"""
    if y >= 0x20: y -= 0x40  # in effect
    return k_mem_map_addr + y * 0x80 + x

def mem_flag_addr(tile, y=0):
    """Convert a tile number to the sprite's flags address"""
    return k_mem_flag_addr + y * 0x80 + tile

def mem_music_addr(music, ch):
    """Returns the address of the given channel of the given music"""
    return k_mem_music_addr + music * 0x4 + ch
    
def mem_sfx_addr(sound, note):
    """Return the address of the given note of the given sfx"""
    return 0x3200 + sound * 0x44 + note * 0x2
    
def mem_sfx_info_addr(sound, i):
    """Return the address of the i-th info byte of the given sfx"""
    return mem_sfx_addr(sound, 0x20) + i

def mem_create_rom():
    rom = Memory(k_rom_size)
    for i in range(0x40):
        rom.set8(mem_sfx_info_addr(i, 1), 0x1 if i == 0 else 0x10)
        for ch in range(4):
            rom.set8(mem_music_addr(i, ch), 0x41 + ch)
    return rom

k_rom_size = 0x4300 # size of the part of the pico8 cart that gets copied to the pico8 Memory
k_cart_size = 0x8000 # size of the entire pico8 cart
k_code_size = k_cart_size - k_rom_size # size of the code in a pico8 cart
k_trailer_size = 0x20 # size of the pico8 cart trailer in png format
k_url_size = 2040 # max. size of a pico8 url
k_url_prefix_size = 4

# the pico8 palette
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

 # the pico8 character set
k_charset = [
    None, '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '\t', '\n', 'ᵇ', 'ᶜ', '\r', 'ᵉ', 'ᶠ',
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

# maps unicode character to pico8 char index
k_charset_map = {ch[0]: i for i, ch in enumerate(k_charset) if ch != None}

k_variant_char = '\uFE0F'

k_unicap_chars = ['𝘢','𝘣','𝘤','𝘥','𝘦','𝘧','𝘨','𝘩','𝘪','𝘫','𝘬','𝘭','𝘮','𝘯','𝘰','𝘱','𝘲','𝘳','𝘴','𝘵','𝘶','𝘷','𝘸','𝘹','𝘺','𝘻']

k_charset_map.update((ch, i) for i, ch in enumerate(k_unicap_chars, start=ord('A')))

# a variant of the pico8 character set that uses unicode italics for capital characters (used by pico8 for copy/paste)
k_unicap_charset = k_charset[:ord('A')] + k_unicap_chars + k_charset[ord('Z')+1:]
assert len(k_unicap_charset) == 0x100

# p8str - a string where each character is between '\0' and '\xff' and represents
# the corresponding pico8 character. 
# (in the future, this might become a real type. Now, it's just an agreement on how str is used)

def to_p8str(text):
    """Convert a unicode string to a pico8 string"""
    result = []
    for ch in text:
        if ord(ch) < 0x80:
            result.append(ch)
        elif ch in k_charset_map:
            result.append(chr(k_charset_map[ch]))
        elif ch == k_variant_char:
            pass
        else:
            throw(f"invalid char: {ch} ({ord(ch)})")
    return "".join(result)

def from_p8str(text, unicaps=False):
    """Convert a pico8 string to a unicode string. unicaps determines whether to use unicode italics for capital letters"""
    charset = k_unicap_charset if unicaps else k_charset
    return "".join(charset[ord(ch)] for ch in text)

def encode_p8str(text):
    """Encode a pico8 string into bytes"""
    return bytes(ord(ch) for ch in text)

def decode_p8str(bytes):
    """Decodes bytes into a pico8 string"""
    return "".join(chr(b) for b in bytes)

to_pico_chars = to_p8str # legacy name
from_pico_chars = from_p8str # legacy name

# fixnum - an integer representing a 16.16 pico8 fixed-point number
# e.g. 
# This may become a class in the future, but is a convention now.

k_fixnum_mask = 0xffffffff

def num_to_fixnum(value):
    """convert a python int or real to a fixnum"""
    return int(value * (1 << 16)) & k_fixnum_mask

def fixnum_is_negative(value):
    """Return whether the fixnum is negative"""
    return bool(value & 0x80000000)

def fixnum_to_num(value):
    """convert a fixnum to a python int or real"""
    neg = fixnum_is_negative(value)
    if neg:
        value = (-value) & k_fixnum_mask
    if value & 0xffff:
        value /= (1 << 16)
    else:
        value >>= 16 # preserve int-ness
    return -value if neg else value

# pico-8 versions

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
    42: (0,2,6,1),
}

def get_default_version_id():
    version_id = 42 # TODO - update as newer versions get more common
    return maybe_int(os.getenv("PICO8_VERSION_ID"), version_id)

def get_default_platform():
    # there's also 'E' for either Emscripten or Education
    platform = 'w' if os.name == 'nt' else 'x' if sys.platform == 'darwin' else 'l'
    return os.getenv("PICO8_PLATFORM_CHAR", platform)

def get_version_tuple(id):
    """Maps a pico8 version id to a tuple representing the actual version (e.g. (0,2,4,1) is v0.2.4b)"""
    version = k_version_tuples.get(id)
    if version is None:
        if id >= 29:
            eprint(f"warning - unknown version id {id}, outputting wrong version number (should be benign)")
            version = k_version_tuples.get(get_default_version_id(), (0,0,0,0)) # better than nothing?
        elif id >= 19:
            version = (0,2,0,0)
        elif id >= 8:
            version = (0,1,5+id,0) # 13 .. 23
        else:
            version = (0,0,0,0)
    return version
