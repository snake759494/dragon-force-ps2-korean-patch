"""ISO9660 읽기 도우미 (DVD, 2048 바이트 섹터)."""
import os, struct
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ISO = os.path.join(ROOT, 'Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan).iso')
OUT = os.path.join(ROOT, 'Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan) (Korean).iso')

def read(lba, size, iso=ISO):
    with open(iso, 'rb') as f:
        f.seek(lba * 2048); return f.read(size)

def walk(iso=ISO):
    """(경로, lba, size, 디렉터리레코드 위치) 목록."""
    pvd = read(16, 2048, iso)
    rlba, rsize = struct.unpack_from('<I', pvd, 158)[0], struct.unpack_from('<I', pvd, 166)[0]
    res = []
    def rec(lba, size, path):
        data = read(lba, size, iso); p = 0
        while p < len(data):
            n = data[p]
            if n == 0:
                p = (p // 2048 + 1) * 2048; continue
            l, s = struct.unpack_from('<I', data, p + 2)[0], struct.unpack_from('<I', data, p + 10)[0]
            fl = data[p + 25]; nl = data[p + 32]; name = data[p + 33:p + 33 + nl]
            if name not in (b'\0', b'\1'):
                nm = name.decode('latin1').split(';')[0]
                if fl & 2: rec(l, s, path + nm + '/')
                else: res.append((path + nm, l, s, lba * 2048 + p))
            p += n
    rec(rlba, rsize, '/')
    return res

FILES = None
def files():
    global FILES
    if FILES is None: FILES = {p: (l, s) for p, l, s, _ in walk()}
    return FILES

def readfile(path, iso=ISO):
    l, s = files()[path]; return read(l, s, iso)

if __name__ == '__main__':
    for p, l, s, _ in sorted(walk(), key=lambda x: x[1]): print(f'{l:8d} {s:11d} {p}')
