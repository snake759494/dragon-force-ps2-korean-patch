"""전체 한글패치 빌드.
번역: translation/out/*.json, translation/ko/*.json ({id: 한국어}) — 나중 파일이 우선.
python tools/build_all.py [--noiso]"""
import os, sys, json, glob, re, struct, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import data0, sources, textcodec, hangul, wrap, bank, iso
ROOT = hangul.ROOT
TR = os.path.join(ROOT, 'translation')
SLOT_EVENT = 0x40000          # 0x893000 칸 (1536/1544/1552/1560/1561/1563/1564)
SLOT_SATURN = 296960          # 770/1032 계열이 같은 칸에 적재 — 원본 최대 크기
SLOT_POOL = 0x10000           # 1562 (0x883000 칸)


def uid(jp):
    """원문 sha1 앞 12자리 = 번역 키(저장소에는 원문을 두지 않는다)."""
    return hashlib.sha1(jp.encode('utf-8')).hexdigest()[:12]


def load_tr():
    p = os.path.join(TR, 'units.json')       # 원본 ISO 에서 tools/extract.py 로 다시 만드는 파일(선택)
    units = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []
    tr = {}
    files = sorted(glob.glob(os.path.join(TR, 'out', '*.json'))) + [f for f in sorted(glob.glob(os.path.join(TR, 'ko', '*.json'))) if not f.endswith('bin_alt.json')]
    for f in files:
        for k, v in json.load(open(f, encoding='utf-8')).items():
            if isinstance(v, str) and v.strip(): tr[k] = v
    return units, tr


def norm(ko):
    """번역문 정리: 일본어 전용 기호를 한국어용으로."""
    ko = ko.replace('......', '……').replace('...', '…').replace('·', '・').replace('～', '~').replace('〜', '~')
    ko = ko.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    return ko


VAR = r'(⟦V [0-9A-F]{2}⟧)'
JOSA_FIX = [   # 변수 뒤 받침 의존 어미 → 받침과 무관한 형태
    (VAR + r'예요', r', 그거예요'), (VAR + r'다만', r'입니다만'), (VAR + r'요만', r'입니다만'),
    (VAR + r'로구나', r', 너로구나'), (VAR + r'로군', r', 맞군'), (VAR + r'라고', r', 이라고'),
    (VAR + r'다(?=[!.?,…\s]|$)', r', 그거다'), (VAR + r'요(?=[!.?,…\s]|$)', r'입니다'),
    (VAR + r'야(?=[!.?,…\s]|$)', r', 그게 나야'), (VAR + r'여(?=[!.?,…\s]|$)', r' 님이시여'),
    (VAR + r'군(?=[!.?,…\s]|$)', r', 맞군'), (VAR + r'냐(?=[!.?,…\s]|$)', r' 아니냐'),
    (VAR + r'네만', r'일세만'),
]


def fix_josa(ko):
    for a, b in JOSA_FIX:
        ko = re.sub(a, lambda m, b=b: m.group(1) + b, ko)
    return ko.replace(', 이라고', '(이)라고')


def make_tr(trd):
    def f(jp):
        v = trd.get(uid(jp))
        return fix_josa(norm(v)) if v is not None else None
    return f


NL = chr(10)


def enc(s):
    return hangul.encode(s)


def dlg_wrap(ko):
    return wrap.paginate(ko, 13.0, 2)


# ------------------------------------------------------------------ 각 원천
def build_banks(T, mods, report):
    for e in sources.BANKS:
        d = sources.bank_rebuild(e, T, enc, dlg_wrap)
        lim = SLOT_EVENT if e >= 1536 else SLOT_SATURN
        report.append((e, len(data0.read(e)), len(d), lim))
        mods[e] = d


def build_ev(T, mods, report):
    for e in sources.EV:
        d = sources.ev_rebuild(e, T, enc, dlg_wrap)
        report.append((e, len(data0.read(e)), len(d), SLOT_EVENT)); mods[e] = d


def shout_encode(ko):
    pages = wrap.paginate(ko, 13.0, 2)
    return '$'.join('#'.join(p) for p in pages)


def build_shout(T, mods, report):
    d = data0.read(1560); offs, ents = sources.strlist_parse(d, 182)
    for o in ents:
        new = []
        for s in ents[o]:
            ko = T(sources.shout_text(s))
            new.append(s if ko is None else textcodec.from_text(shout_encode(ko), enc))
        ents[o] = new
    r = sources.strlist_build(offs, ents, 182)
    report.append((1560, len(d), len(r), SLOT_EVENT)); mods[1560] = r


