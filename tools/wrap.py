"""한국어 줄바꿈/페이지 나누기. 폭 단위: 전각(한글·SJIS 2바이트) 1.0, 반각 ASCII 0.7(대사창 실측).
태그: ⟦V xx⟧ 변수(이름 등, 폭 추정), ⟦S xx⟧ 속도(폭 0), ⟦XX⟧ 제어(폭 0)."""
import re
TAG = re.compile(r'⟦[^⟧]*⟧')
HALF = 0.7
VARW = {'00': 5, '01': 5, '02': 5, '05': 5, '06': 5, '07': 1.4, '09': 5, '0D': 5, '0F': 6}


def width(s, half=HALF):
    w = 0.0; p = 0
    for m in TAG.finditer(s):
        w += _w(s[p:m.start()], half)
        t = m.group()
        if t.startswith('⟦V '): w += VARW.get(t[3:5], 5)
        p = m.end()
    return w + _w(s[p:], half)


def _w(s, half):
    return sum(half if ord(c) < 0x80 or 0xff61 <= ord(c) <= 0xff9f else 1.0 for c in s)


def tokens(s):
    """공백 기준 낱말(태그는 앞 낱말에 붙음)."""
    return [t for t in re.split(r' (?![^⟦]*⟧)', s) if t != '']


def wrap_lines(text, maxw=13.0, half=HALF):
    """한 문단 → 줄 목록. 공백에서 끊고, 너무 긴 낱말은 글자 단위로 끊는다."""
    words = tokens(' '.join(text.split('\n')))
    lines = []; cur = ''
    for wd in words:
        cand = wd if not cur else cur + ' ' + wd
        if width(cand, half) <= maxw:
            cur = cand; continue
        if cur: lines.append(cur); cur = ''
        while width(wd, half) > maxw:
            # 글자 단위 분할(태그는 쪼개지 않음)
            parts = re.findall(r'⟦[^⟧]*⟧|.', wd)
            acc = ''
            for k, ch in enumerate(parts):
                if width(acc + ch, half) > maxw: break
                acc += ch
            lines.append(acc); wd = wd[len(acc):]
        cur = wd
    if cur: lines.append(cur)
    return lines or ['']


def paginate(text, maxw=13.0, nlines=2, half=HALF):
    """빈 줄 = 강제 페이지 경계. 나머지 줄바꿈은 무시하고 다시 채운다."""
    pages = []
    for block in re.split(r'\n\s*\n', text.strip('\n')):
        ls = wrap_lines(block, maxw, half)
        for i in range(0, len(ls), nlines): pages.append(ls[i:i + nlines])
    return pages or [['']]


def fit_pages(text, n, weights=None, maxw=14.0, nlines=2, half=HALF):
    """번역문을 정확히 n 쪽으로 나눈다(음성이 쪽마다 하나씩 재생되므로 원문 쪽 수 유지).
    낱말 경계에서 자르고, 쪽 길이는 원문 쪽 길이 비율(weights)에 가깝게, 문장 끝에서 끊는 것을 우선.
    들어가지 않으면 None."""
    SP = chr(1)                                   # 태그(⟦V 09⟧) 안 공백 보호
    text = re.sub('⟦[^⟧]*⟧', lambda m: m.group().replace(' ', SP), text)
    words = ' '.join(text.split()).split(' ')
    W = len(words)
    if n <= 0 or W < n: return None
    weights = weights or [1] * n
    tot = sum(len(w) for w in words) or 1
    ws = sum(weights)
    target = [tot * w / ws for w in weights]
    fits = {}
    def ok(i, j):
        k = (i, j)
        if k not in fits:
            fits[k] = len(wrap_lines(' '.join(words[i:j]), maxw, half)) <= nlines
        return fits[k]
    INF = float('inf')
    best = [[INF] * (W + 1) for _ in range(n + 1)]; prev = [[0] * (W + 1) for _ in range(n + 1)]
    best[0][0] = 0
    for p in range(1, n + 1):
        for j in range(p, W - (n - p) + 1):
            for i in range(j - 1, p - 2, -1):
                if best[p - 1][i] == INF: continue
                if not ok(i, j): break
                L = sum(len(w) for w in words[i:j])
                c = (L - target[p - 1]) ** 2
                if p < n and not re.search(r'[.!?…」』)~]$', words[j - 1]): c += 30
                if best[p - 1][i] + c < best[p][j]: best[p][j] = best[p - 1][i] + c; prev[p][j] = i
    if best[n][W] == INF: return None
    cuts = [W]
    for p in range(n, 0, -1): cuts.append(prev[p][cuts[-1]])
    cuts = cuts[::-1]
    return [[l.replace(SP, ' ') for l in wrap_lines(' '.join(words[cuts[k]:cuts[k + 1]]), maxw, half)] for k in range(n)]
