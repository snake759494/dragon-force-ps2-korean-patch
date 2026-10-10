"""번역 결과 검사: python tools/check_out.py j001 [j002 ...]  (인자 없으면 전체)
- 모든 id 존재, 태그/서식 보존, 가나·한자 잔존, 인코딩 불가 문자, 폭 제한(pool/nation)."""
import os, sys, json, re, glob
sys.path.insert(0, os.path.dirname(__file__))
import wrap
TR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'translation')
TAGS = re.compile(r'⟦[^⟧]*⟧|%[-0-9.*]*[sdxXcu]|\\[pen]|&\d{3}|@')
KANA = re.compile(r'[぀-ヺー-ヿ一-鿿ｦ-ﾟ]')


def encodable(ch):
    if '가' <= ch <= '힣' or ord(ch) < 0x80: return True
    try: ch.encode('cp932'); return True
    except UnicodeEncodeError: return False


def check(job):
    j = json.load(open(os.path.join(TR, 'jobs', job + '.json'), encoding='utf-8'))
    p = os.path.join(TR, 'out', job + '.json')
    if not os.path.exists(p): return ['출력 파일 없음']
    out = json.load(open(p, encoding='utf-8')); errs = []
    for u in j['units']:
        k = u['id']
        if k not in out: errs.append('%s 누락' % k); continue
        ko = out[k]
        a = sorted(TAGS.findall(u['jp'])); b = sorted(TAGS.findall(ko))
        if u['cat'] == 'shout': a = [x for x in a if x != '@']; b = [x for x in b if x != '@']
        if a != b: errs.append('%s 태그 불일치 %s → %s' % (k, a, b))
        if KANA.search(ko): errs.append('%s 가나/한자 잔존: %s' % (k, ko[:40]))
        bad = sorted(set(c for c in TAGS.sub('', ko) if not encodable(c) and c != '\n'))
        if bad: errs.append('%s 쓸 수 없는 문자 %s' % (k, bad))
        if u['cat'] == 'pool':
            jl = u['jp'].split('\n'); kl = ko.split('\n')
            if len(jl) != len(kl): errs.append('%s 줄 수 %d→%d' % (k, len(jl), len(kl)))
            for x, y in zip(jl, kl):
                if wrap.width(y.strip(), 0.5) > wrap.width(x.strip(), 0.5) + 0.01:
                    errs.append('%s 폭 초과 %.1f>%.1f: %s' % (k, wrap.width(y.strip(), 0.5), wrap.width(x.strip(), 0.5), y)); break
        if u['cat'] == 'nation':
            jl = u['jp'].split('\n'); kl = ko.split('\n')
            if len(jl) != len(kl): errs.append('%s 줄 수 %d→%d' % (k, len(jl), len(kl)))
            for y in kl:
                if wrap.width(y, 0.5) > 10.0 or len(y.encode('cp949')) > 23: errs.append('%s 줄 폭 초과: %s' % (k, y))
    return errs


if __name__ == '__main__':
    jobs = sys.argv[1:] or [os.path.basename(f)[:-5] for f in sorted(glob.glob(os.path.join(TR, 'jobs', '*.json')))]
    tot = 0
    for jb in jobs:
        e = check(jb); tot += len(e)
        print('%s: %s' % (jb, '정상' if not e else '%d건' % len(e)))
        for x in e[:30]: print('   ', x)
    sys.exit(1 if tot else 0)
