from utils import *
from pico_defs import Language, encode_luastr, decode_luastr
from pico_export import lz4_compress, lz4_uncompress
from pico_compress import update_mtf

# (note - picotron pods have nothing to do with pico8 pods)

k_pod = b"pod"
k_pod_str = k_pod.decode()
k_pod_prefix_str = k_pod_str + ","
k_pod_format = b"pod_format"
k_pod_prefix_strs = (k_pod_format.decode(), "pod_type")
k_pod_raw_format = k_pod_format + b"=\"raw\""
k_meta_prefix = b"--[["
k_meta_pod_prefix = k_meta_prefix + k_pod
k_meta_pod_raw_prefix = k_meta_prefix + k_pod_raw_format
k_meta_suffix = b"]]"

class UserData(Tuple):
    """Represents a picotron userdata"""
    type = width = height = data = ...

def parse_pod(pod, ud_handler=None):
    """Parses a picotron pod from a readable string"""
    src = Source("<pod>", pod)
    tokens, token_errors = tokenize(src, lang=Language.picotron)
    if tokens:
        root, parse_errors = parse(src, tokens, lang=Language.picotron, for_expr=True)
    else:
        root, parse_errors = None, []
    
    value_errors = []
    def add_error(msg, node):
        value_errors.append(Error(msg, node))

    def node_to_value(node):
        if node.type == NodeType.const:
            if node.token.type in (TokenType.number, TokenType.string):
                return node.token.parsed_value
            elif node.token.value == "false":
                return False
            elif node.token.value == "true":
                return True
            else:
                return None
        elif node.type == NodeType.unary_op and node.op == "-" and node.child.type == NodeType.const and node.child.token.type == TokenType.number:
            return -node.child.token.parsed_value

        elif node.type == NodeType.call and node.func.type == NodeType.var and node.func.name == "userdata":
            ud_args = tuple(node_to_value(arg) for arg in node.args)

            if len(ud_args) in (3, 4):
                type, width, data = ud_args[0], ud_args[1], ud_args[-1]
                height = ud_args[2] if len(ud_args) == 4 else 0
                if isinstance(type, str) and isinstance(width, int) and isinstance(height, int) and isinstance(data, str):
                    return UserData(type, width, height, data)

            if len(ud_args) == 0 and ud_handler and (userdata := ud_handler()):
                return userdata

            add_error(f"unknown userdata params: {ud_args}")

        elif node.type == NodeType.table:
            table = {}
            index = 1
            for item in node.items:
                if item.type == NodeType.table_index:
                    key, value = node_to_value(item.key), node_to_value(item.value)
                    if e(key) and e(value):
                        table[key] = value
                elif item.type == NodeType.table_member:
                    value = node_to_value(item.value)
                    if e(value):
                        table[item.key.name] = value
                else:
                    value = node_to_value(item)
                    if e(value):
                        table[index] = value
                    index += 1
            return table
        else:
            add_error(f"unknown pod syntax {node.type}", node)

    value = node_to_value(root) if root else None

    if token_errors or parse_errors or value_errors:
        eprint(f"warning - errors while parsing pod: {pod}")
        for error in token_errors + parse_errors + value_errors:
            eprint("  " + error.format())
    return value

def parse_meta_pod(pod):
    """Parses a picotron pod as it appears in a file's metadata"""
    if pod == k_pod_str:
        return {}

    pod = str_remove_prefix(pod, k_pod_prefix_str)
    return parse_pod("{" + pod + "}")

def format_pod(value, ud_handler=None):
    """Formats a picotron pod into a readable string"""
    if value is None:
        return "nil"
    elif value is False:
        return "false"
    elif value is True:
        return "true"
    elif isinstance(value, (int, float)):
        return format_luanum(value, base=10)
    elif isinstance(value, str):
        return format_string_literal(value, long=False, quote='"')

    elif isinstance(value, UserData):
        type, width, height, data = format_pod(value.type), format_pod(value.width), format_pod(value.height), format_pod(value.data)
        if value.height:
            result = f"userdata({type},{width},{height},{data})"
        else:
            result = f"userdata({type},{width},{data})"
        
        if ud_handler and ud_handler(value, result):
            result = "\0" # to allow unambiguously finding it in the result
        return result

    elif isinstance(value, dict):
        index = 1
        parts = []
        for key, child in value.items():
            if key == index:
                parts.append(format_pod(child, ud_handler))
                index += 1
            elif isinstance(key, str) and is_identifier(key, Language.picotron):
                parts.append(f"{key}={format_pod(child, ud_handler)}")
            else:
                parts.append(f"[{format_pod(key, ud_handler)}]={format_pod(child, ud_handler)}")
        return "{" + ",".join(parts) + "}"
    else:
        throw(f"invalid pod value {value}")

