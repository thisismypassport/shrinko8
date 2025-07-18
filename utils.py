import os, sys, io, bisect, random, copy, collections, itertools, struct, array, re, traceback, hashlib, math, string, weakref, operator, heapq, time, json, tempfile
from datetime import datetime, timedelta, timezone
from functools import reduce, total_ordering, lru_cache, cmp_to_key
from copy import copy, deepcopy
from io import BytesIO, StringIO
from warnings import warn
from reprlib import recursive_repr

def _my_excepthook(type, value, tb):
    obj = traceback.TracebackException(type, value, tb)
    for hook in _my_excepthook.hooks:
        hook(obj)
        
    for line in obj.format():
        print(line, file=sys.stderr, end="")    
        
def add_traceback_hook(hook):
    """adds a hook to be called before printing a traceback, so that the hook can edit it freely"""
    _my_excepthook.hooks.append(hook)

_my_excepthook.hooks = []
sys.excepthook = _my_excepthook

def eprint(*args, **kwargs):
    """like print, but prints to stderr"""
    print(*args, file=sys.stderr, **kwargs)

def context_manager(method_name = "close"):
    """Adds __enter__/__exit__ support for a class, using a specified method_name as the 'close' method"""
    
    def decorator(cls):
        method = getattr(cls, method_name)
        
        def __enter__(m):
            return m
        def __exit__(m, t, v, s):
            method(m)
        
        cls.__enter__ = __enter__
        cls.__exit__ = __exit__
        return cls
    return decorator

def exec_def(name, code):
    """execute 'code' and extract a definition named 'name' from it"""
    namespace = {}
    exec(code, namespace)
    return namespace[name]

def exec_script_by_path(path, name=None):
    """executes script at 'path', returning its module object"""
    import importlib.util
    script_spec = importlib.util.spec_from_file_location(default(name, path_basename_no_extension(path)), path_absolute(path))
    script_mod = importlib.util.module_from_spec(script_spec)
    script_spec.loader.exec_module(script_mod)
    return script_mod

def import_from_script_by_path(path, *func_names):
    """executes script at 'path', importing the requested funcs from it - if they exist"""
    script_mod = exec_script_by_path(path)
    return tuple(getattr(script_mod, name, None) for name in func_names)

def typename(obj):
    """returns the name of the object's type"""
    return type(obj).__name__

class Dynamic(object):
    """An anonymous dynamic class with keyword-args-style initialization"""
    
    def __init__(__m_, **__kw_):
        __m_.__dict__ = __kw_

    @recursive_repr()
    def __repr__(m):
        contents = ", ".join(f"{k}={repr(v)}" for k, v in m.__dict__.items())
        return f"{typename(m)}({contents})"

class DefaultDynamic(Dynamic):
    """Like Dynamic, but accessing an unknown key gives None"""
    
    def __getattr__(m, name):
        return None

def isdescriptor(obj):
    """Return whether the value is a descriptor"""
    return hasattr(obj, "__get__") or hasattr(obj, "__set__") or hasattr(obj, "__del__")

class IncludeAttr:
    """When defining an Enum/Tuple/etc, forces the attribute to be included, despite having a private name or being a function/descriptor/..."""
    def __init__(m, value):
        m.value = value

class NoRenameAttr(IncludeAttr):
    """When defining an Enum/Tuple/etc, forces the attribute to be included and not be renamed, despite having a name ending in _"""
    def __init__(m, value):
        m.value = value

class ExcludeAttr:
    """When defining an Enum/Tuple/etc, forces the attribute to be excluded, despite not having a private name nad not being a function/descriptor/..."""
    def __init__(m, value):
        m.value = value

def _metaclass_collect_values(cls_dict, values, prefirst, next, with_aliases=True):
    prev_value = prefirst
    for key, value in default(values, cls_dict).items():
        keep_key = False
        if key.startswith("__") and key.endswith("__"):
            continue
        elif isinstance(value, IncludeAttr):
            keep_key = isinstance(value, NoRenameAttr)
            value = value.value
        elif key.startswith("_") or callable(value) or isdescriptor(value) or isinstance(value, ExcludeAttr):
            continue
        elif value is ...:
            value = next(prev_value)
        prev_value = value

        yield key, value
        if key.endswith("_") and not keep_key:
            yield key[:-1], value # yield "proper" name last, so it overrides the '_' name in reverse maps

def _metaclass_collect_fields(cls_dict, values):
    fields = []
    defaults = []
    no_default = defaults # marker value, compare via 'is'

    def next_no_default(_):
        return no_default

    for k, v in _metaclass_collect_values(cls_dict, values, None, next_no_default, with_aliases=False):
        fields.append(k)
        if v is not no_default:
            defaults.append(v)
        elif defaults:
            raise Exception(f"Cannot specify required field {k} after optional fields")
    
    return tuple(fields), tuple(defaults)

class EnumMetaclass(type):
    def __new__(meta, cls_name, cls_bases, cls_dict, values=None):
        if not cls_bases or Enum not in cls_bases:
            return super().__new__(meta, cls_name, cls_bases, cls_dict)
        
        # collect
        enum_bases = tuple(base for base in cls_bases if base is not Enum and base.__class__ == EnumMetaclass)
        
        def next_auto(prev):
            if enum_bases:
                raise Exception("Enum with bases must use explicit values") # TODO
            if not isinstance(prev, (int, float)):
                raise Exception(f"Cannot follow {prev} with ...")
            return prev + 1

        name_value_map = dict(_metaclass_collect_values(cls_dict, values, 0, next_auto))
                
        full_name_value_map = name_value_map.copy() if enum_bases else name_value_map
        for base in enum_bases:
            full_name_value_map.update(base._values)
            
        full_value_name_map = {v:k for k,v in full_name_value_map.items()}
        
        # dict
        def __init__(m, value):
            if value in full_value_name_map:
                m.value = value
            elif value in full_name_value_map:
                m.value = full_name_value_map[value]
            else:
                raise ValueError(f"{value} not value of {cls_name}")
    
        def __eq__(m, other):
            if m.__class__ != other.__class__:
                return NotImplemented
            return m.value == other.value
            
        def __lt__(m, other):
            if not isinstance(m, other.__class__) and not isinstance(other, m.__class__):
                return NotImplemented
            return m.value < other.value
    
        def __str__(m):
            return full_value_name_map[m.value]
    
        def __repr__(m):
            return f"{cls_name}.{full_value_name_map[m.value]}"
    
        def __int__(m):
            return m.value
    
        def __hash__(m):
            return hash(m.value)
    
        enum_dict = {}
        enum_dict["__init__"] = __init__
        enum_dict["__eq__"] = __eq__
        enum_dict["__lt__"] = __lt__
        enum_dict["__str__"] = __str__
        enum_dict["__repr__"] = __repr__
        enum_dict["__int__"] = __int__
        enum_dict["__hash__"] = __hash__
        enum_dict["__slots__"] = ("value",)
        enum_dict["_values"] = full_name_value_map
        
        for k, v in cls_dict.items():
            if isinstance(v, ExcludeAttr):
                v = v.value
            
            if k in name_value_map:
                continue
            elif k == "__slots__":
                enum_dict[k] = enum_dict[k] + (v if isinstance(v, tuple) else (v,))
            elif k in enum_dict:
                raise Exception(f"Cannot set {k} in Enum (but can override in inherited classes)")
            else:
                enum_dict[k] = v
                
        enum_class = super().__new__(meta, cls_name, cls_bases, enum_dict)
    
        for k, v in name_value_map.items():
            setattr(enum_class, k, enum_class(v))
    
        enum_class = total_ordering(enum_class)
        return enum_class

class Enum(metaclass=EnumMetaclass):
    """If a class has Enum as a baseclass, it's transformed into an enum.
    All non-private attributes of the class other than functions and descriptors become enum members.
    Atributes with a value of ... receive values automatically.
    Inherited classes behave like regular classes unless they have Enum as a direct baseclass.
    Advanced: ExcludeAttr/IncludeAttr, values keyword parameter
    Atributes with a name ending with _ can be referred to without the _.
    """

