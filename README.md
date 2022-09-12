# Shrinko8

A set of Pico-8 cart tools, with a focus on shrinking code size.

The supported tools are:
* [Minification](#minification) - Reduce the token count, character count and compression ratio of your cart.
* [Linting](#linting) - Check for common code errors such as forgetting to declare a local.
* [Getting Cart Size](#getting-cart-size) - Count the amount of tokens, characters, and compressed bytes your cart uses.
* [Format Conversion](#format-conversion) - Convert between p8 and png files. Achieves slightly better code compression than Pico-8's.
* [Custom Python Script](#custom-python-script) - Run a custom python script to preprocess or postprocess your cart

Requires [Python](https://www.python.org/) 3.7 or above to run.

Reading/Writing PNGs additionally requires the Pillow module (`python -m pip install pillow` to install)

[Download the latest version here.](https://github.com/thisismypassport/shrinko8/archive/refs/heads/main.zip)

# Minification

Greatly reduces the character count of your cart, as well as greatly improves its compression ratio (so that its compressed size is smaller) and can reduce the number of tokens as well.

In detail:
* All unnecessary spaces and line breaks are removed
* Unnecessary tokens like parentheses and trailing commas are removed
* Identifiers are renamed to be as short as possible
* Tokens are made more consistent, to reduce compression ratio

## To minify your p8 cart:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --minify`

If you just want the lua source without the rest of the baggage, change the output extension to .lua:

`python shrinko8.py path-to-input.p8 path-to-output.lua --minify`

If you want to create a png cart, change the output extension to .png:

`python shrinko8.py path-to-input.p8 path-to-output.png --minify`

Shrinko8 compresses code a bit better than Pico-8.

## Automatic renaming of identifiers

The minifier renames all locals, globals, and table member accesses to minimize character count and compressed size.

This means that if you have a table member (or global) you access both as an identifier and as a string, you'll need to take one of the two approaches below to fix this, or your minified cart won't work

E.g:
```lua
local my_key = "key" -- here, key is a string
local my_obj = {key=123} -- here, key is an identifier
?my_obj[my_key] -- BUG! my_obj will not have a "key" member after minification
```

### Renaming strings (recommended, results in smaller carts)

You can add a `--[[member]]` comment before a string to have the minifier rename it as if it were an identifier.

E.g:
```lua
local my_key = --[[member]]"key" -- here, key is a string but is renamed as if it were an identifier
local my_obj = {key=123} -- here, key is an identifier
?my_obj[my_key] -- success, result is 123 after minification
```

You can also use this with multiple keys split by comma:
```lua
local my_keys = split --[[member]]"key1,key2,key3"
```

And you can similarly use `--[[global]]` for globals:
```lua
local my_key = --[[global]]"glob"
glob = 123
?_ENV[my_key] -- 123
```

### Preserving identifiers across the entire cart

You can instruct the minifier to preserve certain identifiers across the entire cart:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --minify --preserve "my_global_1,my_global_2,*.my_member,my_env.*"`

* my_global_1 and my_global_2 will not be renamed when used as globals
* my_member will not be renamed when used as a table member
* table members will not be renamed when accessed through my_env

You can also choose to preserve *all* table members, which allows freely accessing all tables through strings or through identifiers, if you prefer:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --minify --preserve "*.*"`

## Advanced renaming requirements

While the above is enough for simpler carts, there are some advanced usecases with more complex requirements:

* If you have a string in some special format that you're parsing into a table (like "key=val,key2=val2"), you can use [this custom python script](#example---simple-sub-language-for-table-parsing) - or a variant thereof - to allow the keys within the string to be renamed.

* If you have certain tables whose keys you don't want to rename - e.g. because the keys are built at runtime by concatenating strings, or because the tables are serialized to a savefile - you can [preserve all keys in a table](#advanced---controlling-renaming-of-all-keys-of-a-table).

* If you're making your tables inherit _ENV (allowing you to bind the table to _ENV and access both table members and globals without a '.'), you can use `--rename-members-as-globals` in order to rename table members and globals the same way.

* If you're doing other unusual things with _ENV, you may need to [specify how specific identifiers should be renamed](#advanced---controlling-renaming-of-identifiers) to get correct behaviour.

In all these cases, you can start by disabling all renaming (`--no-minify-rename`) or all member renaming (`--preserve "*.*"`) to get things to work and then look into the more complicated solutions to increase compression rate.

### Advanced - Controlling renaming of identifiers

The `--[[global]]` and `--[[member]]` hints can also be used on identifiers to change the way they're renamed.

In additon, the `--[[preserve]]` hint can prevent identifiers from being renamed at all:
```lua
do
  local _ENV = {--[[global]]assert=assert}
  assert(true)
end
for _ENV in all({{x=1}, {x=2}}) do
  --[[member]]x += 1
end
--[[preserve]]some_future_pico8_api(1,2,3)
```

Note that this affects only a specific usage of an identifier. If you want to rename all usages of a global, `--preserve` is the recommended approach.

### Advanced - Controlling renaming of all keys of a table

Additionally, you can use `--[[preserve-keys]]`, `--[[global-keys]]` and `--[[member-keys]]` to affect how *all* keys of a table are renamed.

This can be applied on either table constructors (aka `{...}`) or on variables. When applying on variables, the hint affects all members accessed through that variable, as well as any table constructors directly assigned to it.
```lua
local --[[preserve-keys]]my_table = {preserved1=1, preserved2=2}
my_table.preserved1 += 1 -- all member accesses through my_table are preserved
?my_table["preserved1"]

-- here, {preserved3=3} is not directly assigned to my_table and so needs its own hint
my_table = setmetatable(--[[preserve-keys]]{preserved3=3}, my_meta)
?my_table["preserved3"]

do
  local _ENV = --[[global-keys]]{assert=assert, add=add}
  assert(add({}, 1) == 1)
end

for --[[member-keys]]_ENV in all({{x=1,y=5}, {x=2,y=6}}) do
  x += y + y*x
end
```

### Advanced - Renaming Built-in Pico-8 functions

For cases like tweet-carts where you want really few characters, you can minify the names of built-in pico-8 functions while still using their original name as follows:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --minify --no-preserve "circfill,rectfill"`

```lua
circfill, rectfill = --[[preserve]]circfill, --[[preserve]]rectfill
circfill(10,10,20); circfill(90,90,30)
rectfill(0,0,100,100); rectfill(20,20,40,40)
```

Here, all uses of circfill and rectfill are renamed unless they're preceded by `--[[preserve]]`

Be aware that doing this won't reduce the compressed size of the cart, and will increases the token count (due to the assignment), so it's of limited use, for when you care about character count above all else.

## Options

You can disable parts of the minification process via additional command-line options:

* `--no-minify-rename` : Disable all renaming of identifiers
* `--no-minify-spaces` : Disable removal of spaces (and line breaks)
* `--no-minify-lines` : Disable removal of line breaks
* `--no-minify-comments` : Disable removal of comments (requires `--no-minify-spaces`)
* `--no-minify-tokens` : Disable removal and alteration of tokens (not including identifier renaming)

You can configure how identifier renaming is done:

* `--rename-members-as-globals` : Rename members (table keys) and globals the same way, useful when tables inherit from _ENV.
* `--preserve` : Described [here](#preserving-identifiers-across-the-entire-cart)
* `--no-preserve` : Described [here](#advanced---renaming-built-in-pico-8-functions)

You can also generate a file telling you how the identifiers were renamed: (This can be useful for debugging and more) 

* `--rename-map <file>`

## Keeping comments

You can keep specific comments in the output via:

```lua
--keep: This is a comment to keep
-- But this comment is gone after minify
```

Currently, all kept comments are placed at the start of the file, however.

# Linting

Linting finds common code issues in your cart, like forgetting to use a 'local' statement

## To lint your p8 cart:

`python shrinko8.py path-to-input.p8 --lint`

You can combine linting with other operations:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --lint --count --minify`

## Options

You can disable certain lints globally via additional command-line options:

* `--no-lint-unused` : Disable lint on unused variables
* `--no-lint-duplicate` : Disable lint on duplicate variable names
* `--no-lint-undefined` : Disable lint on undefined variables

Normally, a lint failure prevents cart creation, but `--no-lint-fail` overrides that.

## Undefined variable lints

In Pico-8 (and lua in general), variables that aren't explicitly declared as local (via a `local` statement) are implicitly global. This can cause all sorts of bugs and headaches if you typo the name of a local or forget to declare a local.

This lint alerts you when you're accessing a variable that wasn't declared as local and isn't a known global variable, e.g:
```lua
function f()
    x, y = 10, 20 -- lint warning: you probably meant to use 'local' here instead of assigning to global variables.
    while x < y do stuff(x, y) end
end
```

### Defining global variables

The linter normally allows you to define global variables in the global scope or in the _init function. If you don't, your options are either:

Tell the linter about the globals it didn't see you define via the `--lint` hint:
```lua
--lint: global_1, global_2
function f()
    dostuff(global_1, global_2)
end
```

Tell the linter to allow you to define globals (by assigning to them) in a specific function via the `--lint func::_init` hint:
```lua
--lint: func::_init
function my_init()
    global_1, global_2 = 1, 2 -- these globals can be used anywhere now that they're assigned here
end
```

### Re-assigning built-in globals

Similarly, to protect against accidental use of built-in globals like `run` or `t`, the linter only allows you to assign to built-in globals in the global scope or in an _init function:
```lua
function f()
    t = func() -- lint warning: you probably meant to use 'local' here, even though t is a built-in global
end
```

If you do want to reassign some built-in global anywhere, you can use `--lint`:
```lua
--lint: print
function f()
    local old_print = print
    print = function() end
    call_something()
    print = old_print
end
```

## Unused variable lints

This lint alerts you when you've declared a local but never used it, which is usually a mistake.

It also tells you when the *last* parameter of a function is unused, as that's either a mistake or a waste of a token.

To tell the linter that some specific local is OK to be unused, named it beginning with underscore (e.g. `_` or `_some_name`). E.g:
```lua
do
  local _, _, x, y = get_stuff() -- lint warning about y (but not about _) - you probably meant to pass it to do_stuff
  do_stuff(x, x)
end
```

## Duplicate variable lints

This lint alerts you when you declare a local with the same name as a local in a parent scope (even across functions).

This can cause confusion and bugs since you can accidentally use the wrong local. E.g:
```lua
function f()
  for i=1,10 do
    do_stuff(i)
    for i=1,5 do -- lint warning about i
      do_more(i)
    end
  end
end
```

The linter allows duplicate variables if they're all named `_`:
```lua
local _, _, x, y, _, z = stuff()
```

# Getting Cart Size

You can enable printing the number of tokens, characters, and compressed bytes used by the code in the cart (including percentages):

`python shrinko8.py path-to-input.p8 --count`

E.g may print:

```
tokens: 8053 98%
chars: 30320 46%
compressed: 12176 77%
```

Note that the compressed size is how *this* tool would compress the code, which is slightly better than how Pico-8 would.

You can combine counting with other operations, in which case the counts are of the output cart, not the input cart:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --lint --count --minify`

In such cases, you can also use `--input-count` to count the number of tokens, characters, and compressed bytes (if applicable) of the input cart.

# Format Conversion

Shrinko8 supports multiple cart formats, and allows converting between them:
* p8 - Pico-8 cart source
* png - Pico-8 cart exported into a png
* rom - Pico-8 cart exported into a rom
* tiny-rom - Pico-8 cart exported into a tiny rom (code only)
* lua - raw lua code, with no headers
* clip - Pico-8 clipboard format (i.e. [cart]...[/cart])
* url - Pico-8 education version url (code & gfx only)
* auto - try to determine automatically from content

E.g:
```
python shrinko8.py path-to-input.p8 path-to-output.png
python shrinko8.py path-to-input.png path-to-output.rom
python shrinko8.py path-to-input.rom path-to-output.lua
```

By default, the format is determined by the file extension, but you can specify it explicitly via:
* `--input-format <format>` for the input format.
* `--format <format>` for the output format
(Where `<format>` is one of the formats listed above)

You can combine conversion with other operations:

`python shrinko8.py path-to-input.p8 path-to-output.rom --count --lint --minify`

Specifying the format is also useful when using the standard input/output (via `-`), e.g.:

`python shrinko8.py path-to-input.p8 - --minify --format lua` (This prints minified lua to stdout)

# Custom Python Script

For advanced usecases, you can create a python script that will be called to preprocess or postprocess the cart before/after the other steps.

This can be used for:
* Merging in code and data (from other carts, or data files, etc.)
* Saving minor variations of the cart.
* Likely much more.

To run, use `--script <path>`, here shown together with other tools:

`python shrinko8.py path-to-input.p8 path-to-output.png --count --lint --minify --script path-to-script.py`

You can also pass arguments to your script by putting them after `--script-args`:

`python shrinko8.py path-to-input.p8 path-to-output.png --count --lint --minify --script path-to-script.py --script-args my-script-arg --my-script-opt 123`

Example python script showing the API and various capabilities:
```python
# this is called after your cart is read but before any processing is done on it:
def preprocess_main(cart, args, **_):
    print("hello from preprocess_main!")

    # 'cart' contains 'code' and 'rom' attributes that can be used to read or modify it
    # 'cart.code' is just a string
    # 'cart.rom' is a bytearray with some extra APIs like get16/set32/etc (see Memory in pico_defs.py)

    # copy the spritesheet from another cart
    from pico_cart import read_cart
    other_cart = read_cart("test.p8") # can be used to read p8 or png carts
    cart.rom[0x0000:0x2000] = other_cart.rom[0x0000:0x2000]

    # encode binary data into a string in our cart
    # our cart's code should contain a string like so: "$$DATA$$"
    from pico_utils import bytes_to_string_contents
    with open("binary.dat", "rb") as f:
        cart.code = cart.code.replace("$$DATA$$", bytes_to_string_contents(f.read()))

    # args.script_args contains any arguments sent to this script
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("arg", help="first arg sent to script", nargs="?")
    parser.add_argument("--my-script-opt", type=int, help="option sent to script")
    opts = parser.parse_args(args.script_args)
    print("Received args:", opts.arg, opts.my_script_opt)

# this is called before your cart is written, after it was fully processed
def postprocess_main(cart, **_):
    print("hello from postprocess_main!")

    # write a new cart with the same code but zeroed spritesheet, in both p8 and png formats
    from pico_cart import write_cart, CartFormat
    new_cart = cart.copy()
    new_cart.rom[0x0000:0x2000] = bytearray(0x2000) # zero it out
    write_cart("new_cart.p8", new_cart, CartFormat.p8)
    write_cart("new_cart.p8.png", new_cart, CartFormat.png)
```
## Advanced - custom sub-language

For **really** advanced usecases, if you're embedding a custom language inside the strings of your pico-8 code, you can let Shrinko8 know how to lint & minify it.

E.g. this allows renaming identifiers shared by both the pico-8 code and the custom language.

Mark the language with `--[[language::<name>]]` in the code:
```lua
eval(--[[language::evally]][[
    circfill 50 50 20 7
    my_global_var <- pack
    rawset my_global_var .some_member 123
    rawset my_global_var .another_member 456
]])
```

In the python script, provide a class that handles the language via sublanguage_main:

(This is a complete example of what sublanguages can do, you can find a simpler example [below](#Example---simple-sub-language-for-table-parsing)
```python
from pico_process import SubLanguageBase, is_identifier
from collections import Counter

class MySubLanguage(SubLanguageBase):
    # NOTE: all members are optional.

    # called to parse the sub-language from a string
    # (strings consist of raw pico-8 chars ('\0' to '\xff') - not real unicode)
    def __init__(self, str, on_error, **_):
        # our trivial language consists of space-separated tokens in newline-separated statements
        self.stmts = [stmt.split() for stmt in str.splitlines()]
        # we can report parsing errors:
        #on_error("Example")

    # these are utility functions for our own use:

    def is_global(self, token):
        # is the token a global in our language? e.g. sin / rectfill / g_my_global
        return is_identifier(token)

    def is_member(self, token):
        # is the token a member in our language? e.g. .my_member / .x
        return token.startswith(".") and self.is_global(token[1:])
        
    # for --lint:

    # called to get globals defined within the sub-language's code
    def get_defined_globals(self, **_):
        for stmt in self.stmts:
            if len(stmt) > 1 and stmt[1] == "<-": # our lang's assignment token
                yield stmt[0]

    # called to lint the sub-language's code
    def lint(self, builtins, globals, on_error, **_):
        for stmt in self.stmts:
            for token in stmt:
                if self.is_global(token) and token not in builtins and token not in globals:
                    on_error("Identifier '%s' not found" % token)
        # could do custom lints too

    # for --minify:

    # called to get all characters that won't get removed or renamed by the minifier
    # (aka, all characters other than whitespace and identifiers)
    # this is optional and doesn't affect correctness, but can slightly improve compressed size
    def get_unminified_chars(self, **_):
        for stmt in self.stmts:
            for token in stmt:
                if not self.is_global(token) and not self.is_member(token):
                    yield from token

    # called to get all uses of globals in the language's code
    def get_global_usages(self, **_):
        usages = Counter()
        for stmt in self.stmts:
            for token in stmt:
                if self.is_global(token):
                    usages[token] += 1
        return usages
        
    # called to get all uses of members (table keys) in the language's code
    def get_member_usages(self, **_):
        usages = Counter()
        for stmt in self.stmts:
            for token in stmt:
                if self.is_member(token):
                    usages[token[1:]] += 1
        return usages

    # for very advanced languages only, see test_input/sublang.py for details
    # def get_local_usages(self, **_):

    # called to rename all uses of globals/members/etc
    def rename(self, globals, members, **_):
        for stmt in self.stmts:
            for i, token in enumerate(stmt):
                if self.is_global(token) and token in globals:
                    stmt[i] = globals[token]
                elif self.is_member(token) and token[1:] in members:
                    stmt[i] = members[token[1:]]

    # called (after rename) to return a minified string
    def minify(self, **_):
        return "\n".join(" ".join(stmt) for stmt in self.stmts)

# this is called to get a sub-language class by name
def sublanguage_main(lang, **_):
    if lang == "evally":
        return MySubLanguage
```

### Example - simple sub-language for table parsing

Often it's useful in pico-8 to define a simple sub-language to parse something like this:

`"key1=val1,key2=val2,val3,val4"`

To:

`{key1="val1",key2="val2","val3","val4"}`

Here, to minify properly, the keys (key1/key2) should be renamed as members, while the values should be left alone.

The custom python script:
```python
from pico_process import SubLanguageBase
from collections import Counter

class SplitKeysSubLang(SubLanguageBase):
    # parses the string
    def __init__(self, str, **_):
        self.data = [item.split("=") for item in str.split(",")]

    # counts usage of keys
    # (returned keys are ignored if they're not identifiers)
    def get_member_usages(self, **_):
        return Counter(item[0] for item in self.data if len(item) > 1)

    # renames the keys
    def rename(self, members, **_):
        for item in self.data:
            if len(item) > 1:
                item[0] = members.get(item[0], item[0])

    # formats back to string
    def minify(self, **_):
        return ",".join("=".join(item) for item in self.data)

def sublanguage_main(lang, **_):
    if lang == "splitkeys":
        return SplitKeysSubLang
```

In the code:
```lua
local table = splitkeys(--[[language::splitkeys]]"key1=val1,key2=val2,val3,val4")
?table.key1 -- "val1"
?table[1] -- "val3"
```

To run, use `--script <path>` as before.