def escape_meta(pod):
    i = 0
    while True:
        i = pod.find("]]", i)
        if i < 0:
            break
        repl = "\\93\\093" if str_get(pod, i+2, "").isdigit() else "\\93\\93"
        pod = str_replace_at(pod, i, 2, repl)
    return pod

def format_meta_pod(value):
    """Formats a picotron pod as it should appear in a file's metadata"""
    for pod_prefix_str in k_pod_prefix_strs:
        if pod_prefix_str in value: # put it first
            prefix = f"{pod_prefix_str}={format_pod(value[pod_prefix_str])}"
            value = value.copy()
            del value[pod_prefix_str]
            break
    else:
        prefix = k_pod_str
    
    rest = format_pod(value)[1:-1]
    return escape_meta(f"{prefix},{rest}" if rest else prefix)

k_lz4_prefix = b"lz4\0"
k_pxu_prefix = b"pxu\0"

class PxuFlags(Bitmask):
    unk_type = 0x3
    has_height = 0x40
    long_size = 0x800
    compress = 0x2000

def read_pxu(data, idx):
    """Reads the picotron userdata compression format 'pxu' into a UserData."""

    with BinaryReader(BytesIO(data)) as r:
        r.setpos(idx)
        check(r.bytes(4) == k_pxu_prefix, "wrong pxu header")
        flags = PxuFlags(r.u16())
        if not flags.compress or flags.unk_type != 3:
            throw(f"unsupported pxu flags: {flags}")

        width = r.u32() if flags.long_size else r.u8()
        height = (r.u32() if flags.long_size else r.u8()) if flags.has_height else 1
        size = width * height

        bits = r.u8()
        check(bits == 4, "unsupported pxu bits") # TODO - allow more?
        mask = (1 << bits) - 1
        ext_count = 1 << (8 - bits)

        # the general idea behind the complexity is that repeated pixels can
        # take up spots from low-valued pixels.

        data = bytearray()
        mapping = [i for i in range(mask)]
        mtf = [i for i in range(mask)]

        while len(data) < size:
            b = r.u8()
            
            index = b & mask
            if index == mask:
                value = r.u8()
                mapping[mtf[-1]] = value
            
            else:
                update_mtf(mtf, mtf.index(index), index)
                value = mapping[index]
            
            count = 1 + (b >> bits)
            if count == ext_count:
                while True:
                    c = r.u8()
                    count += c
                    if c != 0xff:
                        break
            
            for i in range(count):
                data.append(value)

        hexdata = "".join(f"{b:02x}" for b in data)
        return UserData("u8", width, height if flags.has_height else 0, hexdata), r.pos()

def read_pod(value):
    """Reads a picotron pod from possibly compressed bytes"""

    if value.startswith(k_lz4_prefix):
        with BinaryReader(BytesIO(value)) as r:
            r.addpos(4)
            size = r.u32()
            _unc_size = r.u32()
            value = lz4_uncompress(r.bytes(size))

    pxu_i = 0
    userdatas = None
    while True:
        pxu_i = value.find(k_pxu_prefix, pxu_i)
        if pxu_i < 0:
            break
        
        userdatas = userdatas or deque()
        userdata, end_i = read_pxu(value, pxu_i)
        value = str_replace_between(value, pxu_i, end_i, b"userdata()")
        userdatas.append(userdata)

    def handle_userdata():
        if userdatas:
            return userdatas.popleft()

    return parse_pod(decode_luastr(value), handle_userdata)

