# this is called after your cart is read but before any processing is done on it:
def preprocess_main(cart, args, **_):
    print("hello from preprocess_main!")

    # 'cart' contains 'code' and 'rom' attributes that can be used to read or modify it
    # 'cart.code' is just a string
    # 'cart.rom' is a bytearray with some extra APIs like get16/set32/etc (see Memory in pico_defs.py)

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

# this is called before your cart is written, after it was fully processed
def postprocess_main(cart, **_):
    print("hello from postprocess_main!")

    # write a new cart with the same code but zeroed spritesheet, in both p8 and png formats
    from pico_cart import write_cart, CartFormat
    new_cart = cart.copy()
    new_cart.rom[0x0000:0x2000] = bytearray(0x2000) # zero it out
    write_cart("test_output/new_cart.p8", new_cart, CartFormat.p8)
    write_cart("test_output/new_cart.p8.png", new_cart, CartFormat.png)
