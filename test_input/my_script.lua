local module = {}

-- this is called after your cart is read but before any processing is done on it:
function module.preprocess_main(opts)
    local cart, args, ctxt = opts.cart, opts.args, opts.ctxt
    print("hello from preprocess_main!")

    -- copy the spritesheet from another cart
    local read_cart = python.import("pico_cart").read_cart
    local other_cart = read_cart("test_input/test.p8") -- can be used to read p8 or png carts
    cart.rom.set_block(0x0000, other_cart.rom.get_block(0x0000, --[[this is a length!]] 0x2000))

    -- encode binary data into a string in our cart
    -- our cart's code should contain a string like so: "$$DATA$$"
    local bytes_to_string_contents = python.import("pico_utils").bytes_to_string_contents
    local fh = io.open("test_input/binary.dat", "rb") -- lua io/os/etc are available too
    local contents = bytes_to_string_contents(fh:read("*a"))
    cart.code = string.gsub(cart.code, "%$%$DATA%$%$", string.gsub(contents, "%%", "%%%%")) -- gsub is stupid to use with arbitrary strings - but that's lua
    fh:close()

    -- args.script_args contains any arguments sent to this script
    local argopts = args.script_args
    assert(argopts[0] == "my-script-arg" and argopts[1] == "--my-script-opt" and argopts[2] == "123")
    
    -- ctxt contains some read-only information like `lang`, `version` and `builtins`
    -- you can also use ctxt.get/set_field to store extra information on it to pass between different stages
    -- (use a unique field name to avoid conflicts)
    ctxt:set_field("my_script_data", {argopts, other_cart})
end

-- for testing purposes
function assert_cart_equals(cart1, cart2)
    assert(cart1.code == cart2.code)
    assert(cart1.rom == cart2.rom)
end

-- this is called before your cart is written, after it was fully processed
function module.postprocess_main(opts)
    local cart, ctxt = opts.cart, opts.ctxt
    print("hello from postprocess_main!")
    
    local pico_cart = python.import("pico_cart")

    -- dump the code of the cart to be written
    local fh = io.open("test_output/out.txt", "w")
    fh:write(shrinko.from_p8str(cart.code)) -- from_p8str converts the code to unicode (use from shrinko, NOT from pico_defs)
    fh:close()

    local fh = io.open("test_output/rawout.txt", "wb")
    fh:write(cart.code) -- or you can write it as bytes, without encoding
    fh:close()

    -- write an extra cart based on the current cart, but with a zeroed spritesheet, in both p8 and png formats
    local new_cart = cart.copy()
    new_cart.rom.fill8(0x0000, 0, 0x2000) -- zero it out
    pico_cart.write_cart("test_output/new_cart.p8", new_cart, pico_cart.CartFormat.p8)
    pico_cart.write_cart("test_output/new_cart.p8.png", new_cart, pico_cart.CartFormat.png)

    assert_cart_equals(pico_cart.read_cart("test_output/new_cart.p8"), new_cart)
    assert_cart_equals(pico_cart.read_cart("test_output/new_cart.p8.png"), new_cart)

    -- write a new cart with the same rom but custom code, in rom format
    local new_cart = pico_cart.Cart("-- rom-only cart 🐱", cart.rom)
    pico_cart.write_cart("test_output/new_cart2.rom", new_cart, pico_cart.CartFormat.rom)

    assert_cart_equals(pico_cart.read_cart("test_output/new_cart2.rom", pico_cart.CartFormat.rom), new_cart)

    local test_p8str = "-- ¹²³ rom-only cart ▶ 🐱 ⬅️ ♪♪♪"
    assert(shrinko.to_p8str(shrinko.from_p8str(test_p8str)) == test_p8str)
    
    -- can use the data stored in the preprocess stage:
    local argopts = ctxt:get_field("my_script_data")[1]
    assert(argopts[0] == "my-script-arg" and argopts[2] == "123")
end

-- this is called after your cart is parsed into a syntax tree, but before it is transformed for minification
function module.preprocess_syntax_main(opts)
    local args, root, on_error = opts.args, opts.root, opts.on_error
    print("hello from postprocess_syntax_main!")

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
                    assert(node.token.parsed_value == shrinko.from_fixnum(fixnum))
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