"""번역 원천별 파서: 원문 단위 추출과 재조립.
단위 표기: textcodec 유니코드, 줄바꿈 LF, 빈 줄 = 원래 페이지 경계."""
import struct, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import data0, bank, bankpages, textcodec
BS = bytes([0x5c])
CR = b'\r'
PG = b'\x05'
NL = '\n'
NAMES = None


def names():
    """얼굴/화자 번호 → 이름 (1562 의 1666번부터)."""
    global NAMES
    if NAMES is None:
        d = data0.read(1562); w = struct.unpack_from('<3205I', d)
        NAMES = []
        for i in range(1666, 1666 + 200):
            e = d.find(b'\0', w[i]); NAMES.append(d[w[i]:e].decode('cp932', 'replace'))
    return NAMES


def speaker(code):
    if code is None: return ''
    n = names()
    return n[code] if code < 102 else '얼굴%d' % code


# ---------------------------------------------------------------- 메시지 뱅크
BANKS = list(range(770, 778)) + list(range(1032, 1040)) + list(range(1536, 1544)) + list(range(1552, 1560))


def bank_turns(ent):
    """항목 → [['c', 제어줄, 꼬리, _] | ['t', [페이지(줄 bytes 목록)...], 꼬리, 이어짐]]. {05}로 이어진 페이지 = 한 발언."""
    out = []
    for kind, v, tail in bankpages.split(ent):
        if kind == 'p':
            if out and out[-1][0] == 't' and out[-1][3]:
                out[-1][1].append(v); out[-1][2] = tail; out[-1][3] = False
            else:
                out.append(['t', [v], tail, False])
        elif v == PG and out and out[-1][0] == 't' and not out[-1][2] and not out[-1][3]:
            out[-1][3] = True
        else:
            if out and out[-1][0] == 't' and out[-1][3]:
                out[-1][3] = False; out.append(['c', PG, b'', False])
            out.append(['c', v, tail, False])
    if out and out[-1][0] == 't' and out[-1][3]:
        out[-1][3] = False; out.append(['c', PG, b'', False])
    return out


def turn_text(pages):
    return (NL + NL).join(bankpages.page_text(pg) for pg in pages)


def bank_units(e):
    info = bank.parse(data0.read(e)); out = []
    for k, ent in enumerate(info['ents']):
        spk = None
        for it in bank_turns(ent):
            if it[0] == 'c':
                v = it[1]
                if len(v) == 2 and v[0] in (1, 2): spk = v[1]
            else:
                out.append(dict(jp=turn_text(it[1]), ctx='%d#%d %s' % (e, k, speaker(spk)), kind='turn'))
    return out


def turns_join(items):
    parts = []
    for it in items:
        if it[0] == 'c':
            parts.append(['c', it[1], it[2]])
        else:
            for pi, pg in enumerate(it[1]):
                if pi: parts.append(['c', PG, b''])
                parts.append(['p', pg, b''])
            parts[-1][2] = it[2]
    return bankpages.join(parts)


def bank_rebuild(e, tr, enc, wrap):
    """tr(jp)→ko 또는 None, wrap(ko)→[페이지[줄 문자열]]."""
    d = data0.read(e); info = bank.parse(d); ents = []
    for ent in info['ents']:
        items = bank_turns(ent)
        for it in items:
            if it[0] != 't': continue
            ko = tr(turn_text(it[1]))
            if ko is None: continue
            it[1] = [[textcodec.from_text(l, enc) for l in pg] for pg in wrap(ko, [bankpages.page_text(pg) for pg in it[1]])]
        ents.append(turns_join(items))
    return bank.build(d, info, ents)


# ---------------------------------------------------------------- 1544 계열(역슬래시 명령)
EV = list(range(1544, 1552))
CTL = re.compile(re.escape(BS) + rb'(?:[ul]\d{3}|[pwe])')
P_CMD = BS + b'p'


def ev_tokens(s):
    out = []; p = 0
    for m in CTL.finditer(s):
        if m.start() > p: out.append(['t', s[p:m.start()]])
        out.append(['c', m.group()]); p = m.end()
    if p < len(s): out.append(['t', s[p:]])
    return out


