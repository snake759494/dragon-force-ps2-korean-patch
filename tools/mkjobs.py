"""translation/units.json → translation/jobs/jNNN.json (일본어 약 LIMIT 자씩, 등장 순서 유지, 분류별로 나눔)."""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__))
import hangul
TR = os.path.join(hangul.ROOT, 'translation')
JA = re.compile(r'[^\x00-\x7f]')
LIMIT = 7500


def main():
    units = json.load(open(os.path.join(TR, 'units.json'), encoding='utf-8'))
    os.makedirs(os.path.join(TR, 'jobs'), exist_ok=True)
    done = set()
    for f in os.listdir(os.path.join(TR, 'out')):
        done.update(json.load(open(os.path.join(TR, 'out', f), encoding='utf-8')).keys())
    groups = [('dlg', ['dlg']), ('sys', ['pool', 'nation', 'goddess', 'shout']), ('zukan', ['zukan'])]
    n = 0; jobs = []
    for gname, cats in groups:
        cur = []; size = 0
        for u in units:
            if u['cat'] not in cats or u['id'] in done: continue
            cur.append(dict(id=u['id'], cat=u['cat'], ctx=u['ctx'], jp=u['jp']))
            size += len(JA.findall(u['jp']))
            if size >= LIMIT:
                jobs.append((gname, cur)); cur = []; size = 0
        if cur: jobs.append((gname, cur))
    for gname, cur in jobs:
        n += 1
        json.dump(dict(job='j%03d' % n, kind=gname, units=cur), open(os.path.join(TR, 'jobs', 'j%03d.json' % n), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('작업', n)


if __name__ == '__main__':
    main()
