import struct
from encode import build_tree
 
def read_bytes(infile, header_format='=BIHH'):
    header_size = struct.calcsize(header_format)
 
    while True:
        header = infile.read(header_size)
        if not header:
            break
 
        padding, payload_len, common_count, rare_count = struct.unpack(header_format, header)
 
        common_freq = [0] * 256
        for _ in range(common_count):
            symbol, count = struct.unpack('=BI', infile.read(5))
            common_freq[symbol] = count
 
        rare_symbols = list(infile.read(rare_count))
        (rare_weight,) = struct.unpack('=I', infile.read(4))
 
        payload = infile.read(payload_len)
        yield padding, common_freq, rare_symbols, rare_weight, payload
 
 
def huffman_decode(rootNode, payload, padding):
    decoded = bytearray()
    if not rootNode:
        return decoded
 
    bits = []
    for byte in payload:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    if padding > 0:
        bits = bits[:-padding]
 
    # chunk with a single unique symbol: root is a leaf
    if rootNode[1] is None and rootNode[2] is None:
        return bytearray([rootNode[3]] * len(bits))
 
    node = rootNode
    for bit in bits:
        node = node[2] if bit else node[1]
        if node[3] is not None:      # leaf (works for Others-subtree leaves too)
            decoded.append(node[3])
            node = rootNode
    return decoded
 
 
def decode(filename):
    suffix = ".txt.compressed"
    base = filename[:-len(suffix)] if filename.endswith(suffix) else filename
    output_file = base + ".decompressed.txt"
 
    with open(filename, 'rb') as infile, open(output_file, 'wb') as outfile:
        for padding, common, rare, rare_weight, payload in read_bytes(infile):
            _, rootNode = build_tree(common, rare, rare_weight)
            outfile.write(huffman_decode(rootNode, payload, padding))