def build_goddess(T, mods, report):
    d = data0.read(1561); o, e = sources.strlist_parse(d)
    new = []
    for s in e[0]:
        ko = T(textcodec.to_text(s))
        new.append(s if ko is None else textcodec.from_text(ko, enc))
    r = b'\0'.join(new) + b'\0'
    r += b'\0' * ((-len(r)) % 0x800)
    report.append((1561, len(d), len(r), SLOT_EVENT)); mods[1561] = r


def fit_pad(orig, ko_b):
    """앞뒤 공백으로 칸을 맞춘 원문이면 같은 바이트 길이로 다시 가운데 맞춤."""
    lead = len(orig) - len(orig.lstrip(b' ')); trail = len(orig) - len(orig.rstrip(b' '))
    if not (lead or trail) or b'\n' in orig: return ko_b
    core = ko_b.strip(b' ')
    room = len(orig) - len(core)
    if room <= 0: return core
    l = round(room * lead / (lead + trail)) if lead + trail else 0
    return b' ' * l + core + b' ' * (room - l)


def pool_translated(T):
    """1562 인덱스 → 새 bytes(번역 없으면 None)."""
    vals = sources.pool_vals(); keys = sources.pool_keys(); out = {}
    nat = {}
    elf = sources.bin_data('SLPM_657.78')
    for t, r, body in sources.nation_groups():
        jp = NL.join(textcodec.to_text(x) for x in body)
        ko = T(jp)
        if ko is None: continue
        # 각 줄 칸 크기(다음 문자열 시작 전까지) 안에서 낱말 단위로 다시 채운다
        caps = []
        for x in body:
            p = elf.find(x + b'\0', 0x224000)
            q = p + len(x) + 1
            while elf[q] == 0: q += 1
            caps.append(min(q - p - 1, 20))
        words = ' '.join(l.strip() for l in ko.split(NL)).split(' ')
        lines = []; wi = 0
        for k, cap in enumerate(caps):
            cur = '  ' if k == 0 else ''
            while wi < len(words):
                cand = (cur + (' ' if cur.strip() else '') + words[wi]) if cur.strip() else cur + words[wi]
                if len(enc(cand)) <= cap: cur = cand; wi += 1
                else: break
            lines.append(cur)
        if wi < len(words):
            print('  ! 국가 소개 넘침', textcodec.to_text(t), ' '.join(words[wi:]))
        for k, l in zip(body, lines): nat[k] = enc(l)
    for i, v in enumerate(vals):
        if keys[i] in nat: out[i] = nat[keys[i]]; continue
        jp = textcodec.to_text(v).replace('⟦0A⟧', '\n')
        ko = T(jp)
        if ko is None: continue
        b = textcodec.from_text(ko.replace('\n', '⟦0A⟧'), enc)
        out[i] = fit_pad(v, b)
    return out


def build_pool(T, mods, report):
    d = data0.read(1562); w = list(struct.unpack_from('<3205I', d))
    vals = sources.pool_vals(); new = pool_translated(T)
    out = bytearray(d[:0x4000]); seen = {}
    for i in range(3205):
        s = new.get(i, vals[i])
        if s in seen: w[i] = seen[s]; continue
        seen[s] = w[i] = len(out); out += s + b'\0'
    struct.pack_into('<3205I', out, 0, *w)
    out += b'\0' * ((-len(out)) % 0x800)
    report.append((1562, len(d), len(out), SLOT_POOL)); mods[1562] = bytes(out)
    return new


def build_zukan(T, mods, report):
    d = data0.read(1563); ptrs, fs, st = sources.zukan_strings(d)
    out = bytearray(d[:fs]); newv = {}
    for v in sorted(st):
        s = st[v]
        ko = T(textcodec.to_text(s).replace('⟦0A⟧', '\n'))
        if ko is not None:
            ls = []
            for l in ko.split('\n'):
                ind = re.match(r'^[　 ]*', l).group()
                body = l[len(ind):]
                if wrap.width(l, 0.5) > 24.0 and body:
                    sub = wrap.wrap_lines(body, 24.0 - wrap.width(ind, 0.5), 0.5)
                    ls.extend([ind + sub[0]] + ['　' + x for x in sub[1:]] if ind else sub)
                else: ls.append(l)
            s = textcodec.from_text('⟦0A⟧'.join(ls), enc)
        newv[v] = len(out); out += s + b'\0'
    for p, v in ptrs: struct.pack_into('<I', out, p, newv[v])
    out += b'\0' * ((-len(out)) % 0x800)
    report.append((1563, len(d), len(out), SLOT_EVENT)); mods[1563] = bytes(out)
    # 1564: 레코드 4개(+0x10 문자열 오프셋)
    d = data0.read(1564); out = bytearray(d[:0xa4])
    for r in range(4):
        p = struct.unpack_from('<I', d, 0x40 + r * 0x14 + 0x10)[0]
        s = d[p:d.find(b'\0', p)]
        ko = T(textcodec.to_text(s))
        if ko is not None: s = textcodec.from_text(ko, enc)
        struct.pack_into('<I', out, 0x40 + r * 0x14 + 0x10, len(out)); out += s + b'\0'
    out += b'\0' * ((-len(out)) % 0x800)
    mods[1564] = bytes(out)


