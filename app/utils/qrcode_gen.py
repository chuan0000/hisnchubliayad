# Compact pure-Python QR Code generator producing clean SVG
# Supports Version 1-4 Byte Mode with ECC-L
import math

# GF(256) tables with primitive polynomial 0x11d
GF_EXP = [0] * 512
GF_LOG = [0] * 256
x = 1
for i in range(255):
    GF_EXP[i] = x
    GF_EXP[i + 255] = x
    GF_LOG[x] = i
    x <<= 1
    if x & 0x100:
        x ^= 0x11d

def gf_mul(x, y):
    if x == 0 or y == 0:
        return 0
    return GF_EXP[GF_LOG[x] + GF_LOG[y]]

def rs_generator_poly(degree):
    g = [1]
    for i in range(degree):
        # multiply by (x + alpha^i)
        root = GF_EXP[i]
        next_g = [0] * (len(g) + 1)
        for j in range(len(g)):
            next_g[j] ^= gf_mul(g[j], root)
            next_g[j + 1] ^= g[j]
        g = next_g
    return g

def rs_encode(data, ecc_len):
    gen = rs_generator_poly(ecc_len)
    msg = list(data) + [0] * ecc_len
    for i in range(len(data)):
        lead = msg[i]
        if lead != 0:
            for j in range(len(gen)):
                msg[i + j] ^= gf_mul(gen[j], lead)
    return msg[len(data):]

def generate_qr_matrix(text: str):
    data_bytes = text.encode('utf-8')
    data_len = len(data_bytes)
    
    # Version 2 (25x25) capacity ECC-L: 34 bytes data, 10 bytes ECC
    # Version 3 (29x29) capacity ECC-L: 55 bytes data, 15 bytes ECC
    # Version 4 (33x33) capacity ECC-L: 80 bytes data, 20 bytes ECC
    if data_len <= 32:
        ver = 2
        size = 25
        data_cap = 34
        ecc_len = 10
        align_pos = [6, 18]
    elif data_len <= 53:
        ver = 3
        size = 29
        data_cap = 55
        ecc_len = 15
        align_pos = [6, 22]
    else:
        ver = 4
        size = 33
        data_cap = 80
        ecc_len = 20
        align_pos = [6, 26]

    # Build bitstream
    bits = '0100'  # Byte mode
    bits += f'{data_len:08b}'
    for b in data_bytes:
        bits += f'{b:08b}'
    
    # Terminator
    bits += '0' * min(4, data_cap * 8 - len(bits))
    # Pad to byte boundary
    while len(bits) % 8 != 0:
        bits += '0'
    
    # Pad bytes
    pad_bytes = ['11101100', '00010001']
    pad_idx = 0
    while len(bits) < data_cap * 8:
        bits += pad_bytes[pad_idx % 2]
        pad_idx += 1
    
    data_codewords = [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]
    ecc_codewords = rs_encode(data_codewords, ecc_len)
    all_codewords = data_codewords + ecc_codewords
    
    # 2D matrix (None = unassigned, True = black, False = white)
    matrix = [[None] * size for _ in range(size)]
    reserved = [[False] * size for _ in range(size)]
    
    # Place Finder Patterns
    def place_finder(r, c):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size:
                    reserved[nr][nc] = True
                    if 0 <= dr <= 6 and 0 <= dc <= 6:
                        matrix[nr][nc] = (dr in (0, 6) or dc in (0, 6) or (2 <= dr <= 4 and 2 <= dc <= 4))
                    else:
                        matrix[nr][nc] = False

    place_finder(0, 0)
    place_finder(0, size - 7)
    place_finder(size - 7, 0)
    
    # Place Alignment Pattern if ver >= 2
    if ver >= 2:
        ar, ac = align_pos[1], align_pos[1]
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = ar + dr, ac + dc
                if not reserved[nr][nc]:
                    reserved[nr][nc] = True
                    matrix[nr][nc] = (abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0))

    # Timing patterns
    for i in range(8, size - 8):
        if not reserved[6][i]:
            reserved[6][i] = True
            matrix[6][i] = (i % 2 == 0)
        if not reserved[i][6]:
            reserved[i][6] = True
            matrix[i][6] = (i % 2 == 0)

    # Dark module
    reserved[4 * ver + 9][8] = True
    matrix[4 * ver + 9][8] = True

    # Format info area reservation
    for i in range(9):
        if not reserved[8][i]:
            reserved[8][i] = True
        if not reserved[i][8]:
            reserved[i][8] = True
    for i in range(size - 8, size):
        if not reserved[8][i]:
            reserved[8][i] = True
        if not reserved[i][8]:
            reserved[i][8] = True

    # Place data bits
    bit_idx = 0
    bit_str = ''.join(f'{cw:08b}' for cw in all_codewords)
    
    col = size - 1
    up = True
    while col > 0:
        if col == 6:
            col -= 1
        row_range = range(size - 1, -1, -1) if up else range(size)
        for r in row_range:
            for c in (col, col - 1):
                if not reserved[r][c]:
                    b_val = False
                    if bit_idx < len(bit_str):
                        b_val = (bit_str[bit_idx] == '1')
                        bit_idx += 1
                    # Mask 0: (r + c) % 2 == 0
                    if (r + c) % 2 == 0:
                        b_val = not b_val
                    matrix[r][c] = b_val
        up = not up
        col -= 2

    # Format bits for ECC-L, Mask 0: 0b111011111000100 ^ 0b101010000010010 = 010001111010110
    format_bits = "010001111010110"
    for i in range(6):
        matrix[8][i] = (format_bits[i] == '1')
    matrix[8][7] = (format_bits[6] == '1')
    matrix[8][8] = (format_bits[7] == '1')
    matrix[7][8] = (format_bits[8] == '1')
    for i in range(9, 15):
        matrix[14 - i][8] = (format_bits[i] == '1')
        
    for i in range(8):
        matrix[size - 1 - i][8] = (format_bits[i] == '1')
    for i in range(8, 15):
        matrix[8][size - 15 + i] = (format_bits[i] == '1')

    return matrix

def generate_qr_svg(text: str, size_px: int = 260) -> str:
    matrix = generate_qr_matrix(text)
    n = len(matrix)
    margin = 3
    total_cells = n + margin * 2
    cell_size = size_px / total_cells

    paths = []
    for r in range(n):
        for c in range(n):
            if matrix[r][c]:
                x = (c + margin) * cell_size
                y = (r + margin) * cell_size
                paths.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_size:.1f}" height="{cell_size:.1f}" fill="#1e293b"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size_px} {size_px}" width="{size_px}" height="{size_px}">
  <rect width="100%" height="100%" fill="#ffffff" rx="12"/>
  {''.join(paths)}
  <circle cx="{size_px/2}" cy="{size_px/2}" r="16" fill="#f59e0b" stroke="#ffffff" stroke-width="3"/>
  <text x="{size_px/2}" y="{size_px/2 + 5}" font-size="14" text-anchor="middle" fill="#ffffff" font-weight="bold">☸</text>
</svg>'''
    return svg

if __name__ == "__main__":
    svg = generate_qr_svg("http://127.0.0.1:8000/#aims?checkin=1")
    print("QR Code SVG Generated Successfully, length:", len(svg))
    assert '<svg' in svg and '<rect' in svg
