"""번역 밀림 검사: 같은 작업 안에서 원문/번역 길이 비율이 크게 튀거나, 변수·숫자·느낌표 개수가 어긋나는 단위."""
import os, sys, json, re, glob
sys.path.insert(0, os.path.dirname(__file__))
TR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'translation')
JA = re.compile(r'[^\x00-\x7f\s]')
def L(s): return len(re.sub(r'\s|⟦[^⟧]*⟧', '', s))
def main(jobs):
    for jb in jobs:
        j = json.load(open(os.path.join(TR, 'jobs', jb + '.json'), encoding='utf-8'))
        p = os.path.join(TR, 'out', jb + '.json')
        if not os.path.exists(p): continue
        o = json.load(open(p, encoding='utf-8')); bad = []
        for u in j['units']:
            ko = o.get(u['id'], ''); a = L(u['jp']); b = L(ko)
            if a >= 6 and (b > a * 2.2 + 6 or b < a * 0.35):
                bad.append((u['id'], a, b, u['jp'][:30].replace('\n', '/'), ko[:30].replace('\n', '/')))
            qa = u['jp'].count('？') + u['jp'].count('?'); qb = ko.count('?') + ko.count('？')
            if qa >= 1 and qb == 0 and a < 30 and u['cat'] == 'dlg':
                bad.append((u['id'], 'Q', qa, u['jp'][:30].replace('\n', '/'), ko[:30].replace('\n', '/')))
        print('%s: %d/%d' % (jb, len(bad), len(j['units'])))
        for x in bad[:8]: print('   ', x)
if __name__ == '__main__':
    main(sys.argv[1:] or [os.path.basename(f)[:-5] for f in sorted(glob.glob(os.path.join(TR, 'out', '*.json')))])
