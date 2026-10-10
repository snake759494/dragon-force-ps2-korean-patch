"""엔트리 67 폰트에 한글 글리프를 그려 넣는다 (NanumSquareNeo ExtraBold, 32×32, 4단계)."""
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import data0, font, hangul
TTF = os.path.join(hangul.ROOT, 'NanumSquareNeo-dEb.ttf')
SIZE = 30          # 원본 한자 30×30 가득
SS = 4             # 초표본화

def render(ch, f):
    S = 32 * SS
    im = Image.new('L', (S, S)); dr = ImageDraw.Draw(im)
    # 가로는 글자 상자 가운데, 세로는 '한' 기준 상자 가운데(기준선 일정)
    bb = dr.textbbox((0, 0), ch, font=f); ref = dr.textbbox((0, 0), '한', font=f)
    x = (S - (bb[2] - bb[0])) / 2 - bb[0]
    y = (S - (ref[3] - ref[1])) / 2 - ref[1]
    dr.text((x, y), ch, 255, font=f)
    a = np.asarray(im.resize((32, 32), Image.LANCZOS)).astype(float) / 255
    return np.clip(np.round(a * 3 + 0.15), 0, 3).astype(np.uint8)

def build():
    buf = bytearray(data0.read(67))
    f = ImageFont.truetype(TTF, SIZE * SS)
    for ch, code in hangul.table().items():
        font.put(buf, font.jis_index(code), render(ch, f))
    # 작은 글꼴: 2바이트 코드 c 는 (0x8d3000 + c*64) 를 읽는다 = 이 파일 오프셋 c*64 - 0x4000 (JIS 87~94행 빈 영역)
    fs = ImageFont.truetype(TTF, 15 * SS)
    for ch in hangul.small_set():
        c = hangul.table()[ch]
        assert c < hangul.SMALL_LIMIT
        put_small(buf, c, render_small(ch, fs))
    return bytes(buf)


def render_small(ch, f):
    S = 16 * SS
    im = Image.new('L', (S, S)); dr = ImageDraw.Draw(im)
    bb = dr.textbbox((0, 0), ch, font=f); ref = dr.textbbox((0, 0), '한', font=f)
    dr.text(((S - (bb[2] - bb[0])) / 2 - bb[0], (S - (ref[3] - ref[1])) / 2 - ref[1]), ch, 255, font=f)
    a = np.asarray(im.resize((16, 16), Image.LANCZOS)).astype(float) / 255
    return np.clip(np.round(a * 3 + 0.2), 0, 3).astype(np.uint8)


def put_small(buf, c, g):
    o = c * 64 - 0x4000
    o -= o % 128 if False else 0
    o = (c // 2) * 128 - 0x4000
    blk = np.frombuffer(bytes(buf[o:o + 128]), np.uint8)
    px = np.zeros(256, np.uint8); px[0::2] = blk & 15; px[1::2] = blk >> 4
    g = g.reshape(-1).astype(np.uint8)
    px = (px & 3) | (g << 2) if c & 1 else (px & 12) | g
    buf[o:o + 128] = (px[0::2] | (px[1::2] << 4)).astype(np.uint8).tobytes()

if __name__ == '__main__':
    b = build()
    rows = []
    cs = hangul.charset()
    img = np.zeros((32 * 4, 32 * 24), np.uint8)
    for k, ch in enumerate(cs[:96]):
        g = font.get(b, font.jis_index(hangul.table()[ch])); r, c = divmod(k, 24)
        img[r * 32:r * 32 + 32, c * 32:c * 32 + 32] = g * 85
    Image.fromarray(img).save(os.path.join(hangul.ROOT, 'work', 'font_preview.png'))
