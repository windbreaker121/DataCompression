import struct
import heapq

def read_in_chunks(file, chunk_size=65536):
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        yield chunk

def split_symbols(freq, min_freq):
    common = [0] * 256
    rare = []
    rare_count = 0

    for symbol, count in enumerate(freq):
        if count == 0:
            continue
        if count < min_freq:
            rare.append(symbol)
            rare_count += count # combined frequencies of all others
        else:
            common[symbol] = count
    return common, rare, rare_count

def build_others_subtree(rare_symbols):
    level = [[0, None, None, s] for s in rare_symbols] # frequency, left, right, symbol

    while len(level) > 1:
        nxt = []

        for i in range(0, len(level) - 1, 2):
            nxt.append([0, level[i], level[i + 1], None]) # left and right childs for internal nodes only, hence the jump 2 step

        if len(level) % 2: # odd one out is carried up a level
            nxt.append(level[-1])

        level = nxt

    return level[0] # root node to others

def build_tree(common_freq, rare_symbols, rare_count):
    heap = []
    counter = 0

    for symbol, frequency in enumerate(common_freq):
        if frequency > 0:
            node = [frequency, None, None, symbol]
            heapq.heappush(heap, (frequency, counter, node))
            counter += 1

    if rare_symbols: # there exist rare symbols
        others = build_others_subtree(rare_symbols)
        others[0] = rare_count # [rare count, left, right, root symbol = None]
        heapq.heappush(heap, (rare_count, counter, others)) # push other subtree normally into heap
        counter += 1

    if not heap:
        return {}, None

    if len(heap) == 1:
        root = heap[0][2]
        if root[3] is not None: # None = combined.
            return {root[3]: '0'}, root

    while len(heap) > 1:
        f1, _, node1 = heapq.heappop(heap)
        f2, _, node2 = heapq.heappop(heap)
        combined = f1 + f2
        node = [combined, node1, node2, None]

        heapq.heappush(heap, (combined, counter, node))
        counter += 1

    root = heap[0][2]
    codes = {}

    def assign_codes(node, code=''):
        if node is None:
            return
        if node[3] is not None:
            codes[node[3]] = code
            return
        assign_codes(node[1], code + '0')
        assign_codes(node[2], code + '1')

    assign_codes(root)
    return codes, root

def encode_chunk_to_bits(chunk, codes):
    accumulator = 0
    bit_count = 0
    packed_bytes = bytearray()

    for byte in chunk:
        for bit in codes[byte]:
            accumulator = (accumulator << 1) | (bit == '1')
            bit_count += 1
            if bit_count == 8:
                packed_bytes.append(accumulator)
                accumulator = 0
                bit_count = 0

    padding_bits = 0
    if bit_count > 0:
        padding_bits = 8 - bit_count
        packed_bytes.append(accumulator << padding_bits)

    return packed_bytes, padding_bits

def write_chunk_to_file(outfile, common_freq, rare_symbols, rare_weight,padding_bits, packed_bytes):
    common = [(s, c) for s, c in enumerate(common_freq) if c > 0]

    outfile.write(struct.pack('=BIHH', padding_bits, len(packed_bytes),len(common), len(rare_symbols)))
    for symbol, count in common:
        outfile.write(struct.pack('=BI', symbol, count))   # 5 bytes each, 1 symbol, 4 frequency

    outfile.write(bytes(rare_symbols))                      # 1 byte each
    outfile.write(struct.pack('=I', rare_weight))           # Others node weight
    outfile.write(packed_bytes)

def code(filename, chunksize=65536, min_freq=1):
    output = filename + '.compressed' if not filename.endswith(".txt") \
        else filename[:-4] + '.txt.compressed'

    with open(filename, 'rb') as infile, open(output, 'wb') as outfile:
        for chunk in read_in_chunks(infile, chunksize):
            freq = [0] * 256
            for byte in chunk:
                freq[byte] += 1

            common, rare, rare_weight = split_symbols(freq, min_freq)
            codes, _ = build_tree(common, rare, rare_weight)

            if not codes:
                continue

            packed, padding = encode_chunk_to_bits(chunk, codes)
            write_chunk_to_file(outfile, common, rare, rare_weight, padding, packed)