def write_pxu(ud):
    """Writes userdata via the picotron userdata compression format 'pxu'"""
    if ud.type != "u8":
        return None
    
    with BinaryWriter() as w:
        flags = PxuFlags.unk_type | PxuFlags.compress
        if ud.height:
            flags |= PxuFlags.has_height
        if ud.width >= 0x100 or ud.height >= 0x100:
            flags |= PxuFlags.long_size

        w.bytes(k_pxu_prefix)
        w.u16(int(flags))
        (w.u32 if flags.long_size else w.u8)(ud.width)
        if flags.has_height:
            (w.u32 if flags.long_size else w.u8)(ud.height)
        
        data = bytearray()
        try:
            for i in range(0, len(ud.data), 2):
                data.append(int(ud.data[i:i+2], 16))
        except ValueError:
            throw("invalid userdata encountered")

        bits = 4 # could try other values, but picotron itself never does?
        w.u8(bits)
        mask = (1 << bits) - 1
        ext_count = 1 << (8 - bits)
        
        mapping = [i for i in range(mask)]
        mtf = [i for i in range(mask)]

        i = 0
        while i < len(data):
            count = 1
            value = data[i]
            i += 1
            while i < len(data) and data[i] == value:
                count += 1
                i += 1

            index = list_find(mapping, value)
            if index < 0:
                index = mask
                mapping[mtf[-1]] = value

            else:
                update_mtf(mtf, mtf.index(index), index)
            
            w.u8(index | ((min(count, ext_count) - 1) << bits))
            if index == mask:
                w.u8(value)
            
            if count >= ext_count:
                count -= ext_count
                while count >= 0xff:
                    w.u8(0xff)
                    count -= 0xff
                w.u8(count)

        return w.f.getvalue()

def write_pod(pod, compress=True, use_pxu=True):
    """Writes a picotron pod into optionally compressed bytes"""
    
    pxu_datas = None
    def handle_userdata(ud, str_data):
        nonlocal pxu_datas
        if use_pxu:
            pxu_data = write_pxu(ud)
            if pxu_data and len(pxu_data) < len(str_data):
                pxu_datas = pxu_datas or deque()
                pxu_datas.append(pxu_data)
                return True

    value = encode_luastr(format_pod(pod, handle_userdata))

    pxu_i = 0
    while pxu_datas:
        pxu_i = value.find(0, pxu_i)
        assert pxu_i >= 0

        pxu_data = pxu_datas.popleft()
        value = str_replace_at(value, pxu_i, 1, pxu_data)
        pxu_i += len(pxu_data)

    if compress:
        with BinaryWriter() as w:
            compressed = lz4_compress(value)
            w.bytes(k_lz4_prefix)
            w.u32(len(compressed))
            w.u32(len(value))
            w.bytes(compressed)
            value = w.f.getvalue()
    
    return value

class PicotronFile:
    """A picotron file or directory in its filesystem - files contain metadata & payload"""

    def __init__(m, data, line=0):
        m.data = data
        m.line = line
    
    @property
    def is_raw(m):
        return e(m.data) and (not m.data.startswith(k_meta_pod_prefix) or m.data.startswith(k_meta_pod_raw_prefix))

    @property
    def raw_metadata(m):
        if m.data is None or not m.data.startswith(k_meta_pod_prefix):
            return None
        end_i = m.data.find(k_meta_suffix)
        if end_i < 0:
            end_i = len(m.data)
        return m.data[len(k_meta_prefix):end_i]

    @raw_metadata.setter
    def raw_metadata(m, value):
        assert not m.is_dir
        if value is None:
            m.data = m.raw_payload
        else:
            m.data = k_meta_prefix + value + k_meta_suffix + m.raw_payload

    @property
    def metadata(m):
        metadata = m.raw_metadata
        if metadata != None:
            metadata = parse_meta_pod(decode_luastr(metadata))
        return metadata

    @metadata.setter
    def metadata(m, value):
        if value is None:
            m.raw_metadata = None
        else:
            assert isinstance(value, dict)
            m.raw_metadata = encode_luastr(format_meta_pod(value))

    @property
    def raw_payload(m):
        if m.data is None:
            return None
        if not m.data.startswith(k_meta_pod_prefix):
            return m.data
        end_i = m.data.find(k_meta_suffix)
        if end_i < 0:
            return b""
        return m.data[end_i + len(k_meta_suffix):]

    @raw_payload.setter
    def raw_payload(m, value):
        assert not m.is_dir
        metadata = m.raw_metadata
        if e(metadata):
            m.data = k_meta_prefix + metadata + k_meta_suffix + value
        else:
            m.data = value

    @property
    def payload(m):
        if m.is_raw:
            return m.raw_payload
        else:
            return read_pod(m.raw_payload)
    
    @payload.setter
    def payload(m, value):
        m.set_payload(value)

    def set_payload(m, value, compress=True, use_pxu=True):
        if m.is_raw:
            m.raw_payload = value
        else:
            m.raw_payload = write_pod(value, compress=compress, use_pxu=use_pxu)

    is_dir = False

class PicotronDir(PicotronFile):
    def __init__(m):
        super().__init__(None)
    
    is_dir = True

from pico_tokenize import tokenize, TokenType, is_identifier
from pico_parse import parse, NodeType
from pico_output import format_luanum, format_string_literal
from pico_process import Source, Error
