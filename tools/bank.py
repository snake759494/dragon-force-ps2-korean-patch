"""메시지 뱅크: [키 u32×N][오프셋 BE u32×N][본문]. 키·오프셋 위치는 파일마다 다름(자동 탐지)."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))

def parse(d):
    n = len(d) // 4
    w = struct.unpack('>%dI' % n, d[:n * 4])
    best = None
    i = 0
    while i < n:
        if w[i] == 0:
            while i + 1 < n and w[i + 1] == 0: i += 1
            j = i
            while j + 1 < n and w[j] <= w[j + 1] < len(d) and w[j + 1] - w[j] < 0x2000: j += 1
            cnt = j - i + 1
            if cnt >= 16 and (best is None or w[j] > best[2]): best = (i * 4, cnt, w[j])
            i = j + 1
        else: i += 1
    toff, N, _ = best
    offs = list(w[toff // 4: toff // 4 + N])
    p = toff + 4 * N
    while d[p] == 0: p += 1
    base = p
    # 마지막 항목 끝: 파일 끝의 0 패딩 제외
    end = len(d)
    while d[end - 1] == 0: end -= 1
    ents = []
    for k in range(N):
        a = base + offs[k]; b = base + offs[k + 1] if k + 1 < N else end
        ents.append(d[a:b])
    return dict(toff=toff, N=N, base=base, end=end, ents=ents)

def build(d, info, ents, limit=None):
    out = bytearray(d[:info['base']])
    offs = []; body = bytearray()
    for e in ents:
        offs.append(len(body)); body += e
    for k, o in enumerate(offs): struct.pack_into('>I', out, info['toff'] + 4 * k, o)
    out += body
    # 원래 길이 이상, 0x800 정렬 패딩
    n = max(len(out), len(d)) if limit is None else len(out)
    out += b'\0' * ((-len(out)) % 0x800)
    if len(out) < len(d): out += b'\0' * (len(d) - len(out))
    return bytes(out)

def show(b):
    s = []; i = 0
    while i < len(b):
        c = b[i]
        if 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xfc:
            s.append(b[i:i + 2].decode('cp932', 'replace')); i += 2
        elif c == 0x0d: s.append('⏎'); i += 1
        elif c < 0x20 or c >= 0x7f: s.append('{%02X}' % c); i += 1
        else: s.append(chr(c)); i += 1
    return ''.join(s)
