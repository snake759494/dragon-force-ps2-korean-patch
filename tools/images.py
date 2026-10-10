"""그림 글자 교체: 군주 소개(엔트리 76 JPEG 0~8, 74 JPEG 0), 병법 해설(70/1, 70/3), 대륙 지도(70/2).
원본 JPEG 의 흰 글자(+어두운 테두리)를 지우고(인페인팅) 한글을 다시 그린다."""
import os, sys, io, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import data0, pack, hangul
ROOT = hangul.ROOT
FONT = os.path.join(ROOT, 'NanumSquareNeo-dEb.ttf')
FONT_B = os.path.join(ROOT, 'NanumSquareNeo-cBd.ttf')
TR = os.path.join(ROOT, 'translation', 'images.json')


def jpg_of(e, k):
    d = data0.read(e); c = pack.children(d)[k][1]
    s = c.find(b'\xff\xd8')
    return c, s, Image.open(io.BytesIO(c[s:])).convert('RGB')


def text_mask(img, box, thr=185):
    """box 안의 흰 글자 + 테두리 마스크."""
    a = np.asarray(img).astype(int)
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1]
    mx = sub.max(2); mn = sub.min(2)
    white = (mn > thr) & (mx - mn < 60)
    m = np.zeros(a.shape[:2], np.uint8)
    m[y0:y1, x0:x1] = white.astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=3)
    return m


def erase(img, boxes):
    m = np.zeros((img.height, img.width), np.uint8)
    for b in boxes: m |= text_mask(img, b)
    out = cv2.inpaint(np.asarray(img)[:, :, ::-1].copy(), m, 6, cv2.INPAINT_TELEA)
    return Image.fromarray(out[:, :, ::-1])


def draw_text(img, x, y, lines, size=21, lh=25, font=FONT, stroke=2):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(font, size)
    for i, l in enumerate(lines):
        # 그림자
        d.text((x + 2, y + i * lh + 2), l, font=f, fill=(0, 0, 0), stroke_width=stroke, stroke_fill=(0, 0, 0))
        d.text((x, y + i * lh), l, font=f, fill=(255, 255, 255), stroke_width=stroke, stroke_fill=(20, 20, 20))
    return img


def wrap_px(text, maxpx, size=21, font=FONT, indent='  '):
    f = ImageFont.truetype(font, size)
    words = text.split(' '); lines = []; cur = indent
    for w in words:
        cand = (cur + ' ' + w) if cur.strip() else cur + w
        if f.getlength(cand) <= maxpx: cur = cand
        else: lines.append(cur); cur = w
    lines.append(cur)
    return lines


def encode_jpeg(img, limit):
    """원래 크기 이하가 되는 가장 높은 품질."""
    for q in (92, 90, 88, 85, 82, 80, 76, 72, 68, 64, 60):
        b = io.BytesIO(); img.save(b, 'JPEG', quality=q, subsampling=2); b = b.getvalue()
        if len(b) <= limit: return b, q
    return b, q


def profile(e, k, title, ruler, body):
    c, s, img = jpg_of(e, k)
    img = erase(img, [(30, 25, 300, 95), (30, 100, 345, 400)])
    draw_text(img, 40, 33, [title, ruler], size=24, lh=28)
    lines = wrap_px(body, 295, size=22)
    lh = 25 if len(lines) <= 11 else 23
    draw_text(img, 38, 108, lines, size=22, lh=lh)
    return c, s, img


def rebuild_pack(e, newkids):
    d = data0.read(e); kids = pack.children(d)
    import struct
    h = struct.unpack_from('<I', d)[0]
    out = bytearray(d[:h]); offs = []
    for k, (o, c) in enumerate(kids):
        if out and len(out) % 0x40: out += b'\0' * ((-len(out)) % 0x40)
        offs.append(len(out)); out += newkids.get(k, c)
    for k, o in enumerate(offs): struct.pack_into('<I', out, 4 * k, o)
    return bytes(out)


def build():
    T = json.load(open(TR, encoding='utf-8'))
    mods = {}
    for e in (76,):
        new = {}
        for k, p in enumerate(T['profiles'] if e == 76 else [T['profiles'][0]]):
            c, s, img = profile(e, k, p['title'], p['ruler'], p['body'])
            jb, q = encode_jpeg(img, len(c) - s)
            new[k] = c[:s] + jb
        mods[e] = rebuild_pack(e, new)
    return mods


