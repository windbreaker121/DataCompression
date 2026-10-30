from encode import code
from decode import decode
 
def main():
    option = input("1. compress\n2. decompress\n")
 
    if option in ("1", "compress"):
        filename = input("file name: ")
        raw = input("min frequency for 'Others' group (blank = 1, plain Huffman): ")
        min_freq = int(raw) if raw.strip() else 1
        code(filename, min_freq=min_freq)
 
    elif option in ("2", "decompress"):
        filename = input("file name: ")
        decode(filename)
 
if __name__ == '__main__':
    main()