class BitmaskMetaclass(type):
    def __new__(meta, cls_name, cls_bases, cls_dict, values=None):
        if not cls_bases or Bitmask not in cls_bases:
            return super().__new__(meta, cls_name, cls_bases, cls_dict)
        
        # collect
        bitmask_bases = tuple(base for base in cls_bases if base is not Bitmask and base.__class__ == BitmaskMetaclass)
        
        def next_auto(prev):
            if bitmask_bases:
                raise Exception("Bitmasks with bases must use explicit values") # TODO
            if not isinstance(prev, int) or (prev != 0 and not is_pow2(prev)):
                raise Exception(f"Cannot follow {prev} with ...")
            return prev << 1 if prev != 0 else 1

        name_mask_map = dict(_metaclass_collect_values(cls_dict, values, 0, next_auto))
        
        full_name_mask_map = name_mask_map.copy() if bitmask_bases else name_mask_map
        for base in bitmask_bases:
            full_name_mask_map.update(base._fields)
    
        full_mask_name_map = {v:k for k,v in full_name_mask_map.items()}
        full_mask = reduce(lambda x,y:x|y, full_mask_name_map.keys(), 0)
        
        # dict
        def __init__(m, value = None, **kwargs):
            if value is None:
                m.value = 0
            elif isinstance(value, int) and (value & full_mask) == value:
                m.value = value
            elif isinstance(value, str) and value in full_name_mask_map:
                m.value = full_name_mask_map[value]
            elif isinstance(value, m.__class__):
                m.value = value.value
            elif isinstance(value, (tuple, list)):
                m.value = reduce(lambda x,y:x|y, (full_name_mask_map[part] for part in value), 0)
            else:
                raise ValueError(f"{value} not value of {cls_name}")
        
            if kwargs:
                for key, value in kwargs.items():
                    setattr(m, key, value)
    
        def __eq__(m, other):
            if m.__class__ != other.__class__:
                return NotImplemented
            return m.value == other.value
        
        def __hash__(m):
            return hash(m.value)
        
        def __str__(m):
            if m.value:
                values = []
                for mask, name in full_mask_name_map.items():
                    if m.value & mask:
                        values.append(name)
    
                return ",".join(values)
            else:
                return ""
    
        def __repr__(m):
            if m.value:
                values = []
                for mask, name in full_mask_name_map.items():
                    if m.value & mask:
                        values.append(f"{cls_name}.{name}")
    
                return " | ".join(values)
            else:
                return f"{cls_name}(0)"
    
        def __int__(m):
            return m.value
    
        def __bool__(m):
            return m.value != 0
    
        def __and__(m, other):
            if m.__class__ != other.__class__:
                return NotImplemented
            return m.__class__(m.value & other.value)
        
        def __or__(m, other):
            if m.__class__ != other.__class__:
                return NotImplemented
            return m.__class__(m.value | other.value)
        
        def __xor__(m, other):
            if m.__class__ != other.__class__:
                return NotImplemented
            return m.__class__(m.value ^ other.value)
    
        class no_bits_property:
            def __init__(m, mask):
                m.mask = mask
                
            def __get__(m, obj, cls):
                if obj is None:
                    return cls(m.mask)
                else:
                    raise AttributeError()
                
            def __set__(m, obj, value):
                raise AttributeError()
    
        class bit_property:
            def __init__(m, mask):
                m.mask = mask
            
            def __get__(m, obj, cls):
                if obj is None:
                    return cls(m.mask)
                else:
                    return bool(obj.value & m.mask)
    
            def __set__(m, obj, value):
                if value:
                    obj.value |= m.mask
                else:
                    obj.value &= ~m.mask
                    
        class bitfield_property:
            def __init__(m, mask):
                m.mask = mask
                m.shift = count_trailing_zero_bits(mask)
            
            def __get__(m, obj, cls):
                if obj is None:
                    return cls(m.mask)
                else:
                    return (obj.value & m.mask) >> m.shift
    
            def __set__(m, obj, value):
                obj.value = (obj.value & ~m.mask) | ((value << m.shift) & m.mask)
                    
        class typed_bitfield_property:
            def __init__(m, mask, type):
                m.mask, m.type = mask, type
                m.shift = count_trailing_zero_bits(mask)
            
            def __get__(m, obj, cls):
                if obj is None:
                    return cls(m.mask)
                else:
                    return m.type((obj.value & m.mask) >> m.shift)
    
            def __set__(m, obj, value):
                obj.value = (obj.value & ~m.mask) | ((int(value) << m.shift) & m.mask)
                    
        bitmask_dict = {}
        bitmask_dict["__init__"] = __init__
        bitmask_dict["__eq__"] = __eq__
        bitmask_dict["__hash__"] = __hash__
        bitmask_dict["__str__"] = __str__
        bitmask_dict["__repr__"] = __repr__
        bitmask_dict["__int__"] = __int__
        bitmask_dict["__nonzero__"] = __bool__
        bitmask_dict["__bool__"] = __bool__
        bitmask_dict["__and__"] = __and__
        bitmask_dict["__or__"] = __or__
        bitmask_dict["__xor__"] = __xor__
        bitmask_dict["__slots__"] = ("value",)
        bitmask_dict["_fields"] = full_name_mask_map
    
        annots = cls_dict.get("__annotations__", None)

        for name, mask in name_mask_map.items():
            if annots and name in annots:
                bitmask_dict[name] = typed_bitfield_property(mask, annots[name])
            elif mask == 0:
                bitmask_dict[name] = no_bits_property(mask)
            elif is_pow2(mask):
                bitmask_dict[name] = bit_property(mask)
            else:
                bitmask_dict[name] = bitfield_property(mask)
    
        for k, v in cls_dict.items():
            if isinstance(v, ExcludeAttr):
                v = v.value
            
            if k in name_mask_map:
                continue
            elif k == "__slots__":
                bitmask_dict[k] = bitmask_dict[k] + (v if isinstance(v, tuple) else (v,))
            elif k in bitmask_dict:
                raise Exception(f"Cannot set {k} in Bitmask (but can override in inherited classes)")
            else:
                bitmask_dict[k] = v
                
        return super().__new__(meta, cls_name, cls_bases, bitmask_dict)

class Bitmask(metaclass=BitmaskMetaclass):
    """If a class has Bitmask as a baseclass, it's transformed into a bitmask.
    All non-private attributes of the class other than functions and descriptors become bitmask fields.
    Atributes with a value of ... receive bits automatically.
    A bitmask is like a struct, but with its fields mapped into a single bitmask integer.
    Bitmasks can also be manipulated via: & | ^
    Inherited classes behave like regular classes unless they have Bitmask as a direct baseclass.
    Advanced: ExcludeAttr/IncludeAttr, values keyword parameter
    Atributes with a name ending with _ can be referred to without the _.
    """
    
class TupleMetaclass(type):
    def __new__(meta, cls_name, cls_bases, cls_dict, values=None):
        if not cls_bases or cls_bases == (tuple,) or Tuple not in cls_bases:
            return super().__new__(meta, cls_name, cls_bases, cls_dict)
        
        # collect
        tuple_bases = tuple(base for base in cls_bases if base is not Tuple and base.__class__ == TupleMetaclass)
        
        fields, defaults = _metaclass_collect_fields(cls_dict, values)
                
        if tuple_bases:
            if defaults:
                raise Exception("Cannot use defaults with bases")
            all_fields = sum((base._fields for base in tuple_bases), ()) + fields
        else:
            all_fields = fields

        # dict
        all_fields_str = ', '.join(all_fields)
        all_fields_tupstr = all_fields_str + ("," if len(all_fields) == 1 else "")
        new_def = f"def __new__(__cls, {all_fields_str}):\n"
        new_def += f"    return tuple.__new__(__cls, ({all_fields_tupstr}))\n"
        __new__ = exec_def("__new__", new_def)
        __new__.__defaults__ = defaults

        def __reduce_ex__(m, proto):
            return (m.__new__, (m.__class__, *m))
        
        @recursive_repr()
        def __repr__(m):
            contents = ", ".join(f"{f}={repr(getattr(m, f))}" for f in m._fields)
            return f"{cls_name}({contents})"
        
        def _replace(m, **changes):
            return m.__class__(*map(changes.pop, m._fields, m))
    
        tuple_dict = {}
        tuple_dict["__new__"] = __new__
        tuple_dict["__reduce_ex__"] = __reduce_ex__
        tuple_dict["__repr__"] = __repr__
        tuple_dict["__slots__"] = () # fields come from tuple
        tuple_dict["_replace"] = _replace
        tuple_dict["_fields"] = all_fields
        
        start = len(all_fields) - len(fields)
        for i, field in enumerate(fields):
            tuple_dict[field] = property(operator.itemgetter(start + i))
        
        fields_set = set(fields)

        for k, v in cls_dict.items():
            if isinstance(v, ExcludeAttr):
                v = v.value
            
            if k in fields_set:
                continue
            elif k == "__slots__":
                tuple_dict[k] = tuple_dict[k] + (v if isinstance(v, tuple) else (v,))
            elif k in tuple_dict:
                raise Exception(f"Cannot set {k} in Tuple (but can override in inherited classes)")
            else:
                tuple_dict[k] = v
        
        return super().__new__(meta, cls_name, cls_bases, tuple_dict)
    
class Tuple(tuple, metaclass=TupleMetaclass):
    """If a class has Tuple as a baseclass, it's transformed into a named tuple.
    All non-private attributes of the class other than functions and descriptors become tuple fields.
    Atributes with a value of ... are required, otherwise - optional with the given default value.
    The tuple behaves similarly to collections.namedtuple
    Inherited classes behave like regular classes unless they have Tuple as a direct baseclass.
    Advanced: ExcludeAttr/IncludeAttr, values keyword parameter
    Atributes with a name ending with _ can be referred to without the _.
    """
        
class StructMetaclass(type):
    def __new__(meta, cls_name, cls_bases, cls_dict, values=None):
        if not cls_bases or Struct not in cls_bases:
            return super().__new__(meta, cls_name, cls_bases, cls_dict)
        
        # collect
        struct_bases = tuple(base for base in cls_bases if base is not Struct and base.__class__ == StructMetaclass)
        
        fields, defaults = _metaclass_collect_fields(cls_dict, values)
        
        if struct_bases:
            if defaults:
                raise Exception("Cannot use defaults with bases")
            all_fields = sum((base._fields for base in struct_bases), ()) + fields
        else:
            all_fields = fields
        
        # dict                    
        init_def = f"def __init__(__m, {', '.join(all_fields)}):\n"
        for field in all_fields:
            init_def += f"    __m.{field} = {field}\n"
        if not all_fields:
            init_def += "    pass"
        __init__ = exec_def("__init__", init_def)
        __init__.__defaults__ = defaults
        
        @recursive_repr()
        def __repr__(m):
            contents = ", ".join(f"{f}={repr(getattr(m, f))}" for f in m._fields)
            return f"{cls_name}({contents})"
        
        # note - equality is by-identity (unless option to control is added?)
    
        struct_dict = {}
        struct_dict["__init__"] = __init__
        struct_dict["__repr__"] = __repr__
        struct_dict["__slots__"] = fields
        struct_dict["_fields"] = all_fields
        
        fields_set = set(fields)
        
        for k, v in cls_dict.items():
            if isinstance(v, ExcludeAttr):
                v = v.value
            
            if k in fields_set:
                continue
            elif k == "__slots__":
                struct_dict[k] = struct_dict[k] + (v if isinstance(v, tuple) else (v,))
            elif k in struct_dict:
                raise Exception(f"Cannot set {k} in Struct (but can override in inherited classes)")
            else:
                struct_dict[k] = v
        
        return super().__new__(meta, cls_name, cls_bases, struct_dict)

