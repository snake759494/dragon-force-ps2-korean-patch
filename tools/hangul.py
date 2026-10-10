"""한글 음절 → SJIS 코드 배정. JIS 16구(0x889F)부터 차례로 한자 칸을 덮어쓴다.
기본 = KS X 1001 2,350자 + 번역문에 쓰인 나머지 음절(translation/charset_extra.txt)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import font
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
START = 15 * 94   # JIS 0x3021 = SJIS 0x889F

def ksx1001():
    out = []
    for a in range(0xb0, 0xc9):
        for b in range(0xa1, 0xff):
            out.append(bytes([a, b]).decode('euc-kr'))
    return out

SMALL_LIMIT = 0x8B40   # 이 코드 미만 = 작은 글꼴(16px)에도 글리프를 둘 수 있는 코드


def small_set():
    """작은 글꼴(반각 칸)로 그려지는 문자열에 쓰인 음절 — 앞 코드에 배정."""
    import json
    p = os.path.join(ROOT, 'translation', 'ko', 'halfkana.json')
    if not os.path.exists(p): return []
    h = json.load(open(p, encoding='utf-8'))
    return sorted(set(c for v in h.values() for c in v if '가' <= c <= '힣'))


def charset():
    small = small_set()
    cs = small + [c for c in ksx1001() if c not in set(small)]
    p = os.path.join(ROOT, 'translation', 'charset_extra.txt')
    if os.path.exists(p):
        extra = sorted(set(open(p, encoding='utf-8').read()) - set(cs))
        cs += [c for c in extra if '가' <= c <= '힣' and c not in set(small)]
    assert START + len(cs) <= 8836
    return cs

_MAP = None
def table():
    global _MAP
    if _MAP is None:
        _MAP = {c: font.index_sjis(START + k) for k, c in enumerate(charset())}
    return _MAP

def encode(s):
    """한글은 배정 코드, 나머지는 cp932. 반각 공백은 0x20."""
    m = table(); out = bytearray()
    for ch in s:
        if ch in m: out += m[ch].to_bytes(2, 'big')
        else: out += ch.encode('cp932')
    return bytes(out)

def decode(b):
    inv = {v: k for k, v in table().items()}; s = []; i = 0
    while i < len(b):
        c = b[i]
        if 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xfc:
            code = int.from_bytes(b[i:i + 2], 'big')
            s.append(inv.get(code) or b[i:i + 2].decode('cp932', 'replace')); i += 2
        else: s.append(chr(c)); i += 1
    return ''.join(s)
