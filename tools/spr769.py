"""엔트리 769 = 전투 화면 이탤릭 글자 스프라이트(새턴 VDP1 4bpp, 상위 니블 먼저, 높이 16, 폭 8의 배수) 연속 배치.
VDP1 VRAM 0x14000 에 적재. 동적계획으로 경계를 추정한다(세로 인접 화소 상관)."""
import numpy as np, sys, os, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import data0

def pixels(d=None):
    d = np.frombuffer(d or data0.read(769), np.uint8)
    px = np.zeros(len(d) * 2, np.uint8); px[0::2] = d >> 4; px[1::2] = d & 15
    return px

def score(px, o, w):
    g = px[o:o + w * 16].reshape(16, w).astype(int)
    nz = (g > 0)
    same = (nz[1:] & nz[:-1]).sum()
    diff = (nz[1:] ^ nz[:-1]).sum()
    return same - 0.5 * diff

def segment(px, start=0, end=None, widths=range(8, 137, 8)):
    end = end or len(px)
    N = (end - start) // 128          # 단위: 8px*16행 = 128 니블
    best = [-1e9] * (N + 1); prev = [0] * (N + 1); best[0] = 0
    for i in range(N):
        if best[i] < -1e8: continue
        for w in widths:
            j = i + w // 8
            if j > N: break
            s = best[i] + score(px, start + i * 128, w) - 1.0
            if s > best[j]: best[j] = s; prev[j] = i
    out = []; j = N
    while j > 0:
        i = prev[j]; out.append((start + i * 128, (j - i) * 8)); j = i
    return out[::-1]


# ---------------------------------------------------------------- 한글 스프라이트 생성
NAMES_JP = """ウェイン ゴルダーク ティリス ミカヅキ レイナート レオン ゴンゴス ジュノーン ロウ ソマリオン ニーナ リンク ギデオン カルハザード グレイス リリア グレン マノア デュラン ラインノール ジュウベエ バクラ シオン ホウライ ラ・デリ ソフィー トイス メノルカ ガリウス ユイカ シャイア ライザック ラギ バギ マニ ユニ アイロス キリコ オルテガ ジョシュア ハヤテ シロウ ハイム リスキーマ イグラシオ タウザ シド ランドルフ クロフォード ミルティア ビューネ カティス ボルガノ ヒルダ ロック エンドリュー セーラ カトマンドゥ ヒックス シェルン グインガル ザド ギョル グスタフ ヨーグ ガンラド マーシャル ガスパー ヘム ヅバン ハリル ディアンド シルビー ノイキス キョウエン クモン ランセツ サヤカ ダイン コハク ミュリア ノーマリィー ギゼルダーク ラムゼイ ラムゼイ キッド ウリル ジャロム ギガ サターナ タイレル アイーシャ バグフィー セルジオ ネルソン ハガネ エリーヌ ミレーヌ ライオーネ パーシル ニカルモ バニラ ゼノン ユリシス ベルターナ グルーダー パンタリオン どくろ党 アトキンス ギュント ゴルディアス ヘルメス シェラサード マグラード マルチナ ルーベンス バラド ニール ラムダ マドルク 竜人 メア フィーナ アレイク フォーリス キルレイン イシュメール ジン ライドー ワルデス シュレイバ ラウングラム スレイド バルナーク ゼウタ サーバス バーラット ガドル リヴィオン ソウガ クレイン フェリーナ エナ ギルテ ヴォイド ログ スティア セルピア ザック ルフス ハイランド ファンダリア ムーンパレス イズモ トラッドノア トパーズ ボザック トリスタン ソルジャー ホースマン メイジ アシガル アーチャー モンク ハーピー ビースト ドラゴニア ゾンビ""".split()
EXTRA_KO = {'ノーマリィー': '노마리', 'どくろ党': '해골당', 'ラウングラム': '라운그람', 'ギルテ': '기르테', '竜人': '용인'}
LABELS = [(0x12180, 16, '군'), (0x12200, 32, '사단'), (0x123c0, 48, '고용병단')]
JIKEI = (0x13ba0, 88)


def sprite_list(px=None):
    """(바이트 오프셋, 폭) 168개: 장수 150 + 나라 8 + 병종 10."""
    px = pixels() if px is None else px
    nz = px > 0
    def sc(o, w):
        g = nz[o:o + w * 16].reshape(16, w); a = g[1:]; b = g[:-1]; s = (a & b).sum(); t = a.sum() + b.sum()
        return 2 * s / t if t else 0
    o = 0; out = []
    while len(out) < len(NAMES_JP):
        s, w = max((sc(o, w), w) for w in range(8, 137, 8))
        out.append((o // 2, w)); o += w * 16
    return out


def render(text, w, size=13, shear=0.22, font=None):
    from PIL import Image, ImageDraw, ImageFont
    import hangul
    font = font or os.path.join(hangul.ROOT, 'NanumSquareNeo-dEb.ttf')
    SS = 4
    for sz in range(size, 8, -1):
        f = ImageFont.truetype(font, sz * SS)
        im = Image.new('L', (w * SS * 2, 16 * SS)); d = ImageDraw.Draw(im)
        bb = d.textbbox((0, 0), text, font=f)
        tw = bb[2] - bb[0] + int(16 * SS * shear)
        if tw <= (w - 2) * SS: break
    d.text((SS * 1 - bb[0] + int(14 * SS * shear), (16 * SS - (bb[3] - bb[1])) // 2 - bb[1]), text, 255, font=f)
    im = im.transform(im.size, Image.AFFINE, (1, shear, -shear * 16 * SS, 0, 1, 0), Image.BICUBIC)
    im = im.crop((0, 0, w * SS, 16 * SS)).resize((w, 16), Image.LANCZOS)
    a = np.asarray(im).astype(float) / 255
    return np.clip(np.round(a * 15), 0, 15).astype(np.uint8)


def pack4(g):
    g = g.reshape(-1)
    return ((g[0::2] << 4) | g[1::2]).astype(np.uint8).tobytes()


def build(glossary):
    d = bytearray(data0.read(769)); px = pixels(bytes(d))
    for (o, w), jp in zip(sprite_list(px), NAMES_JP):
        g = lambda t: glossary.get(hashlib.sha1(t.encode('utf-8')).hexdigest()[:12])   # 용어집 키 = 원문 sha1 앞 12자리
        ko = EXTRA_KO.get(jp) or g(jp) or g(jp.replace('ー', ''))
        if not ko: continue
        d[o:o + w * 8] = pack4(render(ko.replace(' ', ''), w))
    for o, w, ko in LABELS:
        d[o:o + w * 8] = pack4(render(ko, w, size=13))
    # 지형효과 칸: 내부 글자(열 3~50, 행 3~13)만 지우고 다시 쓴다
    o, w = JIKEI
    g = np.frombuffer(bytes(d[o:o + w * 8]), np.uint8)
    p = np.zeros(w * 16, np.uint8); p[0::2] = g >> 4; p[1::2] = g & 15; p = p.reshape(16, w)
    p[3:14, 3:52] = 0
    t = render('지형효과', 52, size=11, shear=0.0)
    t = np.where(t[3:14, :52] >= 7, 15, 0).astype(np.uint8)        # 이 칸 팔레트는 f(글자)만 안전
    p[3:14, 2:54] = np.maximum(p[3:14, 2:54], t)
    d[o:o + w * 8] = pack4(p)
    return bytes(d)
