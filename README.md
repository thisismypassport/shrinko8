# timp_p8_tools

pico8 tools (minify, lint, etc.)

Requires a modern verison of [Python](https://www.python.org/) to run.

[Download the latest version.](https://github.com/thisismypassport/timp_p8_tools/archive/refs/heads/main.zip)

# Minification

Greatly reduces the character count of your cart, as well as greatly improves its compression ratio (so that its compressed size is smaller).

Note: it doesn't affect token count.

## To minify your p8 cart:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify`

If you just want the lua source without the rest of the baggage (except the `__lua__` header line):

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --format code`

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

These hints, together with `--[[string]]` can also be used on identifiers to change the way they're renamed:
```
do
  local _ENV = {--[[global]]assert=assert}
  assert(true)
end
for _ENV in all({{x=1}, {x=2}}) do
  --[[member]]x += 1
end
--[[string]]some_future_pico8_api(1,2,3)
```

### Preserving identifiers

You can instruct the minifier to preserve certain identifiers:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --preserve 'my_global_1,my_global_2,*.my_member,my_env.*'`

* my_global_1 and my_global_2 will not be renamed when used as globals
* my_member will not be renamed when used as a table member
* table members will not be renamed when accessed through my_env

## Renaming Pico-8 Built-in functions

For cases like tweet-carts where you want really few characters, you can minify the names of built-in pico-8 functions while still using their original name as follows:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --no-preserve 'circfill,rectfill'`

```
circfill, rectfill = --[[string]]circfill, --[[string]]rectfill
circfill(10,10,20); circfill(90,90,30)
rectfill(0,0,100,100); rectfill(20,20,40,40)
```

Here, all uses of circfill and rectfill are renamed unless they're preceded by `--[[string]]`

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

You can combine linting with other options:

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

# Token counting

You can enable printing the number of tokens in the cart (including percentage):

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --lint --count --minify`

E.g may print:

`tokens: 4159 50%`