class Struct(metaclass=StructMetaclass):
    """If a class has Struct as a baseclass, it's transformed into a struct.
    All non-private attributes of the class other than functions and descriptors become struct fields.
    Atributes with a value of ... are required, otherwise - optional with the given default value.
    A struct is like a mutable named tuple, except equality goes by identity.
    Inherited classes behave like regular classes unless they have Struct as a direct baseclass.
    Advanced: ExcludeAttr/IncludeAttr, values keyword parameter
    Atributes with a name ending with _ can be referred to without the _.
    """

def SymbolClass(name):
    """Create a class with the given name that returns cached symbols when invoked"""
    class cls(object):
        __slots__ = 'value'
        cache = {}
    
        def __new__(cls, value):
            ident = cls.cache.get(value)
            if ident is None:
                ident = super().__new__(cls)
                ident.value = value
                cls.cache[value] = ident
            return ident
    
        def __str__(m):
            return str(m.value)
        def __bytes__(m):
            return bytes(m.value)
        def __repr__(m):
            return f"`{m.value}"
        
    cls.__name__ = name
    return cls

Symbol = SymbolClass("Symbol")

class classproperty(object):
    """Method decorator that turns it into a read-only class property"""

    def __init__(m, func):
        m.getter = func
        
    def __get__(m, _, cls):
        return m.getter(cls)
    
    # must be read-only, sadly

class staticproperty(object):
    """Method decorator that turns it into a read-only static property"""

    def __init__(m, func):
        m.getter = func
        
    def __get__(m, _, cls):
        return m.getter()
    
    # must be read-only, sadly

class writeonly_property(object):
    """Method decorator that turns it into a write-only property"""

    def __init__(m, func):
        m.func = func
        
    def __set__(m, obj, value):
        return m.func(obj, value)

# reminder to self - if you want a "default property", aka one that has a default value but is settable, use a class field

class lazy_property(object):
    """Method decorator that turns it into a lazily-evaluated property"""

    def __init__(m, func):
        m.func = func

    def __get__(m, obj, cls):
        if obj is None:
            return m
        else:
            value = m.func(obj)
            obj.__dict__[m.func.__name__] = value # won't be called again for this obj
            return value
        
    @staticmethod
    def is_set(obj, name):
        return name in obj.__dict__
    
    @staticmethod
    def clear(obj, name):
        obj.__dict__.pop(name, None)

class lazy_classproperty(object):
    """Method decorator that turns it into a lazily-evaluated class property"""

    def __init__(m, func):
        m.func = func
        
    def __get__(m, _, cls):
        value = m.func(cls)
        setattr(cls, m.func.__name__, value) # won't be called again for this obj
        return value

class lazy_staticproperty(object):
    """Method decorator that turns it into a lazily-evaluated static property"""

    def __init__(m, func):
        m.func = func
        
    def __get__(m, _, cls):
        value = m.func()
        setattr(cls, m.func.__name__, value) # won't be called again for this obj
        return value

class post_property_set(object):
    """Method decorator that creates a field-backed read-write property that calls the
    decorated method when set, with the old and new values"""

    def __init__(m, post_func):
        m.post_func = post_func
        m.attr = "_" + post_func.__name__

    def __get__(m, obj, t = None):
        try:
            if obj is None:
                return m
            else:
                return getattr(obj, m.attr)
        except AttributeError:
            return None

    def __set__(m, obj, value):
        old_value = m.__get__(obj)    
        setattr(obj, m.attr, value)
        m.post_func(obj, old_value, value)
            
class post_property_change(post_property_set):
    """Method decorator that creates a field-backed read-write property that calls the
    decorated method when changed (going by == equality), with the old and new values"""

    def __set__(m, obj, value):
        old_value = m.__get__(obj)
        changed = old_value != value
            
        if changed:
            setattr(obj, m.attr, value)
            m.post_func(obj, old_value, value)
                
def staticclass(cls):
    """Class decorator that turns all methods into static methods, and properties into static properties"""
    for name, value in getattrs(cls):
        if callable(value):
            setattr(cls, name, staticmethod(value))
        elif isinstance(value, property):
            setattr(cls, name, staticproperty(value.fget))
        elif isinstance(value, lazy_property):
            setattr(cls, name, lazy_staticproperty(value.func))
    return cls

defaultdict = collections.defaultdict
deque = collections.deque
CounterDictionary = collections.Counter

WeakKeyDictionary = weakref.WeakKeyDictionary
WeakValueDictionary = weakref.WeakValueDictionary

class LazyDict(defaultdict):
    """Dict that populates entries lazily via a function that takes the key as the argument"""

    def __init__(m, populate):
        m.populate = populate
        defaultdict.__init__(m)

    def __missing__(m, key):
        value = m.populate(key)
        m[key] = value
        return value

class OrderByKey:
    """Implements ordering and equality based on order_key()"""
    # def order_key(m):
    def order_type(m): return type(m)

    def __eq__(m, other):
        if isinstance(other, m.order_type()):
            return m.order_key() == other.order_key()
        else:
            return NotImplemented
    def __ne__(m, other):
        if isinstance(other, m.order_type()):
            return m.order_key() != other.order_key()
        else:
            return NotImplemented
    def __lt__(m, other):
        if isinstance(other, m.order_type()):
            return m.order_key() < other.order_key()
        else:
            return NotImplemented
    def __gt__(m, other):
        if isinstance(other, m.order_type()):
            return m.order_key() > other.order_key()
        else:
            return NotImplemented
    def __le__(m, other):
        if isinstance(other, m.order_type()):
            return m.order_key() <= other.order_key()
        else:
            return NotImplemented
    def __ge__(m, other):
        if isinstance(other, m.order_type()):
            return m.order_key() >= other.order_key()
        else:
            return NotImplemented

def u8(n):
    return n & 0xff
def u16(n):
    return n & 0xffff
def u32(n):
    return n & 0xffffffff
def u64(n):
    return n & 0xffffffffffffffff 

def s8(n):
    return (n & 0x7f) - (n & 0x80)
def s16(n):
    return (n & 0x7fff) - (n & 0x8000)
def s32(n):
    return (n & 0x7fffffff) - (n & 0x80000000)
def s64(n):
    return (n & 0x7fffffffffffffff) - (n & 0x8000000000000000)

def f32(f):
    raise Exception("not implemented yet")
def f64(f):
    raise Exception("not implemented yet")

u8.min, u8.max = 0, 0xff
u16.min, u16.max = 0, 0xffff
u32.min, u32.max = 0, 0xffffffff
u64.min, u64.max = 0, 0xffffffffffffffff
s8.min, s8.max = -0x80, 0x7f
s16.min, s16.max = -0x8000, 0x7fff
s32.min, s32.max = -0x80000000, 0x7fffffff
s64.min, s64.max = -0x8000000000000000, 0x7fffffffffffffff

u8.struct_le = u8.struct_be = struct.Struct("=B")
s8.struct_le = s8.struct_le = struct.Struct("=b")
u16.struct_le, u16.struct_be = struct.Struct("<H"), struct.Struct(">H")
s16.struct_le, s16.struct_be = struct.Struct("<h"), struct.Struct(">h")
u32.struct_le, u32.struct_be = struct.Struct("<I"), struct.Struct(">I")
s32.struct_le, s32.struct_be = struct.Struct("<i"), struct.Struct(">i")
u64.struct_le, u64.struct_be = struct.Struct("<Q"), struct.Struct(">Q")
s64.struct_le, s64.struct_be = struct.Struct("<q"), struct.Struct(">q")
f32.struct_le, f32.struct_be = struct.Struct("<f"), struct.Struct(">f")
f64.struct_le, f64.struct_be = struct.Struct("<d"), struct.Struct(">d")

@context_manager("close")
class BinaryBase(object):
    def close(m):
        m.f.close()

    def len(m):
        old_pos = m.pos()
        m.unwind()
        len = m.pos()
        m.setpos(old_pos)
        return len

    def truncate(m):
        m.f.truncate()

    def eof(m):
        return m.f.tell() == m.len()

    def pos(m):
        return m.f.tell()
    def setpos(m, val):
        m.f.seek(val, 0)
    def addpos(m, val):
        m.f.seek(val, 1)
    def setendpos(m, val):
        m.f.seek(val, 2)

    def subpos(m, val):
        m.addpos(-val)
    def swappos(m, val):
        pos = m.pos()
        m.setpos(val)
        return pos

    def rewind(m):
        m.setpos(0)
    def unwind(m):
        m.f.seek(0, 2)

    def flush(m):
        m.f.flush()
    
    @property
    def length(m):
        return m.len()
    @property
    def position(m):
        return m.pos()
    @position.setter
    def position(m, value):
        m.setpos(value)

