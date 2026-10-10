"""전투 제목 그림(陣形選択·一騎討ち) = 엔트리 17 안의 새턴 4bpp 스프라이트(상위 니블 먼저). 780 에 같은 구간 사본.
색: 행마다 위→아래 그라데이션 번호(f→5), 2 = 테두리, 3·4 = 그림자."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import data0, hangul

TITLES = [  # (17 오프셋, 폭, 높이, 한국어, 기울기)
    (0x14af19, 96, 23, '진형선택', 0.0),
    (0x14a55e, 136, 31, '일기토', 0.25),
]


def unpack(b, w, h):
    a = np.frombuffer(b, np.uint8)
    p = np.zeros(len(a) * 2, np.uint8); p[0::2] = a >> 4; p[1::2] = a & 15
    return p.reshape(h, w)


def pack(p):
    p = p.reshape(-1)
    return ((p[0::2] << 4) | p[1::2]).astype(np.uint8).tobytes()


def mask(text, w, h, shear):
    from PIL import Image, ImageDraw, ImageFont
    SS = 4; font = os.path.join(hangul.ROOT, 'SeoulHangangEB.ttf')
    for sz in range(h, 8, -1):
        f = ImageFont.truetype(font, sz * SS)
        im = Image.new('L', (w * SS * 2, h * SS)); d = ImageDraw.Draw(im)
        bb = d.textbbox((0, 0), text, font=f, spacing=0)
        tw = bb[2] - bb[0] + int(h * SS * shear); th = bb[3] - bb[1]
        if tw <= (w - 6) * SS and th <= (h - 3) * SS: break
    x0 = (w * SS - tw) // 2 - bb[0] + int(h * SS * shear)
    d.text((x0, (h * SS - th) // 2 - bb[1] - SS // 2), text, 255, font=f)
    if shear:
        im = im.transform(im.size, Image.AFFINE, (1, shear, -shear * h * SS, 0, 1, 0), Image.BICUBIC)
    im = im.crop((0, 0, w * SS, h * SS)).resize((w, h), Image.LANCZOS)
    return np.asarray(im) > 110


def draw(orig, text, shear):
    h, w = orig.shape
    # 행별 채움색: 원본 그 행에서 가장 흔한 5 이상 번호
    grad = []
    for y in range(h):
        v = orig[y][orig[y] >= 5]
        grad.append(np.bincount(v).argmax() if len(v) else (grad[-1] if grad else 15))
    m = mask(text, w, h, shear)
    out = np.zeros((h, w), np.uint8)
    sh = np.zeros_like(m); sh[1:, 1:] = m[:-1, :-1]
    ol = np.zeros_like(m)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ol |= np.roll(np.roll(m, dy, 0), dx, 1)
    out[sh & ~m] = 3
    out[ol & ~m] = 2
    for y in range(h): out[y][m[y]] = grad[y]
    return out


def build(mods):
    d17 = bytearray(mods.get(17) or data0.read(17))
    d780 = bytearray(mods.get(780) or data0.read(780))
    for o, w, h, ko, shear in TITLES:
        n = w * h // 2
        new = pack(draw(unpack(bytes(d17[o:o + n]), w, h), ko, shear))
        q = data0.read(780).find(data0.read(17)[o:o + n])      # 780 사본 위치(제목마다 다름)
        assert q >= 0
        d17[o:o + n] = new; d780[q:q + n] = new
    mods[17] = bytes(d17); mods[780] = bytes(d780)