def ev_turns(s):
    """→ [['c', bytes] | ['t', [페이지 bytes(끝 CR 제외)...], 끝 CR 묶음]] — P 명령으로 이어진 페이지는 한 발언."""
    out = []
    for k, v in ev_tokens(s):
        if k == 'c':
            if v == P_CMD and out and out[-1][0] == 't':
                out[-1][3] = True; continue
            if out and out[-1][0] == 't' and out[-1][3]:
                out.append(['c', P_CMD, None, False]); out[-2][3] = False
            out.append(['c', v, None, False])
        else:
            t = v.rstrip(CR); trail = v[len(t):]
            if not t:
                if out and out[-1][0] == 't' and out[-1][3]:
                    out.append(['c', P_CMD, None, False]); out[-2][3] = False
                out.append(['c', v, None, False]); continue
            if out and out[-1][0] == 't' and out[-1][3]:
                out[-1][1].append(t); out[-1][2].append(trail); out[-1][3] = False
            else:
                out.append(['t', [t], [trail], False])
    if out and out[-1][0] == 't' and out[-1][3]:
        out.append(['c', P_CMD, None, False])
    return out


def ev_join(items):
    b = bytearray()
    for it in items:
        if it[0] == 'c': b += it[1]
        else:
            for pi, (t, tr) in enumerate(zip(it[1], it[2])):
                if pi: b += P_CMD
                b += t + tr
    return bytes(b)


def ev_text(pages):
    return (NL + NL).join(NL.join(textcodec.to_text(l) for l in pg.split(CR)) for pg in pages)


def ev_parse(d):
    offs = struct.unpack_from('<1000I', d)
    used = sorted(set(o for o in offs if o))
    end = len(d.rstrip(b'\0'))
    ents = {}
    for i, o in enumerate(used):
        ents[o] = d[o:(used[i + 1] if i + 1 < len(used) else end)]
    return offs, ents


def ev_units(e):
    offs, ents = ev_parse(data0.read(e)); out = []
    for o, s in ents.items():
        spk = None
        for it in ev_turns(s):
            if it[0] == 'c':
                v = it[1]
                if v[1:2] in (b'u', b'l'): spk = int(v[2:])
                continue
            out.append(dict(jp=ev_text(it[1]), ctx='%d@%x %s' % (e, o, speaker(spk)), kind='turn'))
    return out


def ev_rebuild(e, tr, enc, wrap):
    d = data0.read(e); offs, ents = ev_parse(d)
    hdr = 4000
    body = bytearray(); newo = {}
    for o, s in ents.items():
        newo[o] = hdr + len(body)
        items = ev_turns(s)
        for it in items:
            if it[0] != 't': continue
            ko = tr(ev_text(it[1]))
            if ko is None: continue
            pages = wrap(ko, [ev_text([pg]) for pg in it[1]])
            last = it[2][-1]
            it[1] = [CR.join(textcodec.from_text(l, enc) for l in pg) for pg in pages]
            it[2] = [CR] * (len(pages) - 1) + [last]
        body += ev_join(items)
    out = bytearray(struct.pack('<1000I', *[newo[o] if o else 0 for o in offs]))
    out += body
    out += b'\0' * ((-len(out)) % 0x800)
    return bytes(out)


# ---------------------------------------------------------------- 1535/1562 문자열 치환 표
def pool_keys():
    d = data0.read(1535); w = struct.unpack_from('<3205I', d, 0x200)
    return [d[x:d.find(b'\0', x)] for x in w]


def pool_vals():
    d = data0.read(1562); w = struct.unpack_from('<3205I', d)
    return [d[x:d.find(b'\0', x)] for x in w]


BINS = [('SLPM_657.78', (0x1e2f80, 0x229c58)), ('OPEN.BIN', (0x4f000, 0xcfa60)),
        ('READY.BIN', (0x70000, 0x82674)), ('APPLI.BIN', (0, 0x16f63c))]


def bin_data(name):
    import iso
    return iso.readfile('/' + name)


