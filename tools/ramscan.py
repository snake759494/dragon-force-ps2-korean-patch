"""EE 메모리 덤프에서 적재된 DATA.0 엔트리 찾기 (16바이트 정렬 64바이트 해시)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import data0, iso

def scan(ee_path, lo=0, hi=10000, step=16):
    M = open(ee_path, 'rb').read()
    H = {}
    for a in range(0, len(M) - 64, step):
        b = M[a:a + 64]
        if b.count(0) > 48: continue
        H.setdefault(hash(b), a)
    t = data0.table(); l, s = iso.files()['/DATA.0']
    f = open(iso.ISO, 'rb'); out = []
    for i, (o, n) in sorted(t.items()):
        if not lo <= i < hi or n > 8_000_000: continue
        f.seek(l * 2048 + o); d = f.read(min(n, 0x20000))
        hits = []
        for k in range(0, len(d) - 64, 0x800):
            b = d[k:k + 64]
            if b.count(0) > 48: continue
            a = H.get(hash(b))
            if a is not None and M[a:a + 64] == b: hits.append(a - k)
            if len(hits) >= 3: break
        if hits: out.append((i, n, hits))
    return out

if __name__ == '__main__':
    for i, n, h in scan(sys.argv[1]): print(i, n, [hex(x) for x in h])
