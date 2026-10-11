"""쪽 정렬 번역 검사: python tools/check_pages.py work/align/jobNN.json work/align/outNN.json
out = {key: [쪽1, 쪽2, ...]} — 쪽 수가 원문과 같고, 각 쪽이 2줄·14칸에 들어가고, 태그(⟦…⟧ %d 등)가 원래 번역과 같아야 한다."""
import sys, os, json, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import wrap, build_all

TAG = re.compile(r'⟦[^⟧]*⟧|%\d*[sd]|&\d{3}')


def page_ok(p):
    p = build_all.fix_josa(build_all.norm(p))
    return len(wrap.wrap_lines(' '.join(p.split()), 14.0)) <= 2


def check(job, out):
    bad = []
    for it in job:
        k = it['key']; n = len(it['jp'])
        v = out.get(k)
        if v is None: bad.append((k, '없음')); continue
        if not isinstance(v, list) or len(v) != n: bad.append((k, '쪽 수 %s≠%d' % (len(v) if isinstance(v, list) else '?', n))); continue
        if any(not p.strip() for p in v): bad.append((k, '빈 쪽')); continue
        if collections.Counter(TAG.findall(' '.join(v))) != collections.Counter(TAG.findall(it['ko'])):
            bad.append((k, '태그 다름')); continue
        for i, p in enumerate(v):
            if not page_ok(p): bad.append((k, '%d쪽 넘침: %s' % (i + 1, p))); break
    return bad


if __name__ == '__main__':
    job = json.load(open(sys.argv[1], encoding='utf-8'))
    out = json.load(open(sys.argv[2], encoding='utf-8')) if os.path.exists(sys.argv[2]) else {}
    bad = check(job, out)
    for k, m in bad: print(k, m)
    print('항목 %d, 문제 %d' % (len(job), len(bad)))
