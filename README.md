# timp_p8_tools
p8 tools (e.g minify)

# minification

## To minify your p8 cart:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify`

## If you just want the lua source without the rest of the baggage (except the "__lua__" header line):

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --format code`

## Identifier renaming

The minifier renames all locals, globals, and table member accesses to minimize character count and compressed size.

This means that if you have a table member (or global) you access both as an identifier and as a string, you'll need to take one of the two approaches below to fix this, or your minified cart won't work

E.g:
```
local my_key = "key" -- here, key is a string
local my_obj = {key=123} -- here, key is an identifier
?my_obj[my_key] -- BUG! my_obj will not have a "key" member after minification
```

### Renaming strings (recommended, results in smaller carts)

You can add a `--[[memberof]]` comment before a string to have the minifier rename it as if it were an identifier.

E.g:
```
local my_key = --[[memberof]]"key" -- here, key is a string but is renamed as if it were an identifier
local my_obj = {key=123} -- here, key is an identifier
?my_obj[my_key] -- success, result is 123 after minification
```

You can also use this with multiple keys split by comma:
```
local my_keys = split --[[memberof]]"key1,key2,key3"
```

And you can similarly use `--[[nameof]]` for globals:
```
local my_key = --[[nameof]]"glob"
glob = 123
?_ENV[my_key] -- 123
```

### Preserving identifiers

You can instruct the minifier to preserve certain identifiers:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --preserve 'my_global_1,my_global_2,*.my_member,my_env.*'`

* my_global_1 and my_global_2 will not be renamed when used as globals
* my_member will not be renamed when used as a table member
* table members will not be renamed when accessed through my_env

# other stuff?

You can lint and count tokens

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --lint --count --minify`

The lint is all-or-nothing right now.

To tell it to ignore globals it didn't find you define:

```
--lint: global_1, global_2
function f()
    dostuff(global_1, global_2)
end
```

It complains about unused variables not named `"_"`, as well as about the last function parameter if it is unused and not named `"_"` (this should be revised)
