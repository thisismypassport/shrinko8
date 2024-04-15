# Shrinko8

A set of Pico-8 cart tools, with a focus on shrinking code size.

## [You can run it online here.](https://thisismypassport.github.io/shrinko8)

[You can download a recent Windows Executable here.](https://github.com/thisismypassport/shrinko8/releases)

Otherwise, requires [Python](https://www.python.org/) 3.7 or above to run.

Reading/Writing PNGs additionally requires the Pillow module (`python -m pip install pillow` to install)

[Download the latest version of the source here.](https://github.com/thisismypassport/shrinko8/archive/refs/heads/main.zip)

The major supported features are:
* [Minification](#minification) - Reduce the token count, character count and compression ratio of your cart.
* [Constants](#constants) - Replace constant expressions with their value. Also removes 'if' branches with a constant condition.
* [Linting](#linting) - Check for common code errors such as forgetting to declare a local.
* [Getting Cart Size](#getting-cart-size) - Count the amount of tokens, characters, and compressed bytes your cart uses.
* [Format Conversion](#format-conversion) - Convert between p8 files, pngs, and more. Achieves better code compression than Pico-8 when creating pngs.
* [Unminification](#unminification) - Add spaces and newlines to the code of a minified cart, to make it more readable
* [Custom Python Script](#custom-python-script) - Run a custom python script to preprocess or postprocess your cart

# Minification

Greatly reduces the character count of your cart, as well as greatly improves its compression ratio (so that its compressed size is smaller) and can reduce the number of tokens as well.

There are command line [options](#minify-options) to choose how aggressively to minify, as well as what metric (compressed size or character count) to focus on minifying.

It's recommended to combine minification with conversion to png (as seen in the examples below), as Shrinko8 is able to compress code better and can thus fit carts into pngs that Pico-8 cannot.

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
* `--no-minify-reoder` : Disable reordering of statements

You can control how safe the minification is (see [details about unsafe minifications](#pitfalls-of-full-minification)):
* `--minify-safe-only` : Do only safe minification. Equivalent to specifying all of the below.
* `--rename-safe-only` : Do only safe renaming (equivalent to preserving all table keys, and - if _ENV is used in the cart - all globals)
* `--reorder-safe-only` : Do only safe statement reordering.

Additional options:

* `--preserve` :  Equivalent to specifying `--preserve:` in the cart itself. Described [here](#preserving-identifiers-across-the-entire-cart).
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

You can add a `--[[member]]` comment before a string to have the minifier rename it as if it were an identifier.

E.g:
```lua
local my_key = --[[member]]"key" -- here, key is a string but is renamed as if it were an identifier
local my_obj = {key=123} -- here, key is an identifier
?my_obj[my_key] -- success, this prints 123 even after minification
```

You can also use this with multiple keys split by comma (or any other characters):
```lua
local my_keys = split --[[member]]"key1,key2,key3" -- here, each of key1, key2 and key3 is renamed
```

And you can similarly use `--[[global]]` for globals:
```lua
local my_key = --[[global]]"glob"
glob = 123
?_ENV[my_key] -- 123
```

Advanced: if you have string literals in some special format that you're parsing into a table (like "key=val,key2=val2"), you can use [this custom python script](#example---simple-sub-language-for-table-parsing) - or a variant thereof - to allow only the keys within the string to be renamed.

### Preserving identifiers across the entire cart

You can instruct the minifier to preserve certain identifiers across the entire cart by adding a `--preserve:` comment anywhere in the code:

```lua
--preserve: my_global_1, my_global_2, update_*, *.my_member, my_env.*
```

* my_global_1 and my_global_2 will not be renamed when used as globals
* globals whose names start with `update_` will not be renamed
* my_member will not be renamed when used to index a table
* table members will not be renamed when accessed through my_env

If you prefer, you can instead pass this information in the command line, e,g:

`python shrinko8.py path-to-input.p8 path-to-output.png --minify --preserve "my_global_1, my_global_2, update_*, *.my_member, my_env.*"`

You can combine wildcards and negation (`!`) to preserve everything except some identifiers:

```lua
--preserve: *.*, !*.my_*
```

* Only identifiers starting with `my_` will be renamed when used to index a table

### Renaming table keys the same way as globals

You can instruct the minifier to rename table keys the same way as globals (allowing you to freely mix _ENV and other tables), by adding the following comment in the code:

```lua
--preserve: *=*.*
```

If you prefer, you can instead pass `--preserve "*=*.*"` to the command line.

### Controlling renaming of all keys of a table

You can use `--[[preserve-keys]]`, `--[[global-keys]]` and `--[[member-keys]]` to affect how *all* keys of a table are renamed.

This can be applied on either table constructors (aka `{...}`) or on variables. When applying on variables, the hint affects all members accessed through that variable, as well as any table constructors directly assigned to it.
```lua
local --[[preserve-keys]]my_table = {preserved1=1, preserved2=2}
my_table.preserved1 += 1 -- all member accesses through my_table are preserved
?my_table["preserved1"]

-- here, {preserved3=3} is not directly assigned to my_table and so needs its own hint
my_table = setmetatable(--[[preserve-keys]]{preserved3=3}, my_meta)
?my_table["preserved3"]

-- while assigning directly to _ENV no longer requires a hint, indirect assignment like below does:
local env = --[[global-keys]]{assert=assert, add=add}
do
  local _ENV = env
  assert(add({}, 1) == 1)
end
```

This can be also be useful when assigning regular tables to _ENV:
```lua
-- hints on an _ENV local affects all globals in its scope
for --[[member-keys]]_ENV in all({{x=1,y=5}, {x=2,y=6}}) do
  x += y + y*x
end
```

### Advanced - Controlling renaming of specific identifier occurrences

The `--[[global]]`, `--[[member]]` and `--[[preserve]]` hints can also be used on a **specific** occurrence of an identifier to change the way it's renamed.

Usually, there are easier ways to control renaming (such as by [preserving identifiers across the entire cart](#preserving-identifiers-across-the-entire-cart) or [controlling renaming of all keys in a table](#controlling-renaming-of-all-keys-of-a-table)), but this option is here for cases where you need precise control over how to rename each occurence.

```lua
do
  -- NOTE: can be more easily achieved via --[[global-keys]]
  local _ENV = {--[[global]]assert=assert}
  assert(true)
end
-- NOTE: can be more easily achieved via --[[member-keys]]
for _ENV in all({{x=1}, {x=2}}) do
  --[[member]]x += 1
end
```

### Advanced - Renaming Built-in Pico-8 functions

For cases like tweet-carts, when you use a builtin function multiple times throughout your cart, you often want to assign it to a shorter name at the beginning of the cart. With shrinko8, you can keep using the full name of the builtin, but tell the minifer to only preserve the builtin when it's first accessed, as follows:

```lua
--preserve: !circfill, !rectfill
circfill, rectfill = --[[preserve]]circfill, --[[preserve]]rectfill
circfill(10,10,20); circfill(90,90,30)
rectfill(0,0,100,100); rectfill(20,20,40,40)
```

Above, all uses of circfill and rectfill are renamed except for the ones preceded by `--[[preserve]]`

Be aware that doing this won't reduce the compressed size of the cart, and will increases the token count (due to the assignment), so it's only for when you care about character count above all else.

### Advanced - Explicit renaming

While Shrinko8 has good heuristics for choosing identifier names, it's still possible to improve upon them when hand-minifying carts (useful especially when trying to fit small carts under some chosen limit).

In order to still be able to use Shrinko8 in such cases, a hint is provided to instruct Shrinko8 how to rename specific variables:

```lua
function --[[rename::f]]func(--[[rename::a]]arg)
    local --[[rename::b]]val = arg
end
```

A rename hint affects all instances of the marked variable.

## Prevent merging of specific statements

You can insert `--[[no-merge]]` between two statements to ensure they're not merged, e.g:

```lua
-- note: this example requires --focus-tokens to see the effect
local weird_table = setmetatable({add_me=0}, {
    __newindex=function(tbl, key, val) rawset(tbl, key, val + t.add_me) end
})
-- the following statements do not do the same thing if combined into one
-- aka: weird_table.add_me, weird_table.new_key = 3, 4
-- so we can add --[[no-merge]] between them to ensure they're not merged.
weird_table.add_me = 3
--[[no-merge]]
weird_table.new_key = 4
```

## Keeping comments

You can keep specific comments in the output via:

```lua
--keep: This is a comment to keep
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

In addition, variables that are declared with the `--[[const]]` hint are treated as constants:

```lua
--[[const]] k_hero_spr = 4
spr(k_hero_spr, x, y)
-- becomes:
spr(4, x, y)

--[[const]] version = 'v1.2'
?'version: '..version
-- becomes:
?'version: v1.2'

-- the --[[const]] hint can apply to either individual variables or entire local statements
--[[const]] local k_rock,k_box,k_wall = 4,5,6
objs={k_rock,k_wall,k_wall,k_box}
-- becomes:
objs={4,6,6,5}

-- some builtin functions can be used inside const declarations
--[[const]] k_value = 2.5
--[[const]] derived = flr(mid(k_value, 1, 5))
?derived
-- becomes:
?2
```

Furthermore, constant `if` and `elseif` branches are removed appropriately, allowing you to easily keep debug code in your source files, enabling it by simply changing the value of a variable:

```lua
--[[const]] TRACE = false
--[[const]] DEBUG = true

if (TRACE) ?"something happened!"
if DEBUG then
  spr(debug_spr, 10, 10)
end

-- becomes:
spr(debug_spr,10,10)
```

Some details to keep in mind:
* *Local* variables that **aren't** declared as `--[[const]]` may still be treated as constants in cases where it's safe & advantageous to do so.
* *Local* variables that **are** declared as `--[[const]]` still follow the usual lua scoping rules. They cannot be reassigned but new locals with the same name can be defined.
* *Global* variables that **aren't** declared as `--[[const]]` are currently never treated as constants.
* *Global* variables that **are** declared as `--[[const]]` are assumed to *always* have their constant value. They cannot be reassigned and can only be used below their declaration.

## Passing constants via command line

You can even declare constants in the command line, if you prefer:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --minify-safe-only --const DEBUG true --const SPEED 2.5 --str-const VERSION v1.2`

```lua
--[[CONST]] SPEED = 0.5 -- default value
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

Keep in mind that in some cases, Shrinko8 will play it safe and avoid a computation whose result is questionable or has a high potential to change between pico8 versions. If this prevents a `--[[const]]` variable from being assigned a constant, Shrinko8 will warn about this:

```lua
-- here, abs overflows (due to receiving -0x8000), and shrinko8 chooses not to rely on the overflow behaviour
--[[const]] x = abs(0x7fff+1)-1
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
* You can prevent treating specific variables as constants by declaring them with a `--[[non-const]]` hint. (though normally, there is no reason to do this)

# Linting

Linting finds common code issues in your cart, like forgetting to use a 'local' statement

## To lint your p8 cart:

`python shrinko8.py path-to-input.p8 --lint`

You can combine linting with other operations:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --lint --count --minify`

## Linting options

You can disable certain lints globally via additional command-line options:

* `--no-lint-unused` : Disable lint on unused variables
* `--no-lint-duplicate` : Disable lint on duplicate variable names
* `--no-lint-undefined` : Disable lint on undefined variables

Normally, a lint failure prevents cart creation, but `--no-lint-fail` overrides that.

Normally, lint errors are displayed in a format useful for external editors, showing the line number in the whole .p8 file. However, you can use `--error-format tabbed` to show the pico8 tab number and line number inside that tab instead.

Misc. options:

* `--lint-global` : Equivalent to specifying `--lint:` inside the cart itself

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

Tell the linter about the globals it didn't see you define via the `--lint:` hint:
```lua
--lint: global_1, global_2
function f()
    dostuff(global_1, global_2)
end
```

Tell the linter to allow you to define globals (by assigning to them) in a specific function via the `--lint: func::_init` hint:
```lua
--lint: func::_init
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

# Unminification

You can undo some of the effects of minification, or just reformat the cart's code in a consistent manner:

`python shrinko8.py path-to-input.p8 path-to-output.p8 --unminify`

Of course, renaming cannot be undone, so the resulting code may still not be readable.

Options:

* `--unminify-indent` : Specify the size of the indentation to use (default: 2)

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

    # dump the code of the cart to be written
    from pico_defs import from_p8str
    with open("out.txt", "w", encoding="utf8") as f:
        f.write(from_p8str(cart.code)) # from_p8str converts the code to unicode

    # write an extra cart based on the current cart, but with a zeroed spritesheet, in both p8 and png formats
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
-- (implementation of splitkeys omitted)
local table = splitkeys(--[[language::splitkeys]]"key1=val1,key2=val2,val3,val4")
?table.key1 -- "val1"
?table[1] -- "val3"
```

To run, use `--script <path>` as before.
