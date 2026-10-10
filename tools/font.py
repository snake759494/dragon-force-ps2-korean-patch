"""엔트리 67 SJIS 폰트: JIS 94×94 순서, 글리프 32×32 2bpp, 512B 블록에 두 글리프(하위2비트=짝수, 상위2비트=홀수)."""
import numpy as np, sys, os
sys.path.insert(0, os.path.dirname(__file__))
W = 32

def jis_index(sj):
    """SJIS 2바이트 코드 → 0부터의 JIS 인덱스."""
    a, b = sj >> 8, sj & 0xff
    if a >= 0xe0: a -= 0x40
    row = (a - 0x81) * 2
    if b >= 0x9f: row += 1; col = b - 0x9f
    else: col = b - 0x40 - (1 if b >= 0x80 else 0)
    return row * 94 + col

def index_sjis(idx):
    row, col = divmod(idx, 94)
    a = 0x81 + row // 2
    if a >= 0xa0: a += 0x40
    if row % 2: b = 0x9f + col
    else: b = 0x40 + col + (1 if col >= 0x3f else 0)
    return (a << 8) | b

def get(data, idx):
    blk = np.frombuffer(data, np.uint8, 512, (idx // 2) * 512)
    px = np.zeros(1024, np.uint8); px[0::2] = blk & 15; px[1::2] = blk >> 4
    return ((px >> 2) & 3 if idx & 1 else px & 3).reshape(32, 32)

def put(buf, idx, g):
    """g: 32×32 값 0..3"""
    o = (idx // 2) * 512
    blk = np.frombuffer(bytes(buf[o:o + 512]), np.uint8)
    px = np.zeros(1024, np.uint8); px[0::2] = blk & 15; px[1::2] = blk >> 4
    g = g.reshape(-1).astype(np.uint8)
    if idx & 1: px = (px & 3) | (g << 2)
    else: px = (px & 12) | g
    buf[o:o + 512] = (px[0::2] | (px[1::2] << 4)).astype(np.uint8).tobytes()