class BinaryReader(BinaryBase):
    """Wraps a stream, allowing to easily read binary data from it"""

    def __init__(m, path, big_end = False, enc = "utf-8", wenc = "utf-16"):
        m.big_end, m.enc, m.wenc = big_end, enc, wenc
        
        if isinstance(path, (str, CustomPath)):
            m.f = file_open(path)
        else:
            m.f = path

    def u8(m):
        return u8.struct_le.unpack(m.f.read(1))[0]
    def u16be(m):
        return u16.struct_be.unpack(m.f.read(2))[0]
    def u16le(m):
        return u16.struct_le.unpack(m.f.read(2))[0]
    def u16(m):
        return m.u16be() if m.big_end else m.u16le()
    def u32be(m):
        return u32.struct_be.unpack(m.f.read(4))[0]
    def u32le(m):
        return u32.struct_le.unpack(m.f.read(4))[0]
    def u32(m):
        return m.u32be() if m.big_end else m.u32le()
    def u64be(m):
        return u64.struct_be.unpack(m.f.read(8))[0]
    def u64le(m):
        return u64.struct_le.unpack(m.f.read(8))[0]
    def u64(m):
        return m.u64be() if m.big_end else m.u64le()

    def s8(m):
        return s8.struct_le.unpack(m.f.read(1))[0]
    def s16be(m):
        return s16.struct_be.unpack(m.f.read(2))[0]
    def s16le(m):
        return s16.struct_le.unpack(m.f.read(2))[0]
    def s16(m):
        return m.s16be() if m.big_end else m.s16le()
    def s32be(m):
        return s32.struct_be.unpack(m.f.read(4))[0]
    def s32le(m):
        return s32.struct_le.unpack(m.f.read(4))[0]
    def s32(m):
        return m.s32be() if m.big_end else m.s32le()
    def s64be(m):
        return s64.struct_be.unpack(m.f.read(8))[0]
    def s64le(m):
        return s64.struct_le.unpack(m.f.read(8))[0]
    def s64(m):
        return m.s64be() if m.big_end else m.s64le()

    def bytes(m, size, allow_eof=False):
        result = m.f.read(size)
        if len(result) != size and not allow_eof:
            raise struct.error("end of file")
        return result
    def bytearray(m, size, allow_eof=False):
        result = bytearray(size)
        if m.f.readinto(result) != size and not allow_eof:
            raise struct.error("end of file")
        return result
    
    def str(m, len, enc=None):
        return m.bytes(len).decode(enc or m.enc)
    def wstr(m, len, enc=None):
        return m.bytes(len * 2).decode(enc or m.wenc)

    def f32be(m):
        return f32.struct_be.unpack(m.f.read(4))[0]
    def f32le(m):
        return f32.struct_le.unpack(m.f.read(4))[0]
    def f32(m):
        return m.f32be() if m.big_end else m.f32le()
    def f64be(m):
        return f64.struct_be.unpack(m.f.read(8))[0]
    def f64le(m):
        return f64.struct_le.unpack(m.f.read(8))[0]
    def f64(m):
        return m.f64be() if m.big_end else m.f64le()

    def zbytes(m, size=None, count=1, allow_eof=False):
        zero = b"\0" * count
        if size is None:
            # TODO: optimize if seeking supported?
            result = b""
            while True:
                char = m.bytes(count, allow_eof)
                if allow_eof and len(char) < count:
                    if char:
                        raise struct.error("end of file inside char")
                    break
                elif char == zero:
                    break
                else:
                    result += char
        else:
            result = m.bytes(size * count, allow_eof)
            if allow_eof and count > 1 and len(result) % count:
                raise struct.error("end of file inside char")
            # TODO: any better way? (can't search/split if count > 1)
            for i in range(0, size, count):
                if result[i:i+count] == zero:
                    result = result[:i]
                    break
        return result
        
    def zstr(m, size=None, enc=None):
        return m.zbytes(size).decode(enc or m.enc)
    def wzstr(m, size=None, enc=None):
        return m.zbytes(size, 2).decode(enc or m.wenc)
    
    def struct(m, struct):
        return struct.unpack(m.f.read(struct.size))
    
    def list(m, func, size):
        return [func() for _ in range(size)]
    
    def bool(m):
        return m.u8() != 0

    def nat(m):
        nat = 0
        shift = 0
        more = True
        while more:
            val = m.u8()
            nat |= (val & 0x7f) << shift
            more = (val >> 7)
            shift += 7
        return nat
    
    def int(m):
        nat = m.nat()
        if nat & 1:
            return -(nat - 1) >> 1
        else:
            return nat >> 1
            
    def float(m):
        return m.f64() # python's float

    def nbytes(m):
        return m.bytes(m.nat())

    def align(m, size, start = 0):
        misalign = (m.pos() - start) % size
        if misalign:
            m.addpos(size - misalign)

