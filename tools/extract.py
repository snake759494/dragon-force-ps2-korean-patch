"""모든 원천에서 번역 단위를 뽑아 translation/units.json 에 저장 (원문 기준 중복 제거, 등장 순서 유지).
단위: id(원문 sha1 앞 12자리), cat, jp, ctx, rule."""
import os, sys, json, hashlib, re, struct
sys.path.insert(0, os.path.dirname(__file__))
import data0, sources, textcodec, hangul
ROOT = hangul.ROOT
TR = os.path.join(ROOT, 'translation')
JA = re.compile(r'[぀-ヿ一-鿿ｦ-ﾟ]')


def uid(jp):
    return hashlib.sha1(jp.encode('utf-8')).hexdigest()[:12]


def collect():
    units = {}; order = []

    def add(cat, jp, ctx, rule):
        if not JA.search(jp): return
        k = uid(jp)
        if k in units:
            if len(units[k]['ctx']) < 3: units[k]['ctx'].append(ctx)
            return
        units[k] = dict(id=k, cat=cat, jp=jp, ctx=[ctx], rule=rule); order.append(k)

    # 1) 이벤트 대사(PS2 적재) 1552 → 1544 → 1536, 국가 순
    for g in (1552, 1544, 1536):
        for n in range(8):
            e = g + n
            us = sources.ev_units(e) if g == 1544 else sources.bank_units(e)
            for u in us: add('dlg', u['jp'], u['ctx'], 'dlg')
    # 2) 새턴형 뱅크 (장수 대사)
    for g in (1032, 770):
        for n in range(8):
            for u in sources.bank_units(g + n): add('dlg', u['jp'], u['ctx'], 'dlg')
    # 3) 전투 함성 1560
    offs, ents = sources.strlist_parse(data0.read(1560), 182)
    for k, o in enumerate(offs):
        for j, s in enumerate(ents[o]):
            add('shout', sources.shout_text(s), '1560#%d.%d %s' % (k, j, sources.speaker(k) if k < 102 else ''), 'shout')
    # 4) 국가 소개문
    for k, (t, r, body) in enumerate(sources.nation_groups()):
        jp = '\n'.join(textcodec.to_text(x) for x in body)
        add('nation', jp, 'nation%d %s / %s' % (k, textcodec.to_text(t).strip(), textcodec.to_text(r).strip()), 'nation')
    # 5) 시스템 문자열 1562 (바이너리 등장 순서)
    vals = sources.pool_vals(); keys = sources.pool_keys()
    nat = set()
    for t, r, body in sources.nation_groups(): nat.update(body)
    for i in sources.pool_order():
        if keys[i] in nat: continue
        jp = textcodec.to_text(vals[i]).replace('⟦0A⟧', '\n')
        add('pool', jp, '1562#%d' % i, 'pool')
    # 6) 도감 1563 / 1564
    d = data0.read(1563); ptrs, fs, st = sources.zukan_strings(d)
    for v in sorted(st):
        add('zukan', textcodec.to_text(st[v]).replace('⟦0A⟧', '\n'), '1563@%x' % v, 'zukan')
    d = data0.read(1564)
    for r in range(4):
        p = struct.unpack_from('<I', d, 0x40 + r * 0x14 + 0x10)[0]
        add('zukan', textcodec.to_text(d[p:d.find(b'\0', p)]), '1564#%d' % r, 'zukan')
    # 7) 여신 부활 1561
    o, e = sources.strlist_parse(data0.read(1561))
    for j, s in enumerate(e[0]):
        add('goddess', textcodec.to_text(s), '1561#%d' % j, 'goddess')
    return [units[k] for k in order]


if __name__ == '__main__':
    us = collect()
    os.makedirs(TR, exist_ok=True)
    json.dump(us, open(os.path.join(TR, 'units.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    from collections import Counter
    c = Counter(u['cat'] for u in us); ch = Counter()
    for u in us: ch[u['cat']] += len(JA.findall(u['jp']))
    for k in c: print(k, c[k], ch[k])
    print('합계', len(us), sum(ch.values()))
