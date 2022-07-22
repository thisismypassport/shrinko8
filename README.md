# timp_p8_tools
p8 tools (e.g minify)

# minification

* To minify your p8 cart:

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify`

* If you just want the lua source without the rest of the baggage (except the "__lua__" header line):

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --format code`

* If you want to avoid renaming certain identifiers

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --minify --preserve 'my_global_1,my_global_2,*.my_member,my_env.*'`

-
  - my_global_1 and my_global_2 will not be renamed when used as globals
  - my_member will not be renamed when used as a table member
  - table members will not be renamed when accessed through my_env

* If you want to rename certain strings (better gains than above approach!)

```
local my_key = --[[memberof]]"key"
?{key=123}[my_key] -- 123
local my_keys = split --[[memberof]]"key1,key2,key3"
?{key2=123}[my_keys[2]] -- 123
local my_global = --[[nameof]]"glob"
_ENV[my_global] = 123
?glob -- 123
```

# other stuff?

`python timp_p8_tools.py path-to-input.p8 path-to-output.p8 --lint --count --minify`

Not too configurable right now, though.