if __name__ == '__main__':
    T = json.load(open(TR, encoding='utf-8'))
    p = T['profiles'][int(sys.argv[1]) if len(sys.argv) > 1 else 1]
    c, s, img = profile(76, int(sys.argv[1]) if len(sys.argv) > 1 else 1, p['title'], p['ruler'], p['body'])
    img.save(os.path.join(ROOT, 'work', 'prof_test.png'))


def bands_of(img, x0, x1, thr=170, minh=6):
    a = np.asarray(img).astype(int); mn = a.min(2); mx = a.max(2)
    rows = ((mn > thr) & (mx - mn < 60))[:, x0:x1].sum(1)
    out = []; inb = False
    for y, v in enumerate(rows):
        if v > 3 and not inb: st = y; inb = True
        elif v <= 3 and inb:
            if y - st >= minh: out.append((st, y))
            inb = False
    return out


def red_bars(img):
    """도표 머리의 붉은 띠(작은 진형 이름 칸) y 범위."""
    a = np.asarray(img).astype(int)
    r = (a[:, 18:110, 0] > 110) & (a[:, 18:110, 1] < 60) & (a[:, 18:110, 2] < 60)
    rows = r.sum(1) > 40
    out = []; inb = False
    for y, v in enumerate(rows):
        if v and not inb: st = y; inb = True
        elif not v and inb: out.append((st, y)); inb = False
    return [b for b in out if b[1] - b[0] >= 5]


def war_page(k, spec, page_label):
    c, s, img = jpg_of(70, k)
    bands = bands_of(img, 110, 640)
    assert len(bands) == len(spec['lines']), (k, len(bands), len(spec['lines']))
    boxes = []
    for i, (y0, y1) in enumerate(bands):
        boxes.append((55 if (k == 1 and i < 4) else 112, y0 - 2, 575 if i == 0 else 636, y1 + 2))
    img = erase(img, boxes)
    d = ImageDraw.Draw(img); f = ImageFont.truetype(FONT_B, 17); fbig = ImageFont.truetype(FONT, 19)
    for i, ((y0, y1), l) in enumerate(zip(bands, spec['lines'])):
        x = 60 if (k == 1 and i < 4) else 120
        if k == 3 and i == 0: y0 = y0 + 13   # 2/2 표시와 같은 띠
        ff = fbig if (k == 1 and i == 0) else f
        if l.startswith('['):
            ff = ImageFont.truetype(FONT_B, 15); x = 122
        d.text((x + 1, y0 + 1), l, font=ff, fill=(0, 0, 0))
        d.text((x, y0), l, font=ff, fill=(255, 255, 255))
    # 작은 진형 이름 칸 (도표 머리 띠: 높이 12px)
    bars = {1: [159, 238, 318], 3: [25, 104, 184, 264, 345]}[k]
    fs = ImageFont.truetype(FONT_B, 10)
    a = np.asarray(img)
    for y0, cap in zip(bars, spec['caps']):
        bg = tuple(int(v) for v in a[y0 + 2:y0 + 10, 80:108].reshape(-1, 3).mean(0))
        d.rectangle((19, y0, 110, y0 + 11), fill=bg)
        d.text((22, y0), cap, font=fs, fill=(255, 255, 255))
    return c, s, img


def world_map(spec):
    c, s, img = jpg_of(70, 2)
    a = np.asarray(img).astype(int); mn = a.min(2); mx = a.max(2)
    white = ((mn > 190) & (mx - mn < 50)).astype(np.uint8)
    m = np.zeros(white.shape, np.uint8)
    for x, y, name in spec:
        m[y - 3:y + 18, x - 3:x + 85] = white[y - 3:y + 18, x - 3:x + 85] * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)
    out = cv2.inpaint(np.asarray(img)[:, :, ::-1].copy(), m, 4, cv2.INPAINT_TELEA)
    img = Image.fromarray(out[:, :, ::-1]); d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 13)
    for x, y, name in spec:
        d.text((x, y), name, font=f, fill=(255, 255, 255), stroke_width=2, stroke_fill=(30, 25, 20))
    return c, s, img


def build_all_images():
    T = json.load(open(TR, encoding='utf-8'))
    mods = build()
    new = {}
    for k, key in ((1, 'war1'), (3, 'war2')):
        c, s, img = war_page(k, T[key], key)
        jb, q = encode_jpeg(img, len(c) - s); new[k] = c[:s] + jb
    c, s, img = world_map(T['map'])
    jb, q = encode_jpeg(img, len(c) - s); new[2] = c[:s] + jb
    mods[70] = rebuild_pack(70, new)
    return mods
