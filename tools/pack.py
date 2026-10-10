"""DATA.0 안의 중첩 묶음: [u32 오프셋...(첫 값=헤더 크기 0x40/0x200/0x400), 0] + 자료."""
import struct

def is_pack(d):
    if len(d) < 16: return False
    h = struct.unpack_from('<I', d)[0]
    if h not in (0x40, 0x200, 0x400, 0x800) or h > len(d): return False
    offs = []
    for i in range(0, h, 4):
        v = struct.unpack_from('<I', d, i)[0]
        if v == 0: break
        offs.append(v)
    return len(offs) >= 1 and all(a <= b for a, b in zip(offs, offs[1:])) and offs[-1] <= len(d)

def children(d):
    h = struct.unpack_from('<I', d)[0]; offs = []
    for i in range(0, h, 4):
        v = struct.unpack_from('<I', d, i)[0]
        if v == 0: break
        offs.append(v)
    offs.append(len(d))
    return [(offs[k], d[offs[k]:offs[k + 1]]) for k in range(len(offs) - 1)]

def walk(d, path='', depth=0):
    if depth < 4 and is_pack(d):
        for k, (o, c) in enumerate(children(d)):
            yield from walk(c, '%s/%d' % (path, k), depth + 1)
    else:
        yield path, d