SHORT = []
BIN_ALT = {}   # 바이너리 칸 전용(1562 값이 원문보다 긴 경우)


def build_bins(pool_new):
    """ELF/BIN 안의 풀 문자열을 제자리 교체(칸에 들어갈 때만)."""
    keys = sources.pool_keys(); kidx = {}
    for i, k in enumerate(keys): kidx.setdefault(k, i)
    files = {}; stat = [0, 0]
    allstr = {}
    for name, x, s in sources.bin_strings(): allstr.setdefault(name, []).append((x, s))
    for name, lst in allstr.items():
        d = bytearray(sources.bin_data(name)); starts = set(x for x, s in lst)
        for x, s in lst:
            i = kidx.get(s)
            if i is None or i not in pool_new: continue
            nb = pool_new[i]
            alt = BIN_ALT.get(uid(textcodec.to_text(s)))
            if alt is not None: nb = textcodec.from_text(alt, enc)
            end = x + len(s) + 1
            q = end
            while q < len(d) and d[q] == 0 and q - x < 96: q += 1
            if q in starts: avail = q - x - 1
            else: avail = ((end + 3) & ~3) - x - 1
            if len(nb) <= avail:
                d[x:x + avail] = nb + b'\0' * (avail - len(nb)); stat[0] += 1
            else:
                stat[1] += 1; SHORT.append((name, hex(x), avail, len(nb), textcodec.to_text(s), hangul.decode(nb)))
        files['/' + name] = bytes(d)
    for name, x, s in []: pass
    print('  바이너리 제자리 교체 %d, 칸 부족 %d' % tuple(stat))
    return files


def charset_from(trd):
    cs = set()
    for v in trd.values(): cs.update(c for c in v if '가' <= c <= '힣')
    extra = sorted(cs - set(hangul.ksx1001()))
    open(os.path.join(TR, 'charset_extra.txt'), 'w', encoding='utf-8').write(''.join(extra))
    hangul._MAP = None
    return extra


def main(noiso=False):
    units, trd = load_tr()
    p = os.path.join(TR, 'ko', 'bin_alt.json')
    if os.path.exists(p): BIN_ALT.update(json.load(open(p, encoding='utf-8')))
    print('번역 %d / 단위 %d' % (len(trd), len(units)))
    extra = charset_from(trd)
    print('추가 음절 %d' % len(extra))
    import build_font
    T = make_tr(trd); mods = {}; report = []
    mods[67] = build_font.build()
    build_banks(T, mods, report); build_ev(T, mods, report)
    build_shout(T, mods, report); build_goddess(T, mods, report)
    pool_new = build_pool(T, mods, report); build_zukan(T, mods, report)
    files = build_bins(pool_new)
    import images
    mods.update(images.build_all_images())
    import spr769
    mods[769] = spr769.build(json.load(open(os.path.join(TR, 'glossary.json'), encoding='utf-8')))
    for e in range(770, 778):   # 새턴형 묶음 안에도 같은 스프라이트 사본(0x7680)이 있음
        b = bytearray(mods[e]); n = 0x13e60
        assert b[0x7680 + 0x1000:0x7680 + 0x1040] == data0.read(769)[0x1000:0x1040]
        b[0x7680:0x7680 + n] = mods[769][:n]; mods[e] = bytes(b)
    import titles
    titles.build(mods)          # 陣形選択·一騎討ち 제목 그림
    bad = [r for r in report if r[2] > r[3]]
    for e, a, b, lim in report:
        if b > lim or b > a * 1.15: print('  %5d %7d → %7d (한계 %d)%s' % (e, a, b, lim, ' ★초과' if b > lim else ''))
    if bad:
        print('크기 초과로 중단'); sys.exit(1)
    if noiso: return mods, files
    import build
    build.write_iso(mods, files)


if __name__ == '__main__':
    main('--noiso' in sys.argv)
