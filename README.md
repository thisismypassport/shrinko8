# timp_p8_tools

The supported tools are:
* [Minification](#minification) - Reduce the character count and compression ratio of your cart.
* [Linting](#linting) - Check for common code errors such as forgetting to declare a local.
* [Getting Cart Size](#getting-cart-size) - Count the amount of tokens, characters, and compressed bytes your cart uses.
* [Format Conversion](#format-conversion) - Convert between p8 and png files, often with slightly better compression than Pico-8.

Requires [Python](https://www.python.org/) 3.8 or above to run.

[Download the latest version.](https://github.com/thisismypassport/timp_p8_tools/archive/refs/heads/main.zip)

# Minification

Greatly reduces the character count of your cart, as well as greatly improves its compression ratio (so that its compressed size is smaller).

Note: it doesn't affect token count. (Might be added in the future)

## To minify your p8 cart:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify`

If you just want the lua source without the rest of the baggage (except the `__lua__` header line):

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --format code`

If you want to create a png cart:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --format png`

This tool often compresses a bit better than Pico-8. (caveat - if your *code* contains pre-compressed strings, this tool will currently give worse compression)

## Automatic renaming of identifiers

The minifier renames all locals, globals, and table member accesses to minimize character count and compressed size.

This means that if you have a table member (or global) you access both as an identifier and as a string, you'll need to take one of the two approaches below to fix this, or your minified cart won't work

E.g:
```
local my_key = "key" -- here, key is a string
local my_obj = {key=123} -- here, key is an identifier
?my_obj[my_key] -- BUG! my_obj will not have a "key" member after minification
```

### Renaming strings (recommended, results in smaller carts)

You can add a `--[[member]]` comment before a string to have the minifier rename it as if it were an identifier.

E.g:
```
local my_key = --[[member]]"key" -- here, key is a string but is renamed as if it were an identifier
local my_obj = {key=123} -- here, key is an identifier
?my_obj[my_key] -- success, result is 123 after minification
```

You can also use this with multiple keys split by comma:
```
local my_keys = split --[[member]]"key1,key2,key3"
```

And you can similarly use `--[[global]]` for globals:
```
local my_key = --[[global]]"glob"
glob = 123
?_ENV[my_key] -- 123
```

For more advanced usecases, see the [below section](#advanced---controlling-renaming-of-identifiers).

### Preserving identifiers across the entire cart

You can instruct the minifier to preserve certain identifiers across the entire cart:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --preserve 'my_global_1,my_global_2,*.my_member,my_env.*'`

* my_global_1 and my_global_2 will not be renamed when used as globals
* my_member will not be renamed when used as a table member
* table members will not be renamed when accessed through my_env

You can also choose to preserve *all* table members, which allows freely accessing all tables through strings or through identifiers, if you prefer:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --preserve '*.*'`

## Advanced - Controlling renaming of identifiers

The `--[[global]]` and `--[[member]]` hints can also be used on identifiers to change the way they're renamed.

In additon, the `--[[preserve]]` hint can prevent identifiers from being renamed at all:
```
do
  local _ENV = {--[[global]]assert=assert}
  assert(true)
end
for _ENV in all({{x=1}, {x=2}}) do
  --[[member]]x += 1
end
--[[preserve]]some_future_pico8_api(1,2,3)
```

Additionally, you can use `--[[preserve-keys]]`, `--[[global-keys]]` and `--[[member-keys]]` to affect how *all* keys of a table are renamed.

This can be applied on either table constructors (aka `{...}`) or on variables. When applying on variables, the hint affects all members accessed through that variable, as well as any table constructors directly assigned to it.
```
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

## Advanced - Renaming Built-in Pico-8 functions

For cases like tweet-carts where you want really few characters, you can minify the names of built-in pico-8 functions while still using their original name as follows:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --no-preserve 'circfill,rectfill'`

```
circfill, rectfill = --[[preserve]]circfill, --[[preserve]]rectfill
circfill(10,10,20); circfill(90,90,30)
rectfill(0,0,100,100); rectfill(20,20,40,40)
```

Here, all uses of circfill and rectfill are renamed unless they're preceded by `--[[preserve]]`

Be aware that doing this won't reduce the compressed size of the cart, and will increases the token count (due to the assignment), so it's of limited use, for when you care about character count above all else.

## Options

You can disable parts of the minification process via additional command-line options:

```
--no-minify-rename
--no-minify-spaces
--no-minify-lines
```

## Keeping comments

You can keep specific comments in the output via:

```
--keep: This is a comment to keep
-- But this comment is gone after minify
```

Currently, all kept comments are placed at the start of the file, however.

# Linting

Linting finds common code issues in your cart, like forgetting to use a 'local' statement

## To lint your p8 cart:

`python timp_p8_tools.py path-to-input.p8 --lint`

You can combine linting with other operations:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --lint --count --minify`

## Options

You can disable certain lints globally via additional command-line options:

```
--no-lint-unused
--no-lint-duplicate
--no-lint-undefined
```

Normally, a lint failure prevents cart creation, but `--no-lint-fail` overrides that.

## Undefined variable lints

To tell the linter to ignore globals it didn't see you define:

```
--lint: global_1, global_2
function f()
    dostuff(global_1, global_2)
end
```

The linter normally allows you to define variables in the global scope or in the _init function, but you can extend this to other functions like this:

```
--lint: func::_init
function my_init()
    global_1, global_2 = 1, 2 -- these globals can be used anywhere now that they're assigned to here
end
```

## Unused variable lints

The linter allows unused variables if their names starts with underscore (e.g. `_my_unused`).

The linter checks both locals and the last function parameter of every function if it unused.

## Duplicate variable lints

The linter checks for duplicate locals in the same or inner scope (even across functions)

The linter allows duplicate variables named `_`, though

# Getting Cart Size

You can enable printing the number of tokens, characters, and compressed bytes used by the code in the cart (including percentages):

`python timp_p8_tools.py path-to-input.p8 --count`

E.g may print:

```
tokens: 8053 98%
chars: 30320 46%
compressed: 12176 77%
```

Note that the compressed size is how this tool would compress this cart, which is often a bit better than Pico-8.

You can combine counting with other operations, in which case the counts are of the output cart, not the input cart:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --lint --count --minify`

# Format Conversion

By specifying `--format <p8/code/png>` you can control the format of the output cart, e.g:

`python timp_p8_tools.py path-to-input.p8 path-to-output.png --format png`

This allows converting png carts to p8 carts, and p8 carts to png carts - potentially in tandem with other operations.
