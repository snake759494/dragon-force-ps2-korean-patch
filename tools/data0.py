"""DATA.0 아카이브: 0xa000 바이트 u32 오프셋 표(인덱스→바이트 오프셋, 0=없음). 크기 = 다음 유효 오프셋 - 현재."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import iso
HDR = 0xa000

def table(raw=None):
    l, s = iso.files()['/DATA.0']
    raw = raw or iso.read(l, HDR)
    v = struct.unpack('<%dI' % (HDR // 4), raw[:HDR])
    idx = [(i, o) for i, o in enumerate(v) if o]
    ents = {}
    for k, (i, o) in enumerate(idx):
        end = idx[k + 1][1] if k + 1 < len(idx) else s
        ents[i] = (o, end - o)
    return ents

def read(i):
    l, s = iso.files()['/DATA.0']
    o, n = table()[i]
    with open(iso.ISO, 'rb') as f:
        f.seek(l * 2048 + o); return f.read(n)

def rebuild_into(f, mods, start_lba):
    """열린 ISO f(r+b)의 start_lba 에 DATA.0 을 새로 쓴다. mods: {인덱스: bytes}. 순서 유지, 0x800 정렬.
    반환: 새 DATA.0 크기."""
    l, s = iso.files()['/DATA.0']
    src = open(iso.ISO, 'rb')
    src.seek(l * 2048); hdr = bytearray(src.read(HDR))
    v = list(struct.unpack('<%dI' % (HDR // 4), hdr))
    order = sorted((o, i) for i, o in enumerate(v) if o)
    t = table()
    pos = HDR
    newoff = {}
    f.seek(start_lba * 2048 + HDR)
    for o, i in order:
        if i in mods: d = mods[i]
        else:
            src.seek(l * 2048 + o); d = src.read(t[i][1])
        d = d + b'\0' * ((-len(d)) % 0x800)
        newoff[i] = pos; f.write(d); pos += len(d)
    for i, o in newoff.items(): v[i] = o
    f.seek(start_lba * 2048); f.write(struct.pack('<%dI' % (HDR // 4), *v))
    return pos
