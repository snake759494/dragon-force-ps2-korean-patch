"""GS 전송 패킷 텍스처: [0x30B 머리][GIF A+D(BITBLTBUF/TRXPOS/TRXREG/TRXDIR) + IMAGE]… (팔레트, 본그림 순).
머리: +0x18 팔레트 w,h(u16), +0x28 그림 w,h(u16)."""
import struct
import numpy as np


def transfers(d, start=0x30):
    """→ [dict(psm, w, h, dbp, dbw, x, y, off, size)]  off/size = d 안의 이미지 자료 위치."""
    out = []; p = start; cur = {}
    while p + 16 <= len(d):
        lo, hi = struct.unpack_from('<QQ', d, p)
        nloop = lo & 0x7fff; eop = (lo >> 15) & 1; flg = (lo >> 58) & 3; nreg = (lo >> 60) & 15 or 16
        p += 16
        if flg == 0:   # PACKED (A+D)
            for i in range(nloop * nreg):
                data, addr = struct.unpack_from('<QQ', d, p); p += 16
                addr &= 0xff
                if addr == 0x50:
                    cur['dbp'] = (data >> 32) & 0x3fff; cur['dbw'] = (data >> 48) & 0x3f; cur['psm'] = (data >> 56) & 0x3f
                elif addr == 0x51:
                    cur['x'] = (data >> 32) & 0x7ff; cur['y'] = (data >> 48) & 0x7ff
                elif addr == 0x52:
                    cur['w'] = data & 0xfff; cur['h'] = (data >> 32) & 0xfff
        elif flg == 2:   # IMAGE
            n = nloop * 16
            t = dict(cur); t['off'] = p; t['size'] = n; out.append(t)
            p += n
        else:
            break
        if eop and flg == 2 and len(out) >= 2: pass
        if p >= len(d) or (lo == 0 and hi == 0): break
    return out


def csm1(pal):
    """8비트 팔레트 CSM1 배치 → 순서대로."""
    idx = np.arange(256)
    j = (idx & ~0x18) | ((idx & 0x08) << 1) | ((idx & 0x10) >> 1)
    return pal[j]


def decode(d):
    """→ (RGBA ndarray, 정보). 8/4비트는 팔레트 적용."""
    ts = transfers(d)
    img = ts[-1]; raw = d[img['off']:img['off'] + img['size']]
    w, h, psm = img['w'], img['h'], img['psm']
    if psm == 0:
        a = np.frombuffer(raw, np.uint8)[:w * h * 4].reshape(h, w, 4).copy()
    elif psm == 1:
        a = np.frombuffer(raw, np.uint8)[:w * h * 3].reshape(h, w, 3)
        a = np.concatenate([a, np.full((h, w, 1), 0x80, np.uint8)], 2)
    elif psm in (0x13, 0x14):
        pt = ts[0]; praw = d[pt['off']:pt['off'] + pt['size']]
        pal = np.frombuffer(praw, np.uint8)[:pt['w'] * pt['h'] * 4].reshape(-1, 4)
        if psm == 0x13:
            pal = csm1(pal[:256]); ix = np.frombuffer(raw, np.uint8)[:w * h]
        else:
            b = np.frombuffer(raw, np.uint8)[:w * h // 2]
            ix = np.zeros(w * h, np.uint8); ix[0::2] = b & 15; ix[1::2] = b >> 4
        a = pal[ix].reshape(h, w, 4)
    else:
        raise ValueError('psm %x' % psm)
    return a, img


def to_image(a):
    from PIL import Image
    b = a.copy().astype(np.int32)
    b[..., 3] = np.clip(b[..., 3] * 2, 0, 255)
    return Image.fromarray(b.astype(np.uint8), 'RGBA')
