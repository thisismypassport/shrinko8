# this is called after your cart is read but before any processing is done on it:
def preprocess_main(cart, args, **_):
    print("hello from preprocess_main!")

    # copy the spritesheet from another cart
    from pico_cart import read_cart
    other_cart = read_cart("test_input/test.p8") # can be used to read p8 or png carts
    cart.rom[0x0000:0x2000] = other_cart.rom[0x0000:0x2000]

    # encode binary data into a string in our cart
    # our cart's code should contain a string like so: "$$DATA$$"
    from pico_utils import bytes_to_string_contents
    with open("test_input/binary.dat", "rb") as f:
        cart.code = cart.code.replace("$$DATA$$", bytes_to_string_contents(f.read()))

    # args.script_args contains any arguments sent to this script
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("arg", help="first arg sent to script", nargs="?")
    parser.add_argument("--my-script-opt", type=int, help="option sent to script")
    opts = parser.parse_args(args.script_args)
    print("Received args:", opts.arg, opts.my_script_opt)
    assert(opts.arg == "my-script-arg" and opts.my_script_opt == 123)

# for testing purposes
def assert_cart_equals(cart1, cart2):
    assert(cart1.code == cart2.code)
    assert(cart1.rom == cart2.rom)

# this is called before your cart is written, after it was fully processed
def postprocess_main(cart, **_):
    print("hello from postprocess_main!")

    # dump the code of the cart to be written
    from pico_defs import from_p8str, encode_p8str
    with open("test_output/out.txt", "w", encoding="utf8") as f:
        f.write(from_p8str(cart.code)) # from_p8str converts the code to unicode 
    with open("test_output/rawout.txt", "wb") as f:
        f.write(encode_p8str(cart.code)) # encode_p8str encodes the code to bytes

    # write an extra cart based on the current cart, but with a zeroed spritesheet, in both p8 and png formats
    from pico_cart import write_cart, CartFormat
    new_cart = cart.copy()
    new_cart.rom[0x0000:0x2000] = bytearray(0x2000) # zero it out
    write_cart("test_output/new_cart.p8", new_cart, CartFormat.p8)
    write_cart("test_output/new_cart.p8.png", new_cart, CartFormat.png)

    from pico_cart import read_cart
    assert_cart_equals(read_cart("test_output/new_cart.p8"), new_cart)
    assert_cart_equals(read_cart("test_output/new_cart.p8.png"), new_cart)

    # write a new cart with the same rom but custom code, in rom format
    from pico_cart import Cart, CartFormat, write_cart
    from pico_defs import to_p8str, decode_p8str
    new_cart = Cart(code=to_p8str("-- rom-only cart 🐱"), rom=cart.rom)
    write_cart("test_output/new_cart2.rom", new_cart, CartFormat.rom)

    from pico_cart import read_cart
    assert_cart_equals(read_cart("test_output/new_cart2.rom", CartFormat.rom), new_cart)

    test_str = "-- ¹²³ rom-only cart ▶ 🐱 ⬅️ ♪♪♪"
    assert(from_p8str(to_p8str(test_str)) == test_str)
    test_p8str = to_p8str(test_str)
    assert(decode_p8str(encode_p8str(test_p8str)) == test_p8str)

# this is called after your cart is parsed into a syntax tree, but before it is transformed for minification
def preprocess_syntax_main(cart, root, on_error, args, **_):
    print("hello from postprocess_syntax_main!")

    from pico_parse import NodeType

    if args.lint: # do some custom linting, if linting was requested in the command line
        def pre_visit(node):
            # just as an example, add a lint error on any use of 'goto'
            if node.type == NodeType.goto:
                on_error("goto used", node)
            
            # the syntax tree format isn't really documented anywhere yet. you can:
            # - check examples of use in pico_lint.py
            # - search for the NodeType you're interested in, in pico_parse.py to see what it contains

        def post_visit(node):
            pass # just here as an example

        # visit the entire syntax tree, calling pre_visit before each node, and post_visit after each node
        # extra=True allows you to visit things not apparent in the source itself, such as:
        # implicit parameters, implicit _ENV when accessing globals, etc.
        root.traverse_nodes(pre=pre_visit, post=post_visit, extra=True)

# internal note - yes, there is a bug in the test's output due to preprocess_main changing the code
# yet this not impacting CodeMapping.src_code; will fix if reported.
