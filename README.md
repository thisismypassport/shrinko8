# Shrinko8

A set of Pico-8 & Picotron cart tools, with a focus on shrinking code size.

### [You can run the latest version directly in your browser here.](https://thisismypassport.github.io/shrinko8)

[You can download the latest Windows Executable here.](https://github.com/thisismypassport/shrinko8/releases/tag/latest)

Otherwise, requires [Python](https://www.python.org/) 3.8 or above to run.

Reading/Writing PNGs additionally requires the Pillow module (`python -m pip install pillow` to install)

[Download the latest version of the source here.](https://github.com/thisismypassport/shrinko8/archive/refs/heads/main.zip)

The major supported features are:
* [Minification](#minification) - Reduce the token count, character count and compression ratio of your cart.
* [Constants](#constants) - Replace constant expressions with their value. Also removes 'if' branches with a constant condition.
* [Saving Tokens via Parens-8](#saving-tokens-via-parens-8) - Use Parens-8 to replace your tokens with a string.
* [Linting](#linting) - Check for common code errors such as forgetting to declare a local.
* [Getting Cart Size](#getting-cart-size) - Count the amount of tokens, characters, and compressed bytes your cart uses.
* [Format Conversion](#format-conversion) - Convert between p8 files, pngs, and more. Achieves better code compression than Pico-8 when creating pngs.
* [Unminification](#unminification) - Add spaces and newlines to the code of a minified cart, to make it more readable.
* [Run Custom Pico8 & Python Scripts](#custom-pico8-and-python-scripts) - Run a custom pico8 or python script to preprocess or postprocess your cart.
* [Experimental Picotron support](#picotron-support) - All of the above, plus ability to manipulate Picotron carts.

# Minification

Greatly reduces the character count of your cart, as well as greatly improves its compression ratio (so that its compressed size is smaller) and can reduce the number of tokens as well.

There are command line [options](#minify-options) to choose how aggressively to minify, as well as what metric (compressed size or character count) to focus on minifying.

It's recommended to combine minification with conversion to png (as seen in the examples below), as Shrinko8 is able to compress code better and can thus fit carts into pngs that Pico-8 cannot.

If your goal is to save a larger number of tokens, you can do so via [Parens-8](#saving-tokens-via-parens-8)

## To minify your p8 cart:

You have several options, depending on how much minification you need:

The simplest approach, which gives good results and works on any cart:

`python shrinko8.py path-to-input.p8 path-to-output.png --minify-safe-only`

You can also add `--focus-tokens`, `--focus-chars`, or `--focus-compressed` to the command - depending on what you want Shrinko8 to focus on reducing.

The most aggressive approach, which gives the best results, but sometimes requires you to [give additional information to shrinko8](#pitfalls-of-full-minification) to ensure it minifies your cart correctly:

`python shrinko8.py path-to-input.p8 path-to-output.png --minify`

If you want to minify, but also to keep your cart easily debuggable and reasonably readable by others, you can do:

`python shrinko8.py path-to-input.p8 path-to-output.png --minify-safe-only --no-minify-rename --no-minify-lines`

You can also minify to a p8 file (or a lua file), e.g:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --minify-safe-only`

## Debugging the minified cart

If the minified cart errors or misbehaves, here are some tips:

* Try using `--no-minify-lines` to preserve linebreaks - the resulting cart will generate much more readable runtime errors, at only a very small character & byte cost.

* If the errors or misbehaviours don't occur without minification, do try using `--minify-safe-only`, which always produces a cart that works identically to the original (if not, that's a bug - please report).

    * If `--minify-safe-only` costs too much for you, though, read on to see [how to help Shrinko8 minify your cart correctly without safe minification](#pitfalls-of-full-minification).

## Minify options

You can specify what the minification should focus on reducing via additional command-line options:

* `--focus-tokens` : Focus on reducing the amount of tokens, even if the compressed size or amount of characters grow. Can be combined with the below.
* `--focus-chars` : Focus on reducing the amount of uncompressed characters, even if the compressed size grows.
* `--focus-compressed` : Focus on reducing the compressed size of the code, even if the amount of characters grows.
* By default, the minification is balanced for both metrics.

You can disable parts of the minification process via additional command-line options:

* `--no-minify-rename` : Disable all renaming of identifiers
* `--no-minify-consts` : Disable replacements of constant expressions with their value (see [constants](#constants))
* `--no-minify-spaces` : Disable removal of spaces (and line breaks)
* `--no-minify-lines` : Disable removal of line breaks
* `--no-minify-comments` : Disable removal of comments (requires `--no-minify-spaces`)
* `--no-minify-tokens` : Disable removal and alteration of tokens (not including identifier renaming)
* `--no-minify-reorder` : Disable reordering of statements

You can control how safe the minification is (see [details about unsafe minifications](#pitfalls-of-full-minification)):
* `--minify-safe-only` : Do only safe minification. Equivalent to specifying all of the below.
* `--rename-safe-only` : Do only safe renaming (equivalent to preserving all table keys, and - if _ENV is used in the cart - all globals)
* `--reorder-safe-only` : Do only safe statement reordering
* `--builtins-safe-only` : Do only safe replacement of builtin function calls

Additional options:

* `--preserve` :  Equivalent to specifying `--$preserve:` in the cart itself. Described [here](#preserving-identifiers-across-the-entire-cart).
* `--rename-map <file>` : Generate a file telling you how the identifiers were renamed. (This can be useful for debugging) 

## Operation details

* All unnecessary comments, spaces and line breaks are removed.
* Unnecessary tokens like parentheses and trailing commas are removed
* Identifiers are renamed to be short and to use common characters for better compression
    * Under `--focus-chars`, identifiers are made as short as possible
* Tokens are made more consistent, to reduce compression ratio
* If/while statements may be converted to one-line shorthands, depending on the focus:
    * By default, they're converted to shorthand if deemed to have a positive impact on compression
    * Under `--focus-chars`, they're always converted to shorthand when possible
    * Under `--focus-compressed`, they're always converted to either all shorthands or all longhands
* Multiple successive local declarations are merged into one when safe to do so, saving tokens.
    * under `--focus-tokens`, the same is done for multiple successive assignments. (Especially effective *without* `--minify-safe-only`)

## Pitfalls of full minification

When using `--minify` without `--minify-safe-only`, Shrinko8 makes - by default - some assumptions about your cart:

* Renaming assumptions: (`--rename-safe-only` disables these):
    * Your cart doesn't mix identifiers and strings when indexing tables or _ENV. (E.g. it doesn't access both `some_table.x` and `some_table["x"]`).
    * Your cart does not use _ENV (except for some simple cases)

* Builtin usage assumptions (`--builtins-safe-only` disables these):
    * Your cart does not override builtin functions via _ENV.

* Reordering assumption: (Only relevant under `--focus-tokens`; `--reorder-safe-only` disables it; complex to describe but hard to break):
    * Your cart does not access freshly-assigned variables or table members inside meta-methods or builtins overridden via _ENV. (See example [here](#prevent-merging-of-specific-statements))

These assumptions allow Shrinko8 to - for example - freely rename identifiers used to index tables.

If these assumptions don't hold, the minified cart won't work properly, e.g:

```lua
local my_obj = {key=123} -- here, key is an identifier.
?my_obj.key -- OK. Here, key is an identifier again.
local my_key = "key" -- here, key is a string.
?my_obj[my_key] -- BUG! my_obj will not have a "key" member after minification!
```

In such cases, you have multiple ways to tell Shrinko8 precisely how your cart breaks these assumptions, allowing you to achieve better minification than would be possible with just `--minify-safe-only`:

* Mixing identifiers and strings when indexing tables:

    * If you index a table by both identifiers and string literals, you can [tell Shrinko8 to rename the string literals too](#renaming-specific-strings).

    * If you index a table  by both identifiers and strings that you build at runtime (e.g. via `+`), you can [preserve those identifiers across the entire cart](#preserving-identifiers-across-the-entire-cart).

    * If you have certain tables whose keys you don't want to rename - e.g. because the keys are built at runtime, or because the tables are serialized to a savefile - you can [preserve all keys in a table](#controlling-renaming-of-all-keys-of-a-table).

* Using _ENV:

    * You can always tell Shrinko8 to [rename table keys the same way as globals](#renaming-table-keys-the-same-way-as-globals), making it possible to mix _ENV and other tables freely. (Though if you index _ENV with strings, you still need to follow the 'mixing identifiers and strings' bullet point above)

      Alternatively:

    * If you're making your tables inherit _ENV (allowing you to bind the table to _ENV and access both table members and globals without a '.'), you can [rename table keys the same way as globals](#renaming-table-keys-the-same-way-as-globals).

    * If you're otherwise assigning to or from _ENV, you may need to either [specify how all keys of a table are renamed](#controlling-renaming-of-all-keys-of-a-table), or [specify how specific occurrences of an identifier is renamed](#advanced---controlling-renaming-of-specific-identifier-occurrences) in order to tell Shrinko8 which table keys should be renamed as if they were globals.
    
* Reordering assumptions:

    * You can [prevent merging of specific statements](#prevent-merging-of-specific-statements).

### Renaming specific strings

You can add a `--[[$member]]` comment before a string to have the minifier rename it as if it were an identifier.

E.g:
```lua
local my_key = --[[$member]]"key" -- here, key is a string but is renamed as if it were an identifier
local my_obj = {key=123} -- here, key is an identifier
?my_obj[my_key] -- success, this prints 123 even after minification
```

You can also use this with multiple keys split by comma (or any other characters):
```lua
local my_keys = split --[[$member]]"key1,key2,key3" -- here, each of key1, key2 and key3 is renamed
```

And you can similarly use `--[[$global]]` for globals:
```lua
local my_key = --[[$global]]"glob"
glob = 123
?_ENV[my_key] -- 123
```

If you have string literals with more complex structure - for example `"key=str,key2=str2"` - where different parts of the string must be renamed differently - you can use [the split sub-language](#advanced---the-split-sub-language) to easily define the format of the string.

### Preserving identifiers across the entire cart

You can instruct the minifier to preserve certain identifiers across the entire cart by adding a `--$preserve:` comment anywhere in the code:

```lua
--$preserve: my_global_1, my_global_2, update_*, *.my_member, my_env.*
```

* my_global_1 and my_global_2 will not be renamed when used as globals
* globals whose names start with `update_` will not be renamed
* my_member will not be renamed when used to index a table
* table members will not be renamed when accessed through my_env

If you prefer, you can instead pass this information in the command line, e,g:

`python shrinko8.py path-to-input.p8 path-to-output.png --minify --preserve "my_global_1, my_global_2, update_*, *.my_member, my_env.*"`

You can combine wildcards and negation (`!`) to preserve everything except some identifiers:

```lua
--$preserve: *.*, !*.my_*
```

* Only identifiers starting with `my_` will be renamed when used to index a table

### Renaming table keys the same way as globals

You can instruct the minifier to rename table keys the same way as globals (allowing you to freely mix _ENV and other tables), by adding the following comment in the code:

```lua
--$preserve: *=*.*
```

If you prefer, you can instead pass `--preserve "*=*.*"` to the command line.

### Controlling renaming of all keys of a table

You can use `--[[$preserve-keys]]`, `--[[$global-keys]]` and `--[[$member-keys]]` to affect how *all* keys of a table are renamed.

This can be applied on either table constructors (aka `{...}`) or on variables. When applying on variables, the hint affects all members accessed through that variable, as well as any table constructors directly assigned to it.
```lua
local --[[$preserve-keys]]my_table = {preserved1=1, preserved2=2}
my_table.preserved1 += 1 -- all member accesses through my_table are preserved
?my_table["preserved1"]

-- here, {preserved3=3} is not directly assigned to my_table and so needs its own hint
my_table = setmetatable(--[[$preserve-keys]]{preserved3=3}, my_meta)
?my_table["preserved3"]

-- while assigning directly to _ENV no longer requires a hint, indirect assignment like below does:
local env = --[[$global-keys]]{assert=assert, add=add}
do
  local _ENV = env
  assert(add({}, 1) == 1)
end
```

This can be also be useful when assigning regular tables to _ENV:
```lua
-- hints on an _ENV local affects all globals in its scope
for --[[$member-keys]]_ENV in all({{x=1,y=5}, {x=2,y=6}}) do
  x += y + y*x
end
```

### Advanced - The 'split' sub-language

Say you have a function which takes a string like `"key1=str1,key2=str2"` and splits it into a table `{key1="str1",key2="str2"}`. You want strings passed to this function to be renamed appropriately. (rename key1 and key2 as members, but preserve str1 and str2 as strings)

You can do that by specifying that the strings use the `split` sub-language - which comes builtin to shrinko8:
```lua
mysplit(--[[$language::split (member=string)s,]]"key1=str1,key2=str2")

-- or, to avoid repeating yourself:

--$def-alias: mysplit = split (member=string)s,
mysplit(--[[$language::mysplit]]"key1=str1,key2=str2")
```

Here, `(member=string)s,` tells the split sub-language precisely how the string will be split. Some more examples will help explain the syntax:
```lua
-- here, the string consists of a table member (key), a global, and a string (preserved) - 
--   all separated by ';'
mysplit2(--[[$language::split member;global;string]]"member1;global1;string1")
-- e.g. may result in "m;g;string1"

-- here, notice the plural on 'globals'.
-- this means the string consists of a table member at the start, a string at the end, 
--   and any number of globals between them, all separated by ';'.
mysplit3(--[[$language::split member;globals;string]]"member1;global1;global2;global3;string1")
-- e.g. may result in "m;a;b;c;string1"

-- here, instead of the middle parts being just globals, they're split further via the '=' characters.
-- the plural "s" acts on the parentheses just as it did on the 'global' before.
mysplit4(--[[$language::split member;(global=string)s;string]]
         "member1;global1=str1;global2=str2;global3=str3;endstr")
-- e.g. may result in "m;a=str1;b=str2;c=str3;endstr"

-- here, the trailing ',' is needed to specify the outer separator.
-- the string consists of any number of 'global=string' splits, separated by ','
mysplit5(--[[$language::split (global=string)s,]]"glob1=str1,glob2=str2,glob3=str3")
-- e.g. may result in "a=str1,b=str2,c=str3"
-- it could also have been written as '(global=string)s,(global=string)'

-- here, notice the plural on both 'members' and 'strings'
-- this means the string consists of a global at the start,
--   and then alternating table members and strings
mysplit6(--[[$language::split global,members,strings]]"global,member1,str1,member2,str2,member3,str3")
-- e.g. may result in "g,a,str1,b,str2,c,str3"

-- any separator can be used. '(' and ')' need escaping via '\(' and '\)'.
-- english characters can be used as separators by escaping via '\w', e.g. '\wq'
```

This will give you the power to appropriately rename strings in simple sub-languages consisting of a bunch of splits. For more complex sub-languages that do real parsing, you may need [to write your own sub-language (advanced)](#advanced---custom-sub-language).

### Advanced - Controlling renaming of specific identifier occurrences

The `--[[$global]]`, `--[[$member]]` and `--[[$preserve]]` hints can also be used on a **specific** occurrence of an identifier to change the way it's renamed.

Usually, there are easier ways to control renaming (such as by [preserving identifiers across the entire cart](#preserving-identifiers-across-the-entire-cart) or [controlling renaming of all keys in a table](#controlling-renaming-of-all-keys-of-a-table)), but this option is here for cases where you need precise control over how to rename each occurence.

```lua
do
  -- NOTE: can be more easily achieved via --[[$global-keys]]
  local _ENV = {--[[$global]]assert=assert}
  assert(true)
end
-- NOTE: can be more easily achieved via --[[$member-keys]]
for _ENV in all({{x=1}, {x=2}}) do
  --[[$member]]x += 1
end
```

### Advanced - Renaming Built-in Pico-8 functions

For cases like tweet-carts, when you use a builtin function multiple times throughout your cart, you often want to assign it to a shorter name at the beginning of the cart. With shrinko8, you can keep using the full name of the builtin, but tell the minifer to only preserve the builtin when it's first accessed, as follows:

```lua
--$preserve: !circfill, !rectfill
circfill, rectfill = --[[$preserve]]circfill, --[[$preserve]]rectfill
circfill(10,10,20); circfill(90,90,30)
rectfill(0,0,100,100); rectfill(20,20,40,40)
```

Above, all uses of circfill and rectfill are renamed except for the ones preceded by `--[[$preserve]]`

Be aware that doing this won't reduce the compressed size of the cart, and will increases the token count (due to the assignment), so it's only for when you care about character count above all else.

### Advanced - Explicit renaming

While Shrinko8 has good heuristics for choosing identifier names, it's still possible to improve upon them when hand-minifying carts (useful especially when trying to fit small carts under some chosen limit).

In order to still be able to use Shrinko8 in such cases, a hint is provided to instruct Shrinko8 how to rename specific variables:

```lua
function --[[$rename::f]]func(--[[$rename::a]]arg)
    local --[[$rename::b]]val = arg
end
```

A rename hint affects all instances of the marked variable.

## Prevent merging of specific statements

You can insert `--[[$no-merge]]` between two statements to ensure they're not merged, e.g:

```lua
-- note: this example requires --focus-tokens to see the effect
local weird_table = setmetatable({add_me=0}, {
    __newindex=function(tbl, key, val) rawset(tbl, key, val + t.add_me) end
})
-- the following statements do not do the same thing if combined into one
-- aka: weird_table.add_me, weird_table.new_key = 3, 4
-- so we can add --[[$no-merge]] between them to ensure they're not merged.
weird_table.add_me = 3
--[[$no-merge]]
weird_table.new_key = 4
```

## Keeping comments

You can keep specific comments in the output via:

```lua
--$keep: This is a comment to keep
-- But this comment is gone after minify
```

# Constants

During [minification](#minification), Shrinko8 will automatically replace most constant expressions with their value:

```lua
func(60*60)
-- becomes:
func(3600)

func('the answer is: '..1+3*2)
-- becomes:
func('the answer is: 7')
```

If you don't want to minify, but still want to replace constants, you can pass `--minify-consts-only` to the command line.

In addition, variables that are declared with the `--[[$const]]` hint are treated as constants:

```lua
--[[$const]] k_hero_spr = 4
spr(k_hero_spr, x, y)
-- becomes:
spr(4, x, y)

--[[$const]] version = 'v1.2'
?'version: '..version
-- becomes:
?'version: v1.2'

-- the --[[$const]] hint can apply to either individual variables or entire local statements
--[[$const]] local k_rock,k_box,k_wall = 4,5,6
objs={k_rock,k_wall,k_wall,k_box}
-- becomes:
objs={4,6,6,5}

-- some builtin functions can be used inside const declarations
--[[$const]] k_value = 2.5
--[[$const]] derived = flr(mid(k_value, 1, 5))
?derived
-- becomes:
?2
```

Furthermore, constant `if` and `elseif` branches are removed appropriately, allowing you to easily keep debug code in your source files, enabling it by simply changing the value of a variable:

```lua
--[[$const]] TRACE = false
--[[$const]] DEBUG = true

if (TRACE) ?"something happened!"
if DEBUG then
  spr(debug_spr, 10, 10)
end

-- becomes:
spr(debug_spr,10,10)
```

Some details to keep in mind:
* *Local* variables that **aren't** declared as `--[[$const]]` may still be treated as constants in cases where it's safe & advantageous to do so.
* *Local* variables that **are** declared as `--[[$const]]` still follow the usual lua scoping rules. They cannot be reassigned but new locals with the same name can be defined.
* *Global* variables that **aren't** declared as `--[[$const]]` are currently never treated as constants.
* *Global* variables that **are** declared as `--[[$const]]` are assumed to *always* have their constant value. They cannot be reassigned and can only be used below their declaration.

## Passing constants via command line

You can even declare constants in the command line, if you prefer:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --minify-safe-only --const DEBUG true --const SPEED 2.5 --str-const VERSION v1.2`

```lua
--[[$const]] SPEED = 0.5 -- default value
if DEBUG then
  ?'debug version ' .. (VERSION or '???')
end
hero = 0
function _update()
  hero += SPEED
end
```

Becomes: (disregarding other minifications)

```lua
?"debug version v1.2"
hero = 0
function _update()
  hero += 2.5
end
```

## Limitations

Keep in mind that in some cases, Shrinko8 will play it safe and avoid a computation whose result is questionable or has a high potential to change between pico8 versions. If this prevents a `--[[$const]]` variable from being assigned a constant, Shrinko8 will warn about this:

```lua
-- here, abs overflows (due to receiving -0x8000), and shrinko8 chooses not to rely on the overflow behaviour
--[[$const]] x = abs(0x7fff+1)-1
?x

-- warning:
--tmp.lua:1:13: Local 'x' is marked as const but its value cannot be determined due to 'abs(0x7fff+1)'

-- Becomes only:
x=abs(32768)-1
?x
```

If you find such limitations that you'd like to see lifted, feel free to open an issue.

Finally, note that:
* You can turn off all constant replacement via `--no-minify-consts`.
* You can prevent treating specific variables as constants by declaring them with a `--[[$non-const]]` hint. (though normally, there is no reason to do this)

# Saving Tokens via Parens-8

[Parens-8](https://codeberg.org/wellspring-labs/parens-8) by Wellspring-Labs can compile .....

# Linting

Linting finds common code issues in your cart, like forgetting to use a 'local' statement

## To lint your p8 cart:

`python shrinko8.py path-to-input.p8 --lint`

You can combine linting with other operations:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --lint --count --minify`

## Linting options

You can disable certain lints globally via additional command-line options:

* `--no-lint-unused` : Disable lint on unused variables
    * `--no-lint-unused-global` : Disable lint on unused global variables
* `--no-lint-duplicate` : Disable lint on duplicate variable names
    * `--no-lint-duplicate-global` : Disable lint on duplicate variable names between a local and a global
* `--no-lint-undefined` : Disable lint on undefined variables

Normally, a lint failure prevents cart creation, but `--no-lint-fail` overrides that.

Normally, lint errors are displayed in a format useful for external editors, showing the line number in the whole .p8 file. However, you can use `--error-format tabbed` to show the pico8 tab number and line number inside that tab instead.

Misc. options:

* `--lint-global` : Equivalent to specifying `--$lint:` inside the cart itself

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

Tell the linter about the globals it didn't see you define via the `--$lint:` hint:
```lua
--$lint: global_1, global_2
function f()
    dostuff(global_1, global_2)
end
```

Tell the linter to allow you to define globals (by assigning to them) in a specific function via the `--$lint: func::_init` hint:
```lua
--$lint: func::_init
function my_init()
    global_1, global_2 = 1, 2 -- these globals can be used anywhere since they're assigned here
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
--$lint: print
function f()
    local old_print = print
    print = function() end
    call_something()
    print = old_print
end
```

## Unused variable lints

This lint alerts you when you've declared a variable but never used it, which is usually a mistake.

It also tells you when the *last* parameter of a function is unused, as that's either a mistake or a waste of a token.

To tell the linter that some specific local is OK to be unused, named it beginning with underscore (e.g. `_` or `_some_name`). E.g:
```lua
do
  local _, _, x, y = get_stuff() -- lint warning about y (but not about _) - you probably meant to pass it to do_stuff
  do_stuff(x, x)
end
```

If you have false positives in your cart due to globals being used via `_ENV`, you can disable this check just for globals via `--no-lint-unused-global`.

Another option is to use the `--$lint: used::<var>` hint:
```lua
--$lint: used::global_1, used::global_2
function global_1() end
global_2 = ""
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

It also alerts you when you declare a local with the same name as a global you defined or used elsewhere in your cart, which is similarly confusing, E.g.:

```lua
function maths(arg)
    return sin(arg) + cos(arg)
end
function confess(sin) -- lint warning about sin
    do_stuff(sin)
    -- ...
    show_some_ui(sin(3)) -- oops!
end
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

Note that the compressed size is how *this* tool would compress the code, which is better than how Pico-8 would.

You can combine counting with other operations, in which case the counts are of the output cart, not the input cart:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --lint --count --minify`

In such cases, you can also use `--input-count` to count the number of tokens, characters, and compressed bytes (if applicable) of the input cart.

If you're not interested in the number of tokens or in the compressed size, you can use `--no-count-tokenize` or `--no-count-compress` to avoid tokenizing or compressing the cart just to get the count. (You will still see the count if the tokenize/compress had to be done anyway, though)

# Format Conversion

Shrinko8 supports multiple cart formats, and allows converting between them:
* p8 - Pico-8 cart source
* png - Pico-8 cart exported into a png
* rom - Pico-8 cart exported into a rom
* tiny-rom - Pico-8 cart exported into a tiny rom (code only)
* lua - raw lua code, with no headers
* clip - Pico-8 clipboard format (i.e. [cart]...[/cart])
* url - Pico-8 education version url (code & gfx only)
* js, pod - Exported formats, see [section on how to read or write them](#reading-and-writing-exported-formats).
* label - A 128x128 image of a cart's label (label only)
* spritesheet - A 128x128 image of a cart's spritesheet (gfx only)
* auto - try to determine automatically from content

E.g:
```
python shrinko8.py path-to-input.p8 path-to-output.png
python shrinko8.py path-to-input.png path-to-output.rom
python shrinko8.py path-to-input.rom path-to-output.lua
python shrinko8.py path-to-export/windows/data.pod path-to-output.p8
```

By default, the format is determined by the file extension, but you can specify it explicitly via:
* `--input-format <format>` for the input format.
* `--format <format>` for the output format
(Where `<format>` is one of the formats listed above)

You can combine conversion with other operations:

`python shrinko8.py path-to-input.p8 path-to-output.rom --count --lint --minify`

Specifying the format is also useful when using the standard input/output (via `-`), e.g.:

`python shrinko8.py path-to-input.p8 - --minify --format lua` (This prints minified lua to stdout)

You can convert a cart to multiple formats at once using `--extra-output path [format]`:

`python shrinko8.py path-to-input.p8 path-to-output.png --extra-output path-to-output.p8 --extra-output path-to-output.rom`

You can additionally export the cart's spritesheet and label:

`python shrinko8.py path-to-input.p8 path-to-output.png --extra-output path-to-spritesheet.png spritesheet --extra-output path-to-label.png label`

## Specifying custom labels & titles

Normally, shrinko8 will take the label and title (if any) from the input cart, same as pico8 does.

However, it is also possible to override the label from a custom 128x128 screenshot via `--label <path>` and the title via `--title "some title"`

In addition, since pico8 supports reading carts regardless of if they look like pico8 carts, you can specify a custom template image (overriding [template.png](https://github.com/thisismypassport/shrinko8/blob/main/template.png)) via `--template-image <path>` (and optionally `--template-only` to avoid adding the label and title on top of it). However, this feature should be used in moderation.

## Merging multiple carts into one

You can tell Shrinko8 to merge specific sections from other carts into the input cart using `--merge path sections [format]`.

The following example takes the label from `label-cart.p8` and sfx & music from `sounds-cart.p8`:

`python shrinko8.py path-to-input.p8 path-to-output.png --merge label-cart.p8 label --merge sounds-cart.p8 sfx,music`

The following example imports the spritesheet from a 128x128 image at `spritesheet.png`

`python shrinko8.py path-to-input.p8 path-to-output.png --merge spritesheet.png gfx spritesheet`

## Reading and writing exported formats

Shrinko8 supports reading and writing exported formats. Creating exports through Shrinko8 can be useful in cases when Pico8's compression algorithm isn't able to fit your cart into the export, while Shrinko8's can.

Creating an export requires you to have a copy of Pico8 and provide the pico8.dat file that comes with it as an argument to Shrinko8, as seen [below](#creating-exports).

### Reading exports

Shrinko8 can read the following exports:
* js - Pico-8 carts exported to html+js - supply the .js file to shrinko8.
* pod - Pico-8 carts exported as (any) executables - supply the .pod file to shrinko8.

When you pass an export as the input parameter to Shrinko8, it will - by default - read the main cart inside.

If the export contains more than one cart, you can use:
* `--list` to list the names of the carts in the export (the first cart listed is the main cart)
* `--dump <folder>` to dump all the carts in the export into the given folder
* `--cart <name>` to select which cart to read from the export, instead of the main cart

### Creating exports

Shrinko8 can create the following exports:
* bin - A directory containing all exports (both binary and web). Recommended.
* js - Just the .js file for an html+js export.
* pod - Just the .pod file for any binary export.

When you pass an export as the output parameter to Shrinko8, it will - by default - try to create a new export containing a single cart.

However, for that to work, you need to also supply `--pico8-dat <path to pico8.dat file inside your pico8 directory>` to Shrinko8, e.g:

`python shrinko8.py path-to-input.p8 path-to-output.bin --pico8-dat c:/pico8/pico8.dat`

You can create a multi-cart export by supplying additional input carts:

`python shrinko8.py path-to-main-cart.p8 extra-cart-1.p8 extra-cart-2.p8 path-to-output.bin --pico8-dat c:/pico8/pico8.dat`

If you need to explicitly specify the type of each additional input cart, you can instead use `--extra-input`

Also, if both the input and output are exports, all carts from the input get placed in the output, unless `--cart` is explicitly specified.

## Pico8 versions

By default, Shrinko8 tries to preserve the pico8 version the cart was created with, as well as - when minifying - avoid using features not supported by said pico8 version.

However, some cart formats (roms, js and pod exports) don't store this version, in which case pico8 will create a cart targetting a recent pico8 version, which will require that version of pico8 or newer to load.

You can use `--output-version <version>` (where version can be a string like 'v0.2.6b' or a raw number like 42) to explicitly specify which version to use for the generated cart - or just `--update-version` to use the latest version shrinko8 supports.

You can also use `--version` to print the input cart's pico8 version.

# Unminification

You can undo some of the effects of minification, or just reformat the cart's code in a consistent manner:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --unminify`

Of course, renaming cannot be undone, so the resulting code may still not be readable.

Options:

* `--unminify-indent` : Specify the size of the indentation to use (default: 2). Can also pass `tabs` to indent with tabs instead.

# Custom Pico8 and Python Scripts

For advanced usecases, you can create a pico8 or python script that allow you to:
* Make programmatic modifications to the cart before/after other steps
* Load other carts and merge them in custom ways with the main cart
* Save other carts
* And much more.

To run, use `--script <path>`, here shown together with other tools:

`python shrinko8.py path-to-input.p8 path-to-output.png --count --lint --minify --script path-to-script.py`

You can also pass arguments to your script by putting them after `--script-args`:

`python shrinko8.py path-to-input.p8 path-to-output.png --count --lint --minify --script path-to-script.py --script-args my-script-arg --my-script-opt 123`

The following information and example are specific to whether you want to write in pico8 or python - expand the appropriate section.

<details>
<summary><b>Documentation & example for Python scripts</b></summary>

Python scripts need to have an extension of `.py`

Example python script showing the API and various capabilities:
```python
# this is called after your cart is read but before any processing is done on it:
def preprocess_main(cart, args, ctxt, **_): # '**_' allows other (including future) arguments to be ignored
    print("hello from preprocess_main!")

    # 'cart' contains 'code' and 'rom' attributes that can be used to read or modify it
    # 'cart.code' is a pico8 string where each char is between '\0' and '\xff'
    #             use to/from_p8str in pico_defs.py to convert a pico8 string from/to a unicode string
    #             use decode/encode_p8str in pico_defs.py to convert a pico8 string from/to raw bytes
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

    # args.script_args contains any arguments sent to the script
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("arg", help="first arg sent to script", nargs="?")
    parser.add_argument("--my-script-opt", type=int, help="option sent to script")
    opts = parser.parse_args(args.script_args)
    print("Received args:", opts.arg, opts.my_script_opt)

    # ctxt contains some read-only information like `lang`, `version` and `builtins`
    # you can also use ctxt.get/set_field to store extra information on it to pass between different stages
    # (use a unique field name to avoid conflicts)
    ctxt.set_field("my_script_data", [opts, other_cart])
    # there is also:
    # my_dict = ctxt.get_field("my_dict_field", dict) # initialized to dict() instead of None

# this is called before your cart is written, after it was fully processed
def postprocess_main(cart, ctxt, **_):
    print("hello from postprocess_main!")

    # dump the code of the cart to be written
    from pico_defs import from_p8str
    with open("out.txt", "w", encoding="utf8") as f:
        f.write(from_p8str(cart.code)) # from_p8str converts the code to unicode

    # write an extra cart based on the current cart, but with a zeroed spritesheet, in any format (e.g. p8,png,rom)
    from pico_cart import write_cart, CartFormat
    new_cart = cart.copy()
    new_cart.rom[0x0000:0x2000] = bytearray(0x2000) # zero it out
    write_cart("new_cart.p8", new_cart, CartFormat.p8)
    write_cart("new_cart.p8.png", new_cart, CartFormat.png)

    # write a new cart with the same rom but custom code, in rom format
    from pico_cart import Cart, CartFormat, write_cart
    from pico_defs import to_p8str
    new_cart = Cart(code=to_p8str("-- rom-only cart 🐱"), rom=cart.rom)
    write_cart("new_cart2.rom", new_cart, CartFormat.rom)

    # can use the data stored in the preprocess stage:
    opts, other_cart = ctxt.get_field("my_script_data")
```

</details>
<br>
<details>
<summary><b>Documentation & example for Pico8 scripts</b></summary>

Pico8 scripts need to have an extension of `.p8` or `.lua`. They can import other `.p8` or `.lua` scripts (and the scripts they import can import scripts themselves, unlike in native pico8)

Usually, you'd have a pico8 script that's specific to shrinko's interface, which imports and uses a 'generic' pico8 script that's runnable in pico8 as well.

Pico8 scripts run via [lupaz8](https://github.com/thisismypassport/lupaz8) - a fork of scoder's [lupa](https://github.com/scoder/lupa) using a [fork](https://github.com/thisismypassport/z8lua) of samhocevar's [z8lua](https://github.com/samhocevar/z8lua). In detail:
* They're highly compatible with pico8 syntax and semantics (shorthands, 16.16 fixed-point numbers, etc.)
* They support only a subset of pico8's global functions:
  * All math, string, table, memory, and lua functions are supported. (e.g: `abs`, `split`, `deli`, `memcpy`, `select`)
  * `print` and `printh` are also supported
  * If anything is unsupported, you can add a stub implementation, or open an issue if you think it should be.
* They can also use most standard lua libraries (`io.*`, `os.*`, `string.*`, `table.*`), to allow manipulating files/etc
* They contain the `python` and `shrinko` globals to help interface with shrinko's interface
* They use the `userdata` type for objects coming from python.

Example python script showing the API and various capabilities:
```lua
local module = {} -- include functions that shrinko should call here

-- this is called after your cart is read but before any processing is done on it:
function module.preprocess_main(opts)
    local cart, args, ctxt = opts.cart, opts.args, opts.ctxt
    print("hello from preprocess_main!")

    -- 'cart' contains 'code' and 'rom' attributes that can be used to read or modify it
    -- 'cart.code' is a string containing all the cart's code (in p8scii encoding).
    --             use shrinko.to_utf8 to convert it to a utf8 string (e.g. for use with io:write)
    --             or shrinko.from_utf8 to convert a utf8 string back to p8scii.
    -- 'cart.rom' is a python Memory object that is best to manipulate with the following APIs:
    --            rompeek[2/4](rom,addr[,count]) - similar to peek[2/4]
    --            rompoke[2/4](rom,addr,...) - similar to poke[2/4]
    --            rommemcpy(rom,addr,srcrom,srcaddr,len) - similar to memcpy
    --            rommemset(rom,addr,val,len) - similar to memset
    --            shrinko.from_memory(rom) - get string from rom
    --            shrinko.to_memory(str) - get rom from string
    --            shrinko.to_memory(size) - create Memory object of given size
    --            (to copy between rom and internal pico8 memory - convert to/from string)

    -- copy the spritesheet from another cart
    local read_cart = python.import("pico_cart").read_cart
    local other_cart = read_cart("test_input/test.p8") -- can be used to read p8 or png carts
    rommemcpy(cart.rom, 0x0000, other_cart.rom, 0x0000, 0x2000)

    -- encode binary data into a string in our cart
    -- our cart's code should contain a string like so: "$$DATA$$"
    local bytes_to_string_contents = python.import("pico_utils").bytes_to_string_contents
    local fh = io.open("test_input/binary.dat", "rb") -- lua io/os/etc are available for use
    local contents = bytes_to_string_contents(fh:read("*a"))
    cart.code = string.gsub(cart.code, "%$%$DATA%$%$", string.gsub(contents, "%%", "%%%%")) -- that's lua for you
    fh:close()

    -- args.script_args contains any arguments sent to this script
    local argopts = python.table(args.script_args) -- should convert to lua table first
    for arg in pairs(argopts) do
        print("Received arg: "..arg)
    end
    
    -- ctxt contains some read-only information like `lang`, `version` and `builtins`
    -- you can also use ctxt.get/set_field to store extra information on it to pass between different stages
    -- (use a unique field name to avoid conflicts)
    ctxt:set_field("my_script_data", {argopts, other_cart})
end

-- this is called before your cart is written, after it was fully processed
function module.postprocess_main(opts)
    local cart, ctxt = opts.cart, opts.ctxt
    print("hello from postprocess_main!")
    
    -- dump the code of the cart to be written
    local fh = io.open("test_output/out.txt", "w")
    fh:write(shrinko.to_utf8(cart.code)) -- to_utf8 converts the code to unicode
    fh:close()

    local fh = io.open("test_output/rawout.txt", "wb")
    fh:write(cart.code) -- or you can write it as bytes, without encoding
    fh:close()

    -- write an extra cart based on the current cart, but with a zeroed spritesheet, in any format (e.g. p8,png,rom)
    local pico_cart = python.import("pico_cart")
    local new_cart = cart.copy()
    rommemset(new_cart.rom, 0x0000, 0, 0x2000) -- zero it out
    pico_cart.write_cart("test_output/new_cart.p8", new_cart, pico_cart.CartFormat.p8)
    pico_cart.write_cart("test_output/new_cart.p8.png", new_cart, pico_cart.CartFormat.png)

    -- write a new cart with the same rom but custom code, in rom format
    local new_cart = pico_cart.Cart("-- rom-only cart 🐱", cart.rom)
    pico_cart.write_cart("test_output/new_cart2.rom", new_cart, pico_cart.CartFormat.rom)

    -- can use the data stored in the preprocess stage:
    local data_table = ctxt:get_field("my_script_data")
    local argsopts, other_cart = unpack(data_table)
end

return module -- must return it from the script
```

Python/pico8 integration - more details:
* You can use `python_func(python.args{1, 2, opt1=3, opt2=4})` to pass keyword arguments to a python function
* Usually, accessing attributes and items of python objects directly will work - but for dicts, use e.g. `python.attrs(dict).get(key)` to access attributes.
* You can convert python lists & dicts into tables via `python.table(obj)`
* You can convert tables into python lists via `python.list(tbl)` and into python dicts via `python.dict(tbl)`

</details>

## Advanced - custom sub-language

For **really** advanced usecases, if you're embedding a custom language inside the strings of your pico-8 code, you can let Shrinko8 know how to lint & minify it.

E.g. this allows renaming identifiers shared by both the pico-8 code and the custom language.

Mark the language with `--[[$language::<name>]]` in the code:
```lua
eval(--[[$language::evally]][[
    circfill 50 50 20 7
    my_global_var <- pack
    rawset my_global_var .some_member 123
    rawset my_global_var .another_member 456
]])
```

In the script, provide a class that handles the language via sublanguage_main.

The details are specific to the language you write the script in - expand the appropriate section:

<details>
<summary><b>Documentation & example for Python scripts</b></summary>

Here is a complete example of what sub-languages can do:
```python
from pico_process import SubLanguageBase, is_identifier
from collections import Counter

class MySubLanguage(SubLanguageBase):
    # NOTE: all members are optional.

    # called to parse the sub-language from a string
    # (strings consist of raw pico-8 chars ('\0' to '\xff') - not real unicode)
    def __init__(self, str, args, on_error, **_):
        # we may have received args that can be used to customize the language (not used here)
        self.args = args
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
        
    def is_assignment(self, stmt):
        return len(stmt) > 1 and stmt[1] == "<-" # our lang's assignment token

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

    # for --lint:

    # called to get globals defined within the sub-language's code
    # such globals can be used outside the sub-language too.
    def get_defined_globals(self, **_):
        for stmt in self.stmts:
            # our language only allows assignment to globals, so any assignment defines a global
            if self.is_assignment(stmt):
                yield stmt[0]

    # called to get globals used within the sub-language's code
    def get_used_globals(self, **_):
        for stmt in self.stmts:
            if self.is_assignment(stmt):
                stmt = stmt[2:] # don't return the assignment target, to get warnings if it isn't used

            for token in stmt:
                if self.is_global(token):
                    yield token

    # called to lint the sub-language's code
    def lint(self, builtins, globals, on_error, **_):
        for stmt in self.stmts:
            for token in stmt:
                if self.is_global(token) and token not in builtins and token not in globals:
                    on_error("Identifier '%s' not found" % token)
        # could do custom lints too

# this is called to get a sub-language class by name
def sublanguage_main(lang, **_):
    if lang == "evally":
        return MySubLanguage
```

You can see another sub-language example in Shrinko8's `scripts/split.py`.

</details>
<br>
<details>
<summary><b>Documentation & example for Pico8 scripts</b></summary>

```lua
local pico_process = python.import("pico_process")
local SubLanguageBase = pico_process.SubLanguageBase -- sub-language base-class
local module = {}

-- helper function like split, but ignores empties
function split_nonempty(str, ch)
    local res = split(str, ch, false)
    while (del (res, "")); -- (or copy to new table)
    return res
end

MySubLanguage = python.class(SubLanguageBase)

-- called to parse the sub-language from a string
-- (strings consist of raw pico-8 chars ('\0' to '\xff') - not real unicode)
function MySubLanguage:__init(str, opts)
    -- we may have received args that can be used to customize the language (not used here)
    self.args = opts.args
    -- our trivial language consists of space-separated tokens in newline-separated statements
    local lines = split_nonempty(str, "\n")
    self.stmts = {}
    for line in all(lines) do
        add(self.stmts, split_nonempty(line, " "))
    end
    -- we can report parsing errors:
    -- opts.on_error("Example")
end

-- these are utility functions for our own use:

function MySubLanguage:is_global(token)
    -- is the token a global in our language? e.g. sin / rectfill / g_my_global
    return pico_process.is_identifier(token)
end

function MySubLanguage:is_member(token)
    -- is the token a member in our language? e.g. .my_member / .x
    return token[1] == "." and self:is_global(sub(token, 2))
end
    
function MySubLanguage:is_assignment(stmt)
    return #stmt > 1 and stmt[2] == "<-" -- our lang's assignment token
end

-- for --lint:

-- called to get globals defined (aka assigned to) within the sub-language's code
function MySubLanguage:get_defined_globals()
    local globals = {}
    for stmt in all(self.stmts) do
        if self:is_assignment(stmt) then
            add(globals, stmt[1])
        end
    end
    return python.list(globals) -- must return a python dict
end

-- called to get globals used (aka read from) within the sub-language's code
function MySubLanguage:get_used_globals()
    local globals = {}
    for stmt in all(self.stmts) do
        local start = 1
        if (self:is_assignment(stmt)) start = 3 -- ignore assigned-to globals

        for i=start,#stmt do
            local token = stmt[i]
            if (self:is_global(token)) add(globals, token)
        end
    end
    return python.list(globals) -- must return a python dict
end

-- called to lint the sub-language's code
function MySubLanguage:lint(opts)
    local builtins = python.table(opts.builtins)
    local globals = python.table(opts.globals)

    for stmt in all(self.stmts) do
        for token in all(stmt) do
            if self:is_global(token) and not builtins[token] and not globals[token] then
                opts.on_error("Identifier '" .. token .. "' not found")
            end
        end
    end
    -- could do custom lints too
end

-- for --minify:

-- called to get all characters that won't get removed or renamed by the minifier
-- (aka, all characters other than whitespace and identifiers)
-- this is optional and doesn't affect correctness, but can slightly improve compressed size
function MySubLanguage:get_unminified_chars()
    local chars = python.list() -- could use a table, except a table can easily overflow here
    for stmt in all(self.stmts) do
        for token in all(stmt) do
            if not self:is_global(token) and not self:is_member(token) then
                for ch in all(token) do
                    chars.append(ch)
                end
            end
        end
    end
    return chars -- must return a python list (in our case - already a list)
end

-- called to get all uses of globals in the language's code
function MySubLanguage:get_global_usages()
    local usages = {}
    for stmt in all(self.stmts) do
        for token in all(stmt) do
            if self:is_global(token) then
                usages[token] = (usages[token] or 0) + 1
            end
        end
    end
    return python.dict(usages)
end
    
-- called to get all uses of members (table keys) in the language's code
function MySubLanguage:get_member_usages()
    local usages = {}
    for stmt in all(self.stmts) do
        for token in all(stmt) do
            if self:is_member(token) then
                local member = sub(token, 2)
                usages[member] = (usages[member] or 0) + 1
            end
        end
    end
    return python.dict(usages)
end

-- for very advanced languages only, see test_input/sublang.lua for details
-- def get_local_usages(self, **_):

-- called to rename all uses of globals/members/locals
function MySubLanguage:rename(opts)
    local globals = python.table(opts.globals)
    local members = python.table(opts.members)

    for stmt in all(self.stmts) do
        for i, token in ipairs(stmt) do
            if self:is_global(token) and globals[token] then
                stmt[i] = globals[token]
            elseif self:is_member(token) and members[sub(token, 2)] then
                stmt[i] = members[sub(token, 2)]
            end
        end
    end
end

-- called (after rename) to return a minified string
function MySubLanguage:minify()
    local lines = {}
    for stmt in all(self.stmts) do
        add(lines, table.concat(stmt, " ")) -- can just use table.concat
    end
    return table.concat(lines, "\n")
end

-- this is called to get a sub-languge class by name
function module.sublanguage_main(lang)
    if (lang == "evally") return MySubLanguage
end

return module
```
</details>
<br>

You can pass arguments to a sub-language as follows:
```lua
eval(--[[$language::evally myarg1 --etc]]"(omitted)")
```
Here, the `args` parameter in the constructor will be `myarg1 --etc` and can be parsed via shlex + argparse or in any other way

Furthermore, you can define sub-languages in the p8 file itself, based on existing sub-languages:
```lua
--$def-alias: evally1 = evally myarg1 --etc
eval(--[[$language::evally1 --etc2]]"(omitted)")
```
Here, the `args` parameter in the constructor will be `myarg1 --etc --etc2`

## Advanced - access to the Syntax Tree

For **really** advanced usecases, you may want to have access to the Syntax Tree of your code (from a python script) in order to, e.g. do custom linting and analysis.

Keep in mind that the syntax tree and associated APIs are not fully documented here, and aren't guaranteed not to change in the future.

The rest of the information is specific to the script language - expand the appropriate section:

<details>
<summary><b>Documentation & example for Python scripts</b></summary>

```python
# this is called after your cart is parsed into a syntax tree, but before it is transformed for minification
def preprocess_syntax_main(cart, root, on_error, args, **_):
    from pico_parse import NodeType

    if args.lint: # do some custom linting, if linting was requested in the command line
        def pre_visit(node):
            # just as an example, add a lint error on any use of 'goto'
            if node.type == NodeType.goto:
                on_error("goto used", node)
            
            # the syntax tree format isn't really documented anywhere yet. you can:
            # - check examples of use in pico_lint.py
            # - print() nodes to see what they contain (ignores some attributes for better readability)
            # - search for the NodeType you're interested in, in pico_parse.py, to see what it contains

            # print(node)

        def post_visit(node):
            pass # just here as an example

        # visit the entire syntax tree, calling pre_visit before each node, and post_visit after each node
        # extra=True allows you to visit things not apparent in the source itself, such as:
        # implicit parameters, implicit _ENV when accessing globals, etc.
        root.traverse_nodes(pre=pre_visit, post=post_visit, extra=True)
```

</details>
<br>
<details>
<summary><b>Documentation & example for Pico8 scripts</b></summary>

```lua
local module = {}

-- this is called after your cart is parsed into a syntax tree, but before it is transformed for minification
function module.preprocess_syntax_main(opts)
    local args, root, on_error = opts.args, opts.root, opts.on_error

    NodeType = python.import("pico_parse").NodeType
    TokenType = python.import("pico_tokenize").TokenType

    if args.lint then -- do some custom linting, if linting was requested in the command line
        function pre_visit(node)
            -- just as an example, add a lint error on any use of 'goto'
            if node.type == NodeType["goto"] then
                on_error("goto used", node)
            end

            -- you can use shrinko.to_fixnum/from_fixnum to work with number tokens
            if node.type == NodeType.const then
                if node.token.type == TokenType.number then
                    local fixnum = shrinko.to_fixnum(node.token.parsed_value)
                    print(tostr(fixnum, 1))
                end
            end
            
            -- the syntax tree format isn't really documented anywhere yet. you can:
            -- - check examples of use in pico_lint.py
            -- - print() nodes to see what they contain (ignores some attributes for better readability)
            -- - search for the NodeType you're interested in, in pico_parse.py, to see what it contains
            
            -- print(node)
        end

        function post_visit(node)
            -- empty, just here as an example
        end

        -- visit the entire syntax tree, calling pre_visit before each node, and post_visit after each node
        -- extra=True allows you to visit things not apparent in the source itself, such as:
        -- implicit parameters, implicit _ENV when accessing globals, etc.
        root.traverse_nodes(python.args{pre=pre_visit, post=post_visit, extra=true})
    end
end
return module
```

</details>
<br>

To run, use `--script <path>` as described [before](#custom-python-script).

You can check `pico_lint.py` for examples of how to use the syntax tree.

## Advanced - custom compiler

For **incredibly** advanced usecases, if you have a compiler that takes lua code and converts it into a string/bytecode/etc representation - you can use Shrinko8 to:
* Allow writing the lua code to be fed to the compiler as if it were regular lua code (splitting the cart between 'native' code and compiled code)
* Automate feeding the lua code to the compiler and generating the output
* Perform variable renaming on the native code, the interpreter code, and the compiled code all together

E.g. this allows renaming identifiers shared by both the native pico-8 code and the compiled language.

Switch compiler via `--$switch-compiler:` in the code:
```lua
print("hello from native pico8 code")
--$switch-compiler: repl
print("hello from compiled code")
--$switch-compiler: none
print("hello from native pico8 code again")
```

The rest of the details are specific to the language you write the script in - expand the appropriate section:

<details>
<summary><b>Documentation & example for Python scripts</b></summary>

Here is a complete example of how a compiler can be implemented: (minus the hard stuff!)
```python
from pico_process import CompilerBase

class ReplCompiler(CompilerBase):
    # A sample compiler that actually just inserts the compiled code
    # as a string argument to a p8 function
    # (E.g. could've been used for the repl at https://www.lexaloffle.com/bbs/?tid=36381)
    def __init__(self, ctxt, src, args, **_):
        self.ctxt = ctxt
        self.args = args.split()
        self.src = src
        self.id = str(id(self)) # used to identify this compiler instance inside strings

    # should return any names of dynamic includes that should be inserted in the code
    # immediately after the --$switch-compiler: (resolved via include_main)
    # for simple cases, that's just the code that runs the underlying interpreter (+ placeholder for the compiled code)
    # for complex cases, you can also include the interpreter itself - unless previously included elsewhere
    #   via an explicit --$dynamic-include: (can check via field on ctxt)
    # and you can have placeholders in the interpreter too - allowing to add more ops to the interpreter
    #   depending on what ops are used in the compiled code
    def get_dynamic_includes(self, **_):
        return ["repl.include " + self.id]
    
    # receives a syntax tree root node
    # should compile it and store the results for later use by the placeholder(s)
    def compile(self, root, **_):
        # we have two options - compile the already parsed syntax tree 
        #   (see preprocess_syntax_main in the README for how this could be done)
        # or convert it into code and reparse it via some external library, if preferred.
        #   (note - it's faster to convert to code without minifying)
        
        # here, we convert it into optionally minified code
        from pico_output import output_node
        code = output_node(root, self.ctxt, minify="+minify" in self.args)

        # we'll store the code on the ctxt, for use by the placeholder
        repl_code_dict = self.ctxt.get_field("repl_code", dict)
        if "+rom" in self.args:
            # a special mode in which the code will be encoded into rom
            # (would probably want to supply the address via self.args too)
            from pico_defs import encode_p8str
            enc_code = encode_p8str(code)
            enc_len = len(enc_code)
            self.src.cart.rom[:enc_len] = enc_code
            repl_code_dict[self.id] = f"chr(peek(0, {enc_len}))"
        else:
            # the regular mode in which the code is inserted in a string
            from pico_output import format_string_literal
            repl_code_dict[self.id] = format_string_literal(code)

# this is called by request of ReplCompiler.get_dynamic_include
def get_repl_include(args, **_):
    # since this is an include, the returned code can freely access globals/etc
    return f'execute_raw(--[[$placeholder-expr::repl.code {args}]]"", _ENV)'
    # note: can also use e.g. --[[$placeholder-stmt::repl.statements]] do end

# this is called by request of above --[[$placeholder-expr::...]], after rename but before minify
def get_repl_code(args, ctxt, **_):
    # since this is a placeholder, the returned code must not access any variables that might've been renamed
    # (it can still access _ENVs and builtins)
    repl_code_dict = ctxt.get_field("repl_code", dict)
    return repl_code_dict.get(args) # in our case, args is the compiler's id we passed through the include and the placeholder

# this is called to get any includes & placeholders for the compiler
def include_main(name, **_):
    if name == "repl.include":
        return get_repl_include
    elif name == "repl.code":
        return get_repl_code

# this is called to get a compiler class by name
def compiler_main(name, **_):
    if name == "repl":
        return ReplCompiler
```

You can see another sub-language example in Shrinko8's `scripts/split.py`.

</details>
<br>
<details>
<summary><b>Documentation & example for Pico8 scripts</b></summary>

Here is a complete example of how a compiler can be implemented: (minus the hard stuff!)
```lua
local CompilerBase = python.import("pico_process").CompilerBase
local module = {}

ReplCompiler = python.class(CompilerBase)

-- we store a table on the ctxt with all the code
function ctxt_get_repl_code_table(ctxt)
    return ctxt.get_field("repl_code", function() return {} end)
end

-- A sample compiler that actually just inserts the compiled code
-- as a string argument to a p8 function
-- (E.g. could've been used for the repl at https://www.lexaloffle.com/bbs/?tid=36381)
function ReplCompiler:__init(opts)
    self.args = {}
    for arg in all(split(opts.args, ' ')) do
        self.args[arg] = true
    end

    self.ctxt = opts.ctxt
    self.src = opts.src
    self.id = tostr(self, 1) -- used to identify this compiler instance inside strings
end

-- should return any names of dynamic includes that should be inserted in the code
-- immediately after the --$switch-compiler: (resolved via include_main)
-- for simple cases, that's just the code that runs the underlying interpreter (+ placeholder for the compiled code)
-- for complex cases, you can also include the interpreter itself - unless previously included elsewhere
--   via an explicit --$dynamic-include: (can check via field on ctxt)
-- and you can have placeholders in the interpreter too - allowing to add more ops to the interpreter
--   depending on what ops are used in the compiled code
function ReplCompiler:get_dynamic_includes()
    local includes = {"repl.include " .. self.id}
    return python.list(includes)
end

-- receives a syntax tree root node
-- should compile it and store the results for later use by the placeholder(s)
function ReplCompiler:compile(root)
    -- for p8 scripts, we currently have only one viable option -
    -- convert the syntax tree into code and reparse it via some p8 code
    -- (note - it's faster to convert to code without minifying)
    
    -- here, we convert it into optionally minified code
    local output_node = python.import("pico_output").output_node
    local minify = self.args["+minify"]
    local code = output_node(root, self.ctxt, minify)

    local repl_code_map = ctxt_get_repl_code_table(self.ctxt)
    if self.args["+rom"] then
        -- a special mode in which the code will be encoded into rom
        -- (would probably want to supply the address via self.args too)
        rommemcpy(self.src.cart.rom, 0, shrinko.to_memory(code), 0, #code)
        repl_code_map[self.id] = "chr(peek(0, "..#code.."))"
    else
        -- the regular mode in which the code is inserted in a string
        local format_string_literal = python.import("pico_output").format_string_literal
        repl_code_map[self.id] = format_string_literal(code)
    end
end

-- this is called by request of ReplCompiler.get_dynamic_include
function get_repl_include(opts)
    -- since this is an include, the returned code can freely access globals/etc
    return 'execute_raw(--[[$placeholder-expr::repl.code '..opts.args..']]"", _ENV)'
    -- note: can also use e.g. --[[$placeholder-stmt::repl.statements]] do end
end

-- this is called by request of above --[[$placeholder-expr::...]], after rename but before minify
function get_repl_code(opts)
    -- since this is a placeholder, the returned code must not access any variables that might've been renamed
    -- (it can still access _ENVs and builtins)
    local repl_code_map = ctxt_get_repl_code_table(opts.ctxt)
    return repl_code_map[opts.args] -- in our case, args is the compiler's id we passed through the include and the placeholder
end

-- this is called to get any includes & placeholders for the compiler
function module.include_main(name)
    if (name == "repl.include") return get_repl_include
    if (name == "repl.code") return get_repl_code
end

-- this is called to get a compiler class by name
function module.compiler_main(name)
    if (name == "repl") return ReplCompiler
end

return module
```

You can also see a more complete example in `scripts/parens8.lua`
</details>
<br>

You can pass arguments to a compiler as follows:
```lua
--$switch-compiler: repl +minify and more args
```
Here, the `args` parameter in the constructor will be `+minify and more args` and can be parsed via shlex + argparse or in any other way

Furthermore, you can define sub-languages in the p8 file itself, based on existing sub-languages:
```lua
--$def-alias: repl1 = repl +minify and more args
--$switch-compiler: repl1 and even more args
```
Here, the `args` parameter in the constructor will be `+minify and more args and even more args`

If you use _ENV in your compiler's interpreter, you probably want to write it as `--[[$force-safe]] _ENV` to tell Shrinko8 that this usage of _ENV should not prevent certain minifications under `--minify-safe-only`

You can use `--$dynamic-include: <...>` and `--[[$placeholder-expr::<...>]] ""`/`--[[$placeholder-stmt::<...>]] do end` for other uses outside a compiler - if you have any - but they're currently not documented by themselves.

The compiler is called whenever the cart is minified.
* To call the compiler without otherwise minifying your cart, you can pass `--minify-transform-only` in the command-line.
* To skip calling the compiler during minification, you can pass `--no-minify-transform` in the command-line.

## Contributing a script

Shrinko8 comes with some built-in scripts (as of this writing - the [split](#advanced---the-split-sub-language) and the [parens8](#saving-tokens-via-parens-8) compiler).

If you have a useful sub-language or compiler, you can open a merge-request to add it to the built-in scripts:
- Create a `scripts/YOUR_SCRIPT.py` (or `.lua`) containing your implementation
- If the script contains sublanguage_main, it will be called for `--[[$language::YOUR_SCRIPT]]` and e.g. `--[[$language::YOUR_SCRIPT.ANYTHING ANY_ARGS]]`
- If the script contains compiler_main, it will be called for `--$switch-compiler: YOUR_SCRIPT` and e.g. `--$switch-compiler: YOUR_SCRIPT.ANYTHING ANY_ARGS`
- Note that preprocess/postprocess_main are NOT called. If you need to do any cleanups, you can append a function to `ctxt.at_finish`

# Picotron Support

The support is currently still experimental, and will remain as such at least while Picotron itself is experimental.

To use, use `shrinkotron.py` instead of `shrinko8.py` - the rest is largely the same.

Options specific for Shrinktron:
* `--code-files` - specify which files to process. The default is all lua files (`*.lua`), but you can customize it, e.g. to `*.lua,!dont_touch.lua,minify_me_too.not_lua`.
* `--delete-meta` - specify which files to delete metadata for. The default is all (`*`) under `--minify` or none under `--minify-safe-only`.
* `--keep-label`, `--delete-label` - specify whether the cart label is kept or deleted. The default is to delete it only when saving a png.

Cart manipulation features:
* `--list` - list all files inside the cart.
* `--filter` - specify which files to keep in the output. E.g. can be `--filter "*,!sfx/*"` to remove all files in the sfx folder.
* `--insert` - insert a file or directory into the cart. E.g. `--insert data.bin`
    * You can specify where to place the file or directory inside the cart, e.g: `--insert data.bin misc/data_in_cart.bin`
    * You can also specify a filter for which files to take from the directory, e.g: `--insert data_dir misc/datadir_in_cart "*.lua,*.bin"`
    * Note that the filter is specified relative to the cart root, e.g: `--insert data_dir data "data/file*.bin"`
* `--extract` - extract a file or directory from the cart. E.g. `--extract main.lua` or `--extract sfx/1.sfx MyDocuments/1.sfx`
* `--merge` - merge another cart into the cart. E.g. `--merge other.p64` or `--merge other.p64 "sfx/*,gfx/*"`

Cart formats:
* p64 - Picotron cart source
* dir - Picotron cart exported into a directory
* png - Picotron cart exported into a png
* rom - Picotron cart exported into a rom
* tiny-rom - Picotron cart exported into a tiny rom (code only)
* lua - raw lua code (as main.lua)
* pod - raw POD file (for easier manipulation of single pods)
* label - A 480x270 image of a cart's label (label only)

Cart export formats:
* bin - A directory containing all exports (both binary and web). (write-only)
* html - The web export as an .html file. (read/write)
* dat - A sysrom.dat file used by binary exports, containing the cart. (read/write)

Writing export formats requires passing the picotron.dat file from your picotron directory: `--picotron-dat <path to picotron.dat>`

POD files:
By default, Shrinkotron repacks all POD files for better compression. There are options to change this:
* `--uncompress-pods` (or `-u`) - uncompress all PODs
* `--keep-pod-compression` - do not touch the PODs - keep them as-is
* `--base64-pods` - output base64 version of PODs (probably not useful unless manipulating single pods via the 'pod' format)

Notes:
* Shrinkotron assumes calls to `include` are used to include other unmodified lua files. If this is not the case, minify may break even under `--minify-safe-only`
* Shrinkotron processes the code files in `include` order, allowing you to use `--[[$const]]` globals from an included code file.
    * This requires you to use `include` with literal strings specifying an absolute path (e.g. `include "utils.lua"`).
* As Picotron evolves, there might be new globals or table keys that Shrinkotron isn't aware of. You can report such cases and use [`--preserve`](#preserving-identifiers-across-the-entire-cart) meanwhile.

# Version Changes

Starting from v1.2.7 - shrinko supports putting `$` before hint comments, aka:
* `--$preserve:` instead of `--preserve:`
* `--[[$member]]` instead of `--[[member]]`

For newly introduced hints (such as `--$switch-compiler:`), only the `$` variant is supported.

At some later version, the variant without `$` might become deprecated, so it's recommended not to use it anymore.