def bin_strings():
    """바이너리 안의 (이름, 주소, bytes) — 0 으로 시작하는 위치의 SJIS 문자열."""
    import shstr
    out = []
    for name, (a, b) in BINS:
        d = bin_data(name)
        for x, s in shstr.strings(d[:b], a):
            if d[x - 1] == 0: out.append((name, x, s))
    return out




def pool_order():
    """1562 인덱스를 바이너리 등장 순서로."""
    keys = pool_keys()
    kidx = {}
    for i, k in enumerate(keys): kidx.setdefault(k, []).append(i)
    order = []; seen = set()
    for name, x, s in bin_strings():
        for i in kidx.get(s, []):
            if i not in seen: seen.add(i); order.append(i)
    return order + [i for i in range(len(keys)) if i not in seen]


NATION_TITLES = [0x224050, 0x224178, 0x224298, 0x224380, 0x224478, 0x224580, 0x224690, 0x224790, 0x224898]


def nation_groups():
    """ELF 국가 소개문: [(제목, 군주줄, [본문줄...])] — bytes (1535 키와 같음)."""
    d = bin_data('SLPM_657.78')
    import shstr
    out = []
    for k in range(8):
        ss = [s for x, s in shstr.strings(d[:NATION_TITLES[k + 1]], NATION_TITLES[k]) if d[x - 1] == 0]
        out.append((ss[0], ss[1], ss[2:]))
    return out


# ---------------------------------------------------------------- 0 구분 문자열 목록 (1560 함성, 1561 여신)
def strlist_parse(d, table_n=None):
    """table_n 이 있으면 앞에 LE u32 오프셋표(항목=문자열 목록 시작). 반환 (offs, [항목별 문자열 목록])."""
    end = len(d.rstrip(b'\0'))
    if table_n:
        offs = list(struct.unpack_from('<%dI' % table_n, d))
        starts = sorted(set(offs))
        ents = {}
        for i, o in enumerate(starts):
            e = starts[i + 1] if i + 1 < len(starts) else end + 1
            ents[o] = d[o:e - 1].split(b'\0') if e - 1 > o else []
        return offs, ents
    return None, {0: d[:end].split(b'\0')}


def strlist_build(offs, ents, table_n, align=0x800):
    out = bytearray(4 * table_n) if table_n else bytearray()
    newo = {}
    for o in sorted(ents):
        newo[o] = len(out)
        if ents[o]: out += b'\0'.join(ents[o]) + b'\0'
    if table_n:
        struct.pack_into('<%dI' % table_n, out, 0, *[newo[o] for o in offs])
    out += b'\0' * ((-len(out)) % align)
    return bytes(out)


SHOUT_TR = str.maketrans({'#': '\n'})


def shout_text(b):
    """1560: '#' 줄, '$' 페이지 → 표기: 줄 LF, 페이지 빈 줄."""
    return textcodec.to_text(b).replace('$', '\n\n').replace('#', '\n')


# ---------------------------------------------------------------- 1563 도감 (헤더 포인터표 + 문자열)
def zukan_parse(d):
    hdr = struct.unpack_from('<5I', d)
    tables = []
    bounds = list(hdr) + [None]
    first_str = None
    ptrs = []   # (위치, 값)
    for k in range(5):
        a = hdr[k]
        # 표 끝 = 다음 표 시작 또는 첫 문자열 위치
        b = hdr[k + 1] if k + 1 < 5 else None
        if b is None:
            v0 = struct.unpack_from('<I', d, a)[0]
            b = min(v for v in [struct.unpack_from('<I', d, p)[0] for p in range(hdr[0], a, 4)] + [v0])
        for p in range(a, b, 4): ptrs.append((p, struct.unpack_from('<I', d, p)[0]))
    ptrs = [(p, v) for p, v in ptrs if v]
    first_str = min(v for p, v in ptrs)
    return ptrs, first_str


def zukan_strings(d):
    ptrs, fs = zukan_parse(d)
    vals = sorted(set(v for p, v in ptrs if v))
    return ptrs, fs, {v: d[v:d.find(b'\0', v)] for v in vals}
