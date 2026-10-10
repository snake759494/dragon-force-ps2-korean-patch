"""SJIS 바이트열 ↔ 번역용 유니코드 표기.
제어: {10}{xx} → ⟦V xx⟧ (변수), {07}{xx} → ⟦S xx⟧ (속도), 기타 0x00~0x1f → ⟦XX⟧. 반각 카나 등 cp932 외 바이트 → ⟦XX⟧."""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))

def to_text(b, two=(0x10, 0x07)):
    out = []; i = 0
    while i < len(b):
        c = b[i]
        if 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xfc:
            try: out.append(b[i:i + 2].decode('cp932')); i += 2; continue
            except UnicodeDecodeError: out.append('⟦%02X⟧' % c); i += 1; continue
        if c in two and i + 1 < len(b):
            out.append('⟦%s %02X⟧' % ('V' if c == 0x10 else 'S', b[i + 1])); i += 2; continue
        if c < 0x20 or c >= 0x7f:
            if 0xa1 <= c <= 0xdf: out.append(bytes([c]).decode('cp932')); i += 1; continue
            out.append('⟦%02X⟧' % c); i += 1; continue
        out.append(chr(c)); i += 1
    return ''.join(out)

TAG = re.compile(r'⟦(?:([VS]) )?([0-9A-F]{2})⟧')
def from_text(s, enc):
    """enc: 일반 문자 인코더(hangul.encode)."""
    out = bytearray(); p = 0
    for m in TAG.finditer(s):
        out += enc(s[p:m.start()])
        k, h = m.group(1), int(m.group(2), 16)
        if k == 'V': out += bytes([0x10, h])
        elif k == 'S': out += bytes([0x07, h])
        else: out.append(h)
        p = m.end()
    out += enc(s[p:])
    return bytes(out)