class BinaryBitReader(BinaryBase):
    """Wraps a stream, allowing to easily read bits from it"""

    def __init__(m, f, big_end = False):
        m.f = f
        m._bits = 0
        m._nbits = 0
        m.big_end = big_end

    @property
    def bit_position(m):
        return m.pos() * 8 - m._nbits

    def byte_align(m): # effectively flushes
        m.subpos(m._nbits // 8)
        m._bits, m._nbits = 0, 0

    def _add_bits_le(m, strict):
        value = m.f.read(1)
        if value:
            m._bits |= ord(value) << m._nbits
            m._nbits += 8
        elif strict:
            raise struct.error("end of file")

    def _bits_le(m, n, advance=True):
        while m._nbits < n:
            m._add_bits_le(advance)
        
        value = m._bits & ((1 << n) - 1)
        if advance:
            m._bits >>= n
            m._nbits -= n
        return value

    def _add_bits_be(m, strict):
        value = m.f.read(1)
        if value:
            m._bits = (m._bits << 8) | ord(value)
            m._nbits += 8
        elif strict:
            raise struct.error("end of file")

    def _bits_be(m, n, advance=True):
        while m._nbits < n:
            m._add_bits_be(advance)
        
        bottom_bits = m._nbits - n
        value = m._bits >> bottom_bits
        if advance:
            m._bits &= (1 << bottom_bits) - 1
            m._nbits -= n
        return value

    def bits(m, n):
        return m._bits_be(n) if m.big_end else m._bits_le(n)

    def bit(m):
        return m.bits(1) != 0

    def peek_bits(m, n):
        return m._bits_be(n, False) if m.big_end else m._bits_le(n, False)

    def peek_bit(m):
        return m.peek_bits(1) != 0

    def _advance_bits_long(m, n):
        n -= m._nbits
        m._bits, m._nbits = 0, 0
        m.addpos(n // 8)
        n %= 8
        if n:
            m._add_bits_le(True) # le/be doesn't matter after above flush
        return n # bits left to advance
    
    def _advance_bits_le(m, n):
        if n > m._nbits:
            n = m._advance_bits_long(n)
        m._bits >>= n
        m._nbits -= n
    
    def _advance_bits_be(m, n):
        if n > m._nbits:
            n = m._advance_bits_long(n)
        m._bits &= (1 << (m._nbits - n)) - 1
        m._nbits -= n

    def advance_bits(m, n):
        return m._advance_bits_be(n) if m.big_end else m._advance_bits_le(n)

class BinaryWriter(BinaryBase):
    """Wraps a stream, allowing to easily write binary data to it"""

    def __init__(m, path = None, big_end = False, enc = "utf-8", wenc = "utf-16"):
        m.big_end, m.enc, m.wenc = big_end, enc, wenc
        
        if path is None:
            m.f = BytesIO()
        elif isinstance(path, (str, CustomPath)):
            m.f = file_create(path)
        else:
            m.f = path

    def u8(m, v):
        m.f.write(u8.struct_le.pack(v))
    def u16(m, v):
        if m.big_end:
            m.f.write(u16.struct_be.pack(v))
        else:
            m.f.write(u16.struct_le.pack(v))
    def u32(m, v):
        if m.big_end:
            m.f.write(u32.struct_be.pack(v))
        else:
            m.f.write(u32.struct_le.pack(v))
    def u64(m, v):
        if m.big_end:
            m.f.write(u64.struct_be.pack(v))
        else:
            m.f.write(u64.struct_le.pack(v))

    def s8(m, v):
        m.f.write(s8.struct_le.pack(v))
    def s16(m, v):
        if m.big_end:
            m.f.write(s16.struct_be.pack(v))
        else:
            m.f.write(s16.struct_le.pack(v))
    def s32(m, v):
        if m.big_end:
            m.f.write(s32.struct_be.pack(v))
        else:
            m.f.write(s32.struct_le.pack(v))
    def s64(m, v):
        if m.big_end:
            m.f.write(s64.struct_be.pack(v))
        else:
            m.f.write(s64.struct_le.pack(v))

    def f32(m, v):
        if m.big_end:
            m.f.write(f32.struct_be.pack(v))
        else:
            m.f.write(f32.struct_le.pack(v))
    def f64(m, v):
        if m.big_end:
            m.f.write(f64.struct_be.pack(v))
        else:
            m.f.write(f64.struct_le.pack(v))

    def bytes(m, v):
        m.f.write(v)
        
    def str(m, v, enc=None):
        m.bytes(v.encode(enc or m.enc))
    def wstr(m, v, enc=None):
        m.bytes(v.encode(enc or m.wenc))
            
    def zbytes(m, v, size=None, count=1):
        assert not (count > 1 and len(v) % count)
        zero = b"\0" * count
        if size is None:
            m.bytes(v)
            m.bytes(zero)
        else:
            if len(v) > size * count:
                raise struct.error("input too large for zbytes with fixed size")
            m.bytes(v)
            for i in range(size - len(v) // count):
                m.bytes(zero)
        
    def zstr(m, v, size=None, enc=None):
        m.zbytes(v.encode(enc or m.enc), size)
    def wzstr(m, v, size=None, enc=None):
        m.zbytes(v.encode(enc or m.wenc), size, 2)

    def struct(m, struct, value):
        m.f.write(struct.pack(*value))

    def list(m, func, value):
        for v in value:
            func(v)
            
    def fill(m, v, size):
        for i in range(size):
            m.u8(v)

    def nat(m, v):
        assert v >= 0
        more = True
        while more:
            part = v & 0x7f
            v >>= 7
            more = v != 0
            m.u8(part | (more << 7))
            
    def bool(m, v):
        m.u8(1 if v else 0)
    
    def int(m, v):
        if v >= 0:
            m.nat(v << 1)
        else:
            m.nat((-v << 1) + 1)
            
    def float(m, v):
        m.f64(v) # python's float

    def nbytes(m, v):
        m.nat(len(v))
        m.bytes(v)

    def align(m, size, start = 0, value = 0):
        misalign = (m.pos() - start) % size
        if misalign:
            for _ in range(size - misalign):
                m.u8(value)
                
class BinaryBitWriter(BinaryBase):
    """Wraps a stream, allowing to easily write bits to it"""

    def __init__(m, f, big_end = False):
        m.f = f
        m._bits = 0
        m._nbits = 0
        m.big_end = big_end

    @property
    def bit_position(m):
        return m.pos() * 8 - m._nbits

    def byte_align(m):
        m.flush()

    def _remove_bits_le(m):
        m.f.write(byte(m._bits & 0xff))
        m._bits >>= 8
        m._nbits -= 8

    def _bits_le(m, n, v):
        m._bits |= v << m._nbits
        m._nbits += n

        while m._nbits >= 8:
            m._remove_bits_le()

    def _remove_bits_be(m):
        m._nbits -= 8
        m.f.write(byte(m._bits >> m._nbits))
        m._bits &= (1 << m._nbits) - 1

    def _bits_be(m, n, v):
        m._bits = (m._bits << n) | v
        m._nbits += n

        while m._nbits >= 8:
            m._remove_bits_be()

    def bits(m, n, v):
        if m.big_end:
            m._bits_be(n, v)
        else:
            m._bits_le(n, v)

    def bit(m, v):
        m.bits(1, v)
    
    def close(m):
        m.flush()
        super().close()
        
    def _flush_le(m):
        if m._nbits:
            m.f.write(byte(m._bits & 0xff))
        m._bits, m._nbits = 0, 0
        
    def _flush_be(m):
        if m._nbits:
            m.f.write(byte(m._bits << (8 - m._nbits)))
        m._bits, m._nbits = 0, 0
            
    def flush(m):
        if m.big_end:
            m._flush_be()
        else:
            m._flush_le()

class BinaryBuffer:
    """Wraps a bytearray, allowing to easily read & write binary data in it"""
    # TODO: make more consistent with BinaryReader/Writer (big_end, enc, wenc)

    def __init__(m, src):
        if isinstance(src, bytearray):
            m.buf = src
        else:
            m.buf = bytearray(src)
            
    def __len__(m):
        return len(m.buf)
    
    def r_u8(m, addr):
        return m.buf[addr]
    def w_u8(m, addr, val):
        m.buf[addr] = val
    
    def r_u16(m, addr):
        return u16.struct_le.unpack_from(m.buf, addr)[0]
    def w_u16(m, addr, val):
        u16.struct_le.pack_into(m.buf, addr, val)
        
    def r_u32(m, addr):
        return u32.struct_le.unpack_from(m.buf, addr)[0]
    def w_u32(m, addr, val):
        u32.struct_le.pack_into(m.buf, addr, val)
        
    def r_u64(m, addr):
        return u64.struct_le.unpack_from(m.buf, addr)[0]
    def w_u64(m, addr, val):
        u64.struct_le.pack_into(m.buf, addr, val)
       
    def r_s8(m, addr):
        return s8.struct_le.unpack_from(m.buf, addr)[0]
    def w_s8(m, addr, val):
        s8.struct_le.pack_into(m.buf, addr, val)
         
    def r_s16(m, addr):
        return s16.struct_le.unpack_from(m.buf, addr)[0]
    def w_s16(m, addr, val):
        s16.struct_le.pack_into(m.buf, addr, val)
        
    def r_s32(m, addr):
        return s32.struct_le.unpack_from(m.buf, addr)[0]
    def w_s32(m, addr, val):
        s32.struct_le.pack_into(m.buf, addr, val)
        
    def r_s64(m, addr):
        return s64.struct_le.unpack_from(m.buf, addr)[0]
    def w_s64(m, addr, val):
        s64.struct_le.pack_into(m.buf, addr, val)
        
    def r_f32(m, addr):
        return f32.struct_le.unpack_from(m.buf, addr)[0]
    def w_f32(m, addr, val):
        f32.struct_le.pack_into(m.buf, addr, val)
        
    def r_f64(m, addr):
        return f64.struct_le.unpack_from(m.buf, addr)[0]
    def w_f64(m, addr, val):
        f64.struct_le.pack_into(m.buf, addr, val)
        
    def r_bytes(m, addr, count, allow_eof=False):
        data = m.buf[addr:addr+count]
        if not allow_eof and len(data) < count:
            raise struct.error("end of buffer")
        return data
        
    def r_zbytes(m, addr, size=None, count = 1):
        zero = b"\0" * count
        
        if size is None:
            result = b""
            while True:
                char = m.r_bytes(addr, count)
                if char == zero:
                    break
                else:
                    result += char
                    addr += count
        else:
            result = m.r_bytes(addr, size * count)
            # TODO: any better way? (can't search/split if count > 1)
            for i in range(0, size, count):
                if result[i:i+count] == zero:
                    result = result[:i]
                    break
        return result
        
    def r_zstr(m, addr, size=None, enc="utf-8"):
        return m.r_zbytes(addr, size).decode(enc)
    def r_wzstr(m, addr, size=None, enc="utf-16"):
        return m.r_zbytes(addr, size, 2).decode(enc)
    
    def w_bytes(m, addr, val):
        m.buf[addr:addr+len(val)] = val
    
    def w_zbytes(m, addr, val, size=None, count=1):
        zero = b"\0" * count
        assert not (count > 1 and len(val) % count)

        if size is None:
            m.w_bytes(addr, val)
            m.w_bytes(addr + len(val), zero)
        else:
            if len(val) > size * count:
                raise struct.error("input too large for zbytes with fixed size")
            m.w_bytes(addr, val)
            end_addr = addr + size * count
            addr += len(val)
            while addr < end_addr:
                m.w_bytes(addr, zero)
                addr += count
        
    def w_zstr(m, addr, val, size=None, enc="utf-8"):
        m.w_zbytes(addr, val.encode(enc), size)
    def w_wzstr(m, addr, val, size=None, enc='utf-16'):
        m.w_zbytes(addr, val.encode(enc), size, 2)

    def r_struct(m, addr, struct):
        return struct.unpack_from(m.buf, addr)
    def w_struct(m, addr, struct, val):
        struct.pack_into(m.buf, addr, *val)
        
    def w_from(m, addr, src, src_addr, count):
        m.buf[addr:addr+count] = src.r_bytes(src_addr, count)
    def w_fill(m, addr, value, count):
        m.buf[addr:addr+count] = byte(value) * count
    def w_zero(m, addr, count):
        m.w_fill(addr, 0, count)

def e(value):
    """Return if 'value' is not None (for my sanity)"""
    return value is not None

def default(value, defval):
    """Return 'defval' if 'value' is None"""
    return value if e(value) else defval

def nop(value):
    """The identity function"""
    return value

def product(items):
    """Return the product of 'items'"""
    result = 1
    for item in items:
        result *= item
    return result

def str_insert(str, at, what):
    """Return a string based on 'str' with 'what' inserted at position 'at'"""
    return str[:at] + what + str[at:]

def str_replace_at(str, at, count, what):
    """Return a string based on 'str' with 'what' replacing 'count' chars at position 'at'"""
    return str[:at] + what + str[at + count:]

def str_replace_between(str, start, end, what):
    """Return a string based on 'str' with 'what' replacing chars between 'start' and 'end'"""
    return str[:start] + what + str[end:]

def str_remove_at(str, at, count):
    """Return a string based on 'str' with 'count' chars removed at position 'at'"""
    return str[:at] + str[at + count:]

def str_remove_between(str, start, end):
    """Return a string based on 'str' with chars removed between 'start' and 'end"""
    return str[:start] + str[end:]

def str_trunc(str, count):
    """Truncates a string if larger than 'count' characters"""
    if len(str) > count:
        return str[:count]
    else:
        return str

def str_ljust_trunc(str, count, fillchar = ' '):
    """Left-justifies a string and truncates it"""
    return str_trunc(str, count).ljust(count, fillchar)

def str_rjust_trunc(str, count, fillchar = ' '):
    """Right-justifies a string and truncates it"""
    return str_trunc(str, count).rjust(count, fillchar)

def str_remove_prefix(str, prefix):
    """Return a string based on 'str' with 'prefix' removed from its beginning"""
    if str.startswith(prefix):
        return str[len(prefix):]
    else:
        return str

def str_remove_suffix(str, suffix):
    """Return a string based on 'str' with 'suffix' removed from its end"""
    if str.endswith(suffix):
        return str[:-len(suffix)]
    else:
        return str
    
def str_before_first(str, match, s=None, e=None):
    """Return 'str' before the first 'match'"""
    i = str.find(match, s, e)
    return str[s:i] if i >= 0 else str[s:e]

def str_before_last(str, match, s=None, e=None):
    """Return 'str' before the last 'match'"""
    i = str.rfind(match, s, e)
    return str[s:i] if i >= 0 else ""

def str_after_first(str, match, s=None, e=None):
    """Return 'str' after the first 'match'"""
    i = str.find(match, s, e)
    return str[i+len(match):e] if i >= 0 else ""

def str_after_last(str, match, s=None, e=None):
    """Return 'str' after the last 'match'"""
    i = str.rfind(match, s, e)
    return str[i+len(match):e] if i >= 0 else str[s:e]

def str_split_first(str, match, s=None, e=None):
    """Return 'str' before and after the first 'match'"""
    i = str.find(match, s, e)
    return (str[s:i], str[i+len(match):e]) if i >= 0 else (str[s:e], "")

def str_split_last(str, match, s=None, e=None):
    """Return 'str' before and after the last 'match'"""
    i = str.rfind(match, s, e)
    return (str[s:i], str[i+len(match):e]) if i >= 0 else ("", str[s:e])
    
def str_replace_batch(val, batch):
    """Return a string based on 'val' that contains replacements defined in 'batch'.
    'batch' is a dict or list of pairs, with each pair being:
      (str, str or (lambda: str)) - simple replacement
      (regex, str) - regex replacement (with regex pre-compilation)
      ((re, str), str) - regex replacement without pre-compilation"""
    if isinstance(batch, dict):
        batch = batch.items()
        
    for k, v in batch:
        if isinstance(k, str):
            if callable(v):
                if k not in val:
                    continue
                v = v()
            val = val.replace(k, v)
        elif isinstance(k, re.Pattern):
            val = k.sub(v, val)
        else:
            assert k[0] == re
            val = re.sub(k[1], v, val)
    return val
    
str_replace_by_dict = str_replace_batch # compat.

def list_chunk(list, size):
    """Split a list into sublists of size 'size' each (except possibly the last sublist)"""
    count = div_up(len(list), size)
    return [list[i * size : (i + 1) * size] for i in range(count)]

def list_remove(list, func):
    """Remove elements from a list that match the given 'func'"""
    for i, item in enumerate(list):
        if func(item):
            del list[i]
            i -= 1

def list_find(list, val):
    """Find the index of the given element in the list"""
    try:
        return list.index(val)
    except ValueError:
        return -1

def list_find_where(list, func):
    """Find the index of the first element in a list that matches predicate 'func'"""
    for i, item in enumerate(list):
        if func(item):
            return i
    return -1

def list_rfind_where(list, func):
    """Find the index of the last element in a list that matches predicate 'func'"""
    for i_rev, item in enumerate(reversed(list)):
        if func(item):
            return len(list) - 1 - i_rev # ...
    return -1

def list_get(list, i, defval = None):
    """Get the 'i'th element in the list, or 'defval' (default: None) if not a valid index"""
    return list[i] if 0 <= i < len(list) else defval

def list_rget(list, i, defval = None):
    """Get the 'i'th element in the list from the end, or 'defval' (default: None) if not a valid index"""
    return list[-(i+1)] if 0 <= i < len(list) else defval

def list_set(list, i, val, defval = None):
    """Set the 'i'th element in the list, growing the list with 'defval's (default: Nones) as needed"""
    assert i >= 0
    while i >= len(list):
        list.append(defval)
    list[i] = val

str_get = list_get
str_rget = list_rget
str_chunk = list_chunk

def list_pop(list, defval = None):
    """Pop the element from the list, or get 'defval' (default: None) if empty"""
    return list.pop() if list else defval

def list_unpack(list, n, defval = None):
    """Return the 'n' first elements in the list, padding with 'defval' if needed"""
    for i in range(n):
        yield list_get(list, i, defval)

def tuple_insert(tuple, i, newval):
    """Return a new tuple based on 'tuple' with 'newval' inserted at index 'i'"""
    return tuple[:i] + (newval,) + tuple[i:]

def tuple_replace_at(tuple, i, newval):
    """Return a new tuple based on 'tuple' with 'newval' replacing the element at index 'i'"""
    return tuple[:i] + (newval,) + tuple[i+1:]

def tuple_remove_at(tuple, i, count=1):
    """Return a new tuple based on 'tuple' with 'count' elements removed at index 'i'"""
    return tuple[:i] + tuple[i+count:]

def dict_first_key(dict):
    for key in dict:
        return key

def iter_chunk(src, count):
    it = iter(src)
    while True:
        chunk = tuple(itertools.islice(it, count))
        if not chunk:
            break
        yield chunk

def func_union(func1, func2, return_early=None, return_combine=None):
    """Return a function that behaves like func1 followed by func2. Either of func1/func2 may be None.
    'return_early' can decide whether to return func1's result. 'return_combine' can combine func1's and func2's results"""
    if func1 is None:
        return func2
    elif func2 is None:
        return func1
    elif return_early:
        def union(*args, **kwargs):
            ret = func1(*args, **kwargs)
            if return_early(ret):
                return ret
            return func2(*args, **kwargs)
        return union
    else:
        def union(*args, **kwargs):
            ret1 = func1(*args, **kwargs)
            ret2 = func2(*args, **kwargs)
            if return_combine:
                return return_combine(ret1, ret2)
            # else, None
        return union

def getattrs(obj, private = True, magic = False):
    """Get all attributes of 'obj' (By default, including _privates but excluding __magic__)"""
    for attr in dir(obj):
        if not private and attr.startswith("_"):
            continue
        if not magic and attr.startswith("__") and attr.endswith("__"):
            continue
        yield attr, getattr(obj, attr)

class Point(Tuple):
    """An (x,y) tuple representing a 2d point and supporting arithmetic operations"""
    x = y = ...

    def __add__(m, other):
        assert isinstance(other, Point)
        return Point(m.x + other.x, m.y + other.y)

    def __sub__(m, other):
        assert isinstance(other, Point)
        return Point(m.x - other.x, m.y - other.y)

    def __mul__(m, other):
        if isinstance(other, Point):
            return Point(m.x * other.x, m.y * other.y)
        else:
            return Point(m.x * other, m.y * other)
        
    def __rmul__(m, other):
        return Point(other * m.x, other * m.y)

    def __truediv__(m, other):
        if isinstance(other, Point):
            return Point(m.x / other.x, m.y / other.y)
        else:
            return Point(m.x / other, m.y / other)
        
    def __rtruediv__(m, other):
        return Point(other / m.x, other / m.y)
        
    __div__ = __truediv__
    __rdiv__ = __rtruediv__
    
    def __floordiv__(m, other):
        if isinstance(other, Point):
            return Point(m.x // other.x, m.y // other.y)
        else:
            return Point(m.x // other, m.y // other)
    
    def __rfloordiv__(m, other):
        return Point(other // m.x, other // m.y)
    
    def __mod__(m, other):
        if isinstance(other, Point):
            return Point(m.x % other.x, m.y % other.y)
        else:
            return Point(m.x % other, m.y % other)
        
    def __rmod__(m, other):
        return Point(other % m.x, other % m.y)

    def __abs__(m):
        return Point(abs(m.x), abs(m.y))

    def __neg__(m):
        return Point(-m.x, -m.y)

    def __nonzero__(m):
        return m.x or m.y
    
    def __bool__(m):
        return bool(m.__nonzero__())

    def __ge__(m, other):
        assert isinstance(other, Point)
        return m.x >= other.x and m.y >= other.y

    def __gt__(m, other):
        assert isinstance(other, Point)
        return m.x > other.x and m.y > other.y

    def __le__(m, other):
        assert isinstance(other, Point)
        return m.x <= other.x and m.y <= other.y

    def __lt__(m, other):
        assert isinstance(other, Point)
        return m.x < other.x and m.y < other.y

    def set_x(m, x):
        return Point(x, m.y)

    def set_y(m, y):
        return Point(m.x, y)
    
    def int(m):
        return Point(int(m.x), int(m.y))
    
    def float(m):
        return Point(float(m.x), float(m.y))
    
    @classmethod
    def repeat(cls, value):
        return cls(value, value)
    
    @property
    def norm_squared(m):
        return m.x * m.x + m.y * m.y
    
    @property
    def norm(m):
        return math.sqrt(m.norm_squared)
    
    @staticmethod
    def distance_squared(m, o):
        return (m - o).norm_squared
    
    @staticmethod
    def distance(m, o):
        return (m - o).norm
    
Point.zero = Point(0, 0)

class Rect(Tuple):
    """An (x,y,w,h) tuple representing a 2d rectangle"""
    x = y = w = h = ...

    @property
    def x2(m):
        return m.x + m.w

    @property
    def y2(m):
        return m.y + m.h

    @property
    def pos(m):
        return Point(m.x, m.y)

    @property
    def size(m):
        return Point(m.w, m.h)

    @property
    def pos2(m):
        return Point(m.x2, m.y2)
    
    @property
    def center(m):
        return m.pos + m.size / 2

    def __nonzero__(m):
        return m.w > 0 and m.h > 0
    
    def __bool__(m):
        return bool(m.__nonzero__())

    def __contains__(m, p):
        if isinstance(p, Point):
            return p >= m.pos and p < m.pos2
        elif isinstance(p, Rect):
            return p.pos >= m.pos and p.pos2 <= m.pos2
        else:
            raise Exception("Not implemented")

    def overlaps(m, p):
        assert isinstance(p, Rect)
        return p.pos < m.pos2 and p.pos2 > m.pos

    def __and__(m, p):
        assert isinstance(p, Rect)
        return Rect.from_coords(max(m.x, p.x), max(m.y, p.y), max(min(m.x2, p.x2), 0), max(min(m.y2, p.y2), 0))

    def __add__(m, other):
        assert isinstance(other, Point)
        return Rect(m.x + other.x, m.y + other.y, m.w, m.h)

    def __sub__(m, other):
        assert isinstance(other, Point)
        return Rect(m.x - other.x, m.y - other.y, m.w, m.h)
        
    @classmethod
    def from_pos_size(cls, pos, size):
        return cls(pos.x, pos.y, size.x, size.y)

    @classmethod
    def from_pos(cls, pos, pos2):
        return cls(pos.x, pos.y, pos2.x - pos.x, pos2.y - pos.y)

    @classmethod
    def from_coords(cls, x, y, x2, y2):
        return cls(x, y, x2 - x, y2 - y)

Rect.zero = Rect(0, 0, 0, 0)

class ProjectedDictBase(dict):
    """A dict baseclass where keys are projected via _project before compared"""
    @classmethod
    def _project(cls, key):
        raise NotImplementedError()

    def __init__(m, E=None, **F):
        super().__init__()
        m.update(E, **F)
    def __getitem__(m, key):
        return super().__getitem__(m.__class__._project(key))
    def __setitem__(m, key, value):
        super().__setitem__(m.__class__._project(key), value)
    def __delitem__(m, key):
        return super().__delitem__(m.__class__._project(key))
    def __contains__(m, key):
        return super().__contains__(m.__class__._project(key))
    def pop(m, key, *args, **kwargs):
        return super().pop(m.__class__._project(key), *args, **kwargs)
    def get(m, key, *args, **kwargs):
        return super().get(m.__class__._project(key), *args, **kwargs)
    def setdefault(m, key, *args, **kwargs):
        return super().setdefault(m.__class__._project(key), *args, **kwargs)
    
    def update(m, E=None, **F):
        if E:
            if hasattr(E, "items"):
                for k, v in E.items():
                    m[k] = v
            else:
                for k, v in E:
                    m[k] = v
        
        if F:
            for k, v in F.items():
                m[k] = v

class CaseInsensitiveDict(ProjectedDictBase):
    """A dict where key comparison is case-insensitive"""
    @classmethod
    def _project(cls, key):
        return key.lower()
    
class defaultlist(list):
    """A list allowing read/write of arbitrary indices, filling unused indices via 'defgetter'()"""
    def __init__(m, defgetter):
        m.defgetter = defgetter
        
    def _fill(m, i):
        if isinstance(i, slice):
            while i.stop > len(m):
                m.append(m.defgetter())
        else:
            while i >= len(m):
                m.append(m.defgetter())
            
    def __getitem__(m, i):
        m._fill(i)
        return list.__getitem__(m, i)
        
    def __setitem__(m, i, val):
        m._fill(i)
        list.__setitem__(m, i, val)
        
class MultidimArray(object):
    """A multi-dimensional array of a fixed size"""
    def __init__(m, size, defval=None):
        m.dim = len(size)
        m.size = size
        m.array = [defval] * product(size)

    def copy(m):
        return deepcopy(m)
        
    def _getindex(m, indices):
        array_index = 0
        for i in range(m.dim):
            index, size = indices[i], m.size[i]
            if not (0 <= index < size):
                raise IndexError(indices)
            if i > 0:
                array_index *= size 
            array_index += index
        return array_index
                
    def __getitem__(m, indices):
        return m.array[m._getindex(indices)]
    
    def __setitem__(m, indices, value):
        m.array[m._getindex(indices)] = value
        
    def indices(m):
        indices = [0] * m.dim
        while True:
            yield indices
            
            for i in reversed(range(m.dim)):
                indices[i] += 1
                if indices[i] >= m.size[i]:
                    indices[i] = 0                    
                else:
                    break
            else:
                break

class HeapQueue:
    """A class wrapper over heapq"""
    def __init__(m, iterable=None):
        m.list = list(iterable) if e(iterable) else []
        heapq.heapify(m.list)
        
    def add(m, v):
        heapq.heappush(m.list, v)
    
    def peekleft(m):
        return m.list[0]
    
    def popleft(m):
        return heapq.heappop(m.list)
    
    def __len__(m):
        return len(m.list)

    def __repr__(m):
        return f"HeapQueue({repr(m.list)})"

class RawIOBaseWSeek(io.RawIOBase):
    """Like RawIOBase, but allows seeking"""
    def seek(m, position, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            m.position = position
        elif whence == io.SEEK_CUR:
            m.position += position
        elif whence == io.SEEK_END:
            m.position = m.length + position
        return m.position

class PartialIO(RawIOBaseWSeek):
    """Exposes a region of an existing stream as a stream"""
    def __init__(m, io, offset, length=None):
        length = length if e(length) else io.length - offset 
        m.io = io
        m.position = 0
        m.offset = offset
        m.length = length
        
    def flush(m):
        return m.io.flush()
          
    def readinto(m, target):
        size = len(target)
        view = memoryview(target)
        
        size = max(min(size, m.length - m.position), 0)        
        m.io.seek(m.offset + m.position)
        count = m.io.readinto(view[:size])
        
        m.position += count
        return count
        
    def write(m, data):
        size = len(data)
        view = memoryview(data)
        
        size = max(min(size, m.length - m.position), 0)        
        m.io.seek(m.offset + m.position)
        count = m.io.write(view[:size])
        
        m.position += count
        return count

class SegmentedIO(RawIOBaseWSeek):
    """A stream that combines several existing streams"""
    class Segment(Tuple):
        start = file = offset = size = ...
    
    def __init__(m):
        m.segments = []
        m.last_segment = None
        m.position = 0
        m.length = 0
        
    def add(m, file, offset, size):
        m.segments.append(m.Segment(m.length, file, offset, size))
        m.length += size
            
    def flush(m):
        for segment in m.segments:
            segment.file.flush()
            
    def _find(m, offset):
        segment = m.last_segment
        if segment and segment.start <= offset < segment.start + segment.size:
            return segment, offset - segment.start
        
        for segment in m.segments:
            if segment.start <= offset < segment.start + segment.size:
                m.last_segment = segment
                return segment, offset - segment.start
                
        return None, 0
    
    def readinto(m, target):
        offset = 0
        size = len(target)
        view = memoryview(target)
        
        while offset < size:
            segment, offset_in_seg = m._find(m.position)
            if segment is None:
                break
            
            segment.file.seek(segment.offset + offset_in_seg)
            seg_count = min(segment.size - offset_in_seg, size - offset)
            seg_count = segment.file.readinto(view[offset : offset + seg_count])
            if seg_count is None:
                return offset if offset else None
            
            if seg_count == 0:
                break
            
            offset += seg_count
            m.position += seg_count
            
        return offset
        
    def write(m, data):
        offset = 0
        size = len(data)
        view = memoryview(data)
        
        while offset < size:
            segment, offset_in_seg = m._find(m.position)
            if segment is None:
                break
            
            segment.file.seek(segment.offset + offset_in_seg)
            seg_count = min(segment.size - offset_in_seg, size - offset)
            seg_count = segment.file.write(view[offset : offset + seg_count])
            if seg_count is None:
                return offset if offset else None
            
            if seg_count == 0:
                break
            
            offset += seg_count
            m.position += seg_count
            
        return offset
    
class ByteArrayIO(RawIOBaseWSeek):
    """Exposes a bytearray as a stream""" # did I miss this in the stdlib?
    def __init__(m, arr):
        m.arr = arr
        m.position = 0
    
    @property
    def length(m):
        return len(m.arr)
    
    def readinto(m, target):
        pos = m.position
        slice = m.arr[pos:pos + len(target)]
        count = len(slice)
        target[:count] = slice
        m.position += count
        return count
        
    def write(m, data):
        pos = m.position
        if pos > len(m.arr): # slice syntax doesn't handle this case...
            m.arr += bytearray(pos - len(m.arr))
        size = len(data)
        m.arr[pos:pos + size] = data
        m.position += size
        return size

class IOWrapper:
    def __init__(m, stream):
        m.stream = stream
    def __enter__(m):
        return m.stream
    def __exit__(m, *_):
        pass

class CustomPath(str):
    """A path that refers to some custom-obtained data"""

    def open(m):
        raise FileNotFoundError(type(m))
    def open_text(m, encoding, errors, newline):
        raise FileNotFoundError(type(m))
    def create(m):
        raise FileNotFoundError(type(m))
    def create_text(m, encoding, errors, newline):
        raise FileNotFoundError(type(m))

def path_is_native(path):
    return not isinstance(path, CustomPath)

class StdPath(CustomPath):
    """A path that refers to the standard streams"""

    def open(m):
        return IOWrapper(sys.stdin.buffer)

    def open_text(m, encoding, errors, newline):
        sys.stdin.reconfigure(encoding=encoding, errors=errors, newline=newline)
        return IOWrapper(sys.stdin)

    def create(m):
        return IOWrapper(sys.stdout.buffer)

    def create_text(m, encoding, errors, newline):
        sys.stdout.reconfigure(encoding=encoding, errors=errors, newline=newline)
        return IOWrapper(sys.stdout)

class DataPath(CustomPath):
    """A path that refers to some data"""

    def __new__(cls, value, data):
        path = str.__new__(cls, value)
        path.data = data
        return path

    def open(m):
        return BytesIO(m.data)

    def open_text(m, encoding, errors, newline):
        return StringIO(m.data.decode(encoding, errors), newline=newline)

class URLPath(CustomPath):
    """A path that's actually a URL"""

    def open(m):
        from urllib.request import urlopen
        return urlopen(m)

    def open_text(m, encoding, errors, newline):
        return io.TextIOWrapper(m.open(), encoding, errors, newline)

def file_open(path):
    """Open a binary file for reading"""
    if isinstance(path, CustomPath):
        return path.open()
    else:
        return open(path, "rb")

def file_open_text(path, encoding = "utf-8", errors = None, newline = None):
    """Open a text file for reading"""
    if isinstance(path, CustomPath):
        return path.open_text(encoding, errors, newline)
    else:
        return open(path, "r", encoding=encoding, errors=errors, newline=newline)

def file_open_maybe_text(path, encoding = "utf-8", newline = "\n"):
    return file_open_text(path, encoding, "surrogateescape", newline)

def file_create(path):
    """Create or replace a binary file for writing"""
    if isinstance(path, CustomPath):
        return path.create()
    else:
        return open(path, "wb")

def file_create_text(path, encoding = "utf-8", errors = None, newline = "\n"):
    """Create or replace a text file for writing"""
    if isinstance(path, CustomPath):
        return path.create_text(encoding, errors, newline)
    else:
        return open(path, "w", encoding=encoding, errors=errors, newline=newline)

def file_create_maybe_text(path, encoding = "utf-8", newline = "\n"):
    return file_create_text(path, encoding, "surrogateescape", newline)

def file_read(path, offset = 0, size = None):
    """Read all data from a binary file (or optionally, a subset of data)"""
    with file_open(path) as f:
        if offset:
            f.seek(offset, 0)
        if size:
            return f.read(size)
        else:
            return f.read()
        
def file_read_text(path, encoding = "utf-8", errors = None, newline = None):
    """Read all text from a text file"""
    with file_open_text(path, encoding, errors, newline) as f:
        return f.read()
        
def file_read_maybe_text(path, encoding = "utf-8", newline = None):
    return file_read_text(path, encoding, "surrogateescape", newline)

def file_read_json(path, **json_kwargs):
    """Read data from a json file"""
    with file_open_text(path) as f:
        return json.load(f, **json_kwargs)

def file_write(path, value):
    """Create or replace a binary file, writing 'value' into it"""
    with file_create(path) as f:
        f.write(value)
        
def file_write_text(path, value, encoding = "utf-8", errors = None, newline = "\n"):
    """Create or replace a text file, writing 'value' into it"""
    with file_create_text(path, encoding, errors, newline) as f:
        f.write(value)
        
def file_write_maybe_text(path, value, encoding = "utf-8", newline = "\n"):
    file_write_text(path, value, encoding, "surrogateescape", newline)

def file_write_json(path, value, **json_kwargs):
    """Create or replace a json file, writing 'data' into it"""
    with file_create_text(path) as f:
        json.dump(value, f, **json_kwargs)

def try_file_read(path, defval = None):
    """Try reading all data from a binary file, or return 'defval' on any error"""
    try:
        return file_read(path)
    except Exception:
        return defval

def try_file_read_text(path, defval = None, encoding = "utf-8", errors = None, newline = None):
    """Try reading all text from a text file, or return 'defval' on any error"""
    try:
        return file_read_text(path, encoding, errors, newline)
    except Exception:
        return defval

def try_file_read_maybe_text(path, defval = None, encoding = "utf-8", newline = None):
    return try_file_read_text(path, defval, encoding, "surrogateescape", newline)

def try_file_read_json(path, defval = None, **json_kwargs):
    """Try reading data from a json file, or return 'defval' on any error"""
    try:
        return file_read_json(path, **json_kwargs)
    except Exception:
        return defval

def try_file_write(path, value):
    """Try creating or replacing a binary file, writing 'value' into it. Return if succeeded"""
    try:
        file_write(path, value)
        return True
    except Exception:
        return False

def try_file_write_text(path, value, encoding = "utf-8", errors = None, newline = "\n"):
    """Try creating or replacing a text file, writing 'value' into it. Return if succeeded"""
    try:
        file_write_text(path, value, encoding, errors, newline)
        return True
    except Exception:
        return False

def try_file_write_maybe_text(path, value, encoding = "utf-8", newline = None):
    return try_file_write_text(path, value, encoding, "surrogateescape", newline)

def try_file_write_json(path, value, **json_kwargs):
    """Try creating or replacing a json file, writing 'value' into it. Return if succeeded"""
    try:
        file_write_json(path, value, **json_kwargs)
        return True
    except Exception:
        return False

def file_delete(path):
    """Delete a file if it exists"""
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        return False

file_delete_if_needed = file_delete # old name

def file_temp():
    """Create a temporary file (no auto-deletion)"""
    result = tempfile.NamedTemporaryFile(delete=False)
    result.close()
    return result.name

path_split_name = os.path.split
path_basename = os.path.basename
path_dirname = os.path.dirname
path_absolute = os.path.abspath
path_split_extension = os.path.splitext
path_resolve = os.path.realpath # fully canonicalizes (& normalizes) a path

def path_extension(path):
    """Return the extension of a path"""
    return os.path.splitext(path)[1]

def path_no_extension(path):
    """Return the path without an extension"""
    return os.path.splitext(path)[0]

def path_basename_no_extension(path):
    """Return the basename of the path without an extension"""
    return path_no_extension(path_basename(path))

def path_split_comps(path):
    """Split the path to its components(dir/basenames)"""
    comps = []
    while True:
        path, comp = path_split_name(path)
        if comp:
            comps.append(comp)
        elif path:
            comps.append(path)
        else:
            break
    comps.reverse()
    return comps

def path_relative(path, base=None, fallback=True):
    try:
        return os.path.relpath(path, base)
    except ValueError:
        if fallback:
            return path
        else:
            raise

def path_is_inside(path, base):
    try:
        relpath = path_relative(path, base, fallback=False)
        if relpath == ".." or relpath.startswith(".." + os.sep):
            return False
        return True
    except ValueError:
        return False

def path_modify_time(path):
    """Return the modify time of the file/directory at the given path"""
    return datetime.fromtimestamp(os.path.getmtime(path))

path_join = os.path.join
path_is_absolute = os.path.isabs
path_exists = os.path.exists
path_is_dir = os.path.isdir
path_is_file = os.path.isfile

def path_ensure_dir_exists(path):
    """If the directory of 'path' doesn't exist, create it"""
    dir_ensure_exists(path_dirname(path))

def dir_ensure_exists(path):
    """If the directory 'path' doesn't exist, create it"""
    try:
        os.makedirs(path)
    except FileExistsError:
        pass
    
dir_create_if_needed = dir_ensure_exists # old name

def dir_names(path):
    """Return the names of the contents of the directory"""
    return os.listdir(path)

def dir_paths(path):
    """Return the full paths of the contents of the directory"""
    return (path_join(path, file) for file in dir_names(path))

dir_get_current = os.getcwd
dir_set_current = os.chdir

def try_dir_names(path, defval = None):
    """Try returning the names of the contents of the directory"""
    try:
        return dir_names(path)
    except Exception:
        return defval

def try_dir_paths(path, defval = None):
    """Try returning the full paths of the contents of the directory"""
    try:
        return dir_paths(path)
    except Exception:
        return defval

def filename_fixup(filename):
    """Fixup a filename to be valid"""
    fixed = "".join([ch if ch not in r"\/:*?<>|" else "_" for ch in filename])
    if not fixed or fixed.endswith("."):
        fixed += "_"
    return fixed

def try_cast(value, ctor, defval=None):
    """Try converting 'value' via constructor 'ctor', return 'defval' on failure"""
    try:
        return ctor(value)
    except ValueError:
        return defval

def maybe_int(value, defval=None, base=10):
    """Try converting 'value' to an int, return 'defval' on failure"""
    if value is None:
        return defval
    try:
        return int(value, base)
    except ValueError:
        return defval
    
def maybe_float(value, defval=None, base=10):
    """Try converting 'value' to a float, return 'defval' on failure"""
    if value is None:
        return defval
    try:
        if base == 0:
            base = 16 if value.lower().startswith("0x") else 10

        if base == 10:
            return float(value)
        elif base == 16:
            return float.fromhex(value)
        else:
            return defval
    except ValueError:
        return defval

def maybe_num(value, defval=None, base=10):
    """Try converting 'value' to an int or float, return 'defval' on failure"""
    result = maybe_int(value, base=base)
    if result is None:
        result = maybe_float(value, base=base)
    if result is None:
        result = defval
    return result

def count_significant_bits(a):
    """Return how many significant bits (all but leading zero bits) 'a' has"""
    assert a >= 0
    return a.bit_length()

def count_leading_zero_bits(a, bits):
    """Return how many leading zero bits 'a' has, counting from 'bits'"""
    assert a >= 0
    return bits - a.bit_length()

def count_trailing_zero_bits(a):
    """Return how many trailing zero bits 'a' has"""
    assert a >= 0
    count = 0
    while not (a & 0xff):
        count += 8
        a >>= 8
    while not (a & 0x1):
        count += 1
        a >>= 1
    return count

def make_mask(pos, size):
    """Create a mask with 'size' ones at bit 'pos'"""
    return ((1 << size) - 1) << pos
    
def is_pow2(a):
    """Return if 'a' is a power of 2"""
    return a > 0 and (a & (a - 1)) == 0

def div_up(a, b):
    """Divide 'a' by 'b', rounding up"""
    r, m = divmod(a, b)
    return r + 1 if m else r

def quotrem(a, b):
    """Return the quotient and remainder of dividing 'a' by 'b'"""
    q, r = divmod(a, b)
    if q < 0 and r != 0:
        q += 1
        r -= b
    return q, r

def quot(a, b):
    """Return the quotient of dividing 'a' by 'b'"""
    return quotrem(a, b)[0]

def rem(a, b):
    """Return the remainder of dividing 'a' by 'b'"""
    return quotrem(a, b)[1]

def round_down(a, b):
    """Round 'a' down by 'b'"""
    m = a % b
    return a - m if m else a

def round_up(a, b):
    """Round 'a' up by 'b'"""
    assert b > 0
    m = a % b
    return a + (b - m) if m else a

def round_up_pow2(a):
    """Round 'a' up to its next power of 2"""
    assert a > 0
    return 1 << (a - 1).bit_length()

def sqr(value):
    """Square 'value'"""
    return value * value

def clamp(value, minval, maxval):
    """Return 'value' clamped between 'minval' and 'maxval'"""
    return minval if value < minval else maxval if value > maxval else value

bound = clamp # old/dup name

def lerp(start, end, portion):
    """Return the linear interpolation between 'start' and 'end'"""
    return start + portion * (end - start)

def rotate_left(value, count, bits):
    """Rotate 'value' left by 'count' bits, across 'bits' bits"""
    assert value >= 0
    count %= bits
    return ((value << count) | (value >> (bits - count))) & make_mask(0, bits)

def rotate_right(value, count, bits):
    """Rotate 'value' right by 'count' bits, across 'bits' bits"""
    assert value >= 0
    count %= bits
    return ((value >> count) | (value << (bits - count))) & make_mask(0, bits)

def closure(__func, *args, **kwargs):
    """Create a lambda that applies the given arguments to 'func'"""
    return lambda: __func(*args, **kwargs)

def debug(*msg):
    """Print a message only if debugging is enabled"""
    if debug.enabled:
        print(*msg)
    
debug.enabled = False
    
def warn_assert(cond, msg):
    """Warn if 'cond' is false"""
    if not cond:
        warn(msg)
    return cond

def fail(msg=None):
    """Fail, optionally with message"""
    assert False, msg

class CheckError(Exception):
    """An error meant to be caught and displayed as-is, like AssertionError but for user errors"""

def check(cond, msg):
    """If condition doesn't hold, raise CheckError"""
    if not cond:
        raise CheckError(msg)

def throw(msg):
    """Unconditionally raise CheckError"""
    raise CheckError(msg)

def desc(value):
    """Set a description (desc attr) of the given function"""
    def decorator(f):
        f.desc = value
        return f
    return decorator

def trace(*args):
    """Print with traceback"""
    print(*args)
    traceback.print_stack()
    
def byte(x):
    """Return bytes from a single byte"""
    return bytes((x,))
    
def measure_execution_time(func):
    """Decorator to measure execution time of a function"""
    def decorator(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func} took {end - start:f} seconds")
        return result
    return decorator
    