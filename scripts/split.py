from utils import *
from pico_process import SubLanguageBase
from pico_parse import VarKind
from pico_tokenize import parse_char_escape

@lru_cache
def parse_split_args(args, lang):
    """args is e.g. 'member=string' or '(global.members)=string'
       return value is (separator, split parts, plural begin idx, plural end idx)"""
    idx = 0

    def peek_char():
        return str_get(args, idx, "\0")

    def take_char():
        nonlocal idx
        ch = peek_char()
        idx += 1
        return ch

    def parse_rec(depth):
        nonlocal idx
        start = idx
        split = []
        sep = None
        sep_expected = False
        plural_begin = plural_end = None
        while True:
            ch = take_char()
            if ch == "\0":
                if depth:
                    throw("unexpected end of arguments (unbalanced '('?)")
                break
            elif ch == ")":
                if not depth:
                    throw("unbalanced ')'")
                break
            elif ch == "(":
                if sep_expected:
                    throw(f"missing separator before '('")
                split.append(parse_rec(depth + 1))
                sep_expected = True
            elif ch.isalpha():
                word = ch
                while peek_char().isalpha():
                    word += take_char()

                is_plural = False
                singular = word
                if word.endswith("s"):
                    is_plural = True
                    singular = word[:-1]

                if singular == "member":
                    split.append(VarKind.member)
                elif singular == "global":
                    split.append(VarKind.global_)
                elif singular == "string" or singular == "preserve":
                    split.append(None)
                elif singular == "": # just "s", e.g. after parentheses
                    if not split or not isinstance(split[-1], tuple):
                        throw(f"missing parentheses before {word}")
                else:
                    throw(f"invalid variable type: {word} (use member/global/string, optionally plural)")
                
                if is_plural:
                    if plural_begin is None:
                        plural_begin = len(split) - 1
                        plural_end = plural_begin + 1
                    elif plural_end == len(split) - 1:
                        plural_end += 1
                    else:
                        throw(f"multiple plural variable types must be consecutive")

                if sep_expected and singular != "":
                    throw(f"missing separator before {word}")
                sep_expected = True
            else:
                if ch == "\\":
                    if (ch := str_get(args, idx, "")) in "()":
                        idx += 1
                    elif ch == "w":
                        ch = str_get(args, idx + 1, "")
                        idx += 2
                    else:
                        ch, idx = parse_char_escape(args, idx - 1, lang)
                
                if sep is None:
                    sep = ch
                elif sep != ch:
                    throw(f"parentheses must be used to clarify order of splitting by {sep} and {ch}")
                    
                if not sep_expected:
                    throw(f"expected variable type before separator {ch}")
                sep_expected = False
        
        if sep is None:
            throw(f"no separator specified for: {args[start:idx]} - you can add a separator at the end")

        return (sep, split, plural_begin, plural_end)
    
    return parse_rec(0)

class SplitSubLang(SubLanguageBase):
    """Implements a simple split()-based language, where the interpretation of each split part
    is customizable via the language args"""

    def __init__(m, text, args, ctxt, on_error, **_):
        try:
            template = parse_split_args(args, ctxt.lang)
        except CheckError as e:
            on_error(str(e))
            return

        m.data = m.parse(text, template)
    
    def repeat_partial(m, slice, count):
        slice_i = 0
        result = []
        for i in range(count):
            result.append(slice[slice_i])
            slice_i += 1
            if slice_i == len(slice):
                slice_i = 0
        return result

    def get_types_of_len(m, parts, types, plural_begin, plural_end):
        """get 'types' with the size of 'parts', expanding/shrinking per plural_begin/end as needed"""

        if len(parts) != len(types):
            if plural_begin is None:
                if len(types) < len(parts):
                    types += [None] * (len(parts) - len(types))
            else:
                repeat_len = len(parts) - len(types) + plural_end - plural_begin
                repeat = m.repeat_partial(types[plural_begin:plural_end], repeat_len)
                types = types[:plural_begin] + repeat + types[plural_end:]
            
            if len(types) > len(parts):
                types = types[:len(parts)]
        
        return types
        
    def parse(m, str, template):
        """parses 'str', according to 'template'"""

        sep, types, plural_begin, plural_end = template
        parts = str.split(sep)
        types = m.get_types_of_len(parts, types, plural_begin, plural_end)

        for i, type in enumerate(types):
            if isinstance(type, tuple):
                parts[i] = m.parse(parts[i], type)
        
        return (sep, parts, types)

    def collect_usages_of(m, data, kind, usages):
        _, parts, types = data
        for part, type in zip(parts, types):
            if isinstance(type, tuple):
                m.collect_usages_of(part, kind, usages)
            elif type == kind:
                usages[part] += 1

    def get_usages_of(m, kind):
        usages = CounterDictionary()
        m.collect_usages_of(m.data, kind, usages)
        return usages

    def get_global_usages(m, **_):
        return m.get_usages_of(VarKind.global_)
    def get_member_usages(m, **_):
        return m.get_usages_of(VarKind.member)

    def rename_of(m, data, globals, members):
        _, parts, types = data
        for i, (part, type) in enumerate(zip(parts, types)):
            if isinstance(type, tuple):
                m.rename_of(part, globals, members)
            elif type == VarKind.global_:
                parts[i] = globals.get(parts[i], parts[i])
            elif type == VarKind.member:
                parts[i] = members.get(parts[i], parts[i])

    def rename(m, globals, members, **_):
        m.rename_of(m.data, globals, members)

    def format(m, data):
        sep, parts, _ = data
        return sep.join((m.format(part) if isinstance(part, tuple) else part) for part in parts)
    
    def minify(m, **_):
        return m.format(m.data)

def sublanguage_main(lang, **_):
    if lang == "split":
        return SplitSubLang
