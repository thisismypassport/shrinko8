from utils import *
from pico_defs import Language, encode_luastr, decode_luastr

k_pod = b"pod"
k_pod_prefix = k_pod + b","
k_pod_format = b"pod_format"
k_pod_raw_format = k_pod_format + b"=\"raw\""
k_meta_prefix = b"--[["
k_meta_pod_prefix = k_meta_prefix + k_pod
k_meta_pod_raw_prefix = k_meta_prefix + k_pod_raw_format
k_meta_suffix = b"]]"

class UserData(Struct):
    type = width = height = data = ...

def parse_pod(pod):
    src = Source("<pod>", pod)
    tokens, token_errors = tokenize(src, lang=Language.picotron)
    root, parse_errors = parse(src, tokens, lang=Language.picotron, for_expr=True)
    
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
        elif node.type == NodeType.call and node.func.type == NodeType.var and node.func.name == "userdata" and len(node.args) in (3, 4):
            type = node_to_value(node.args[0])
            width = node_to_value(node.args[1])
            height = node_to_value(node.args[2]) if len(node.args) == 4 else 0
            data = node_to_value(node.args[-1])
            if isinstance(type, str) and isinstance(width, int) and isinstance(height, int) and isinstance(data, str):
                return UserData(type, width, height, data)
            else:
                add_error(f"unknown userdata params: {type}, {width}, {height}, {data}")
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

def escape_meta(pod):
    i = 0
    while True:
        i = pod.find("]]", i)
        if i < 0:
            break
        repl = "\\93\\093" if str_get(pod, i+2, "").isdigit() else "\\93\\93"
        pod = str_replace_at(pod, i, 2, repl)
    return pod

def format_pod(value, meta=False):
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
        # TODO: pxu (though not usable in meta, anyway)
        type, width, height, data = format_pod(value.type), format_pod(value.width), format_pod(value.height), format_pod(value.data)
        if value.height:
            return f"userdata({type},{width},{height},{data})"
        else:
            return f"userdata({type},{width},{data})"
    elif isinstance(value, dict):
        index = 1
        parts = []
        
        if meta and k_pod_format in value: # put it first
            parts.append(f"{k_pod_format}={format_pod(value[k_pod_format])}")
            value = value.copy()
            del value[k_pod_format]

        for key, child in value:
            if key == index:
                parts.append(format_pod(child))
                index += 1
            elif is_identifier(key, Language.picotron):
                parts.append(f"{key}={format_pod(child)}")
            else:
                parts.append(f"[{format_pod(key)}]={format_pod(child)}")
        return "{" + ",".join(parts) + "}"
    else:
        throw(f"invalid pod value {value}")

class PicotronFile:
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
            metadata = "{" + decode_luastr(str_remove_prefix(metadata, k_pod_prefix)) + "}"
            metadata = parse_pod(metadata)
        return metadata

    @metadata.setter
    def metadata(m, value):
        if value is None:
            m.raw_metadata = None
        else:
            check(isinstance(value, dict))
            m.raw_metadata = encode_luastr(escape_meta(format_pod(value, meta=True))[1:-1])

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

    is_dir = False

class PicotronDir(PicotronFile):
    def __init__(m):
        super().__init__(None)
    
    is_dir = True

from pico_tokenize import tokenize, TokenType, is_identifier
from pico_parse import parse, NodeType
from pico_output import format_luanum, format_string_literal
from pico_process import Source, Error
