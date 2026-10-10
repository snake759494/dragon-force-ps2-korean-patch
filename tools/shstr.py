"""SH-2(새턴) 프로그램/데이터 안의 SJIS 문자열: 탐지, 적재 기준 주소 추정, 포인터 참조 찾기."""
import re, struct, collections, sys, os
sys.path.insert(0, os.path.dirname(__file__))
SJ = rb'[\x81-\x9f\xe0-\xef][\x40-\xfc]'
J = re.compile(rb'(?:' + SJ + rb'|[\x20-\x7e\x0a\x0d])*(?:' + SJ + rb')(?:' + SJ + rb'|[\x20-\x7e\x0a\x0d])*\x00')
K = re.compile(rb'(?:\x82[\x9f-\xf1]|\x83[\x40-\x96]|\x81[\x40-\xac]|[\x88-\x9f\xe0-\xea][\x40-\xfc])')

def is_text(s):
    k = len(K.findall(s))
    if k < 1: return False
    # 그림 데이터 오탐 제거: 가나/일반 문장부호 비율, 반복 금지
    kana = len(re.findall(rb'\x82[\x9f-\xf1]|\x83[\x40-\x96]|\x81[\x40-\x5b]', s))
    return k * 2 >= len(s) * 0.5 and (kana >= 1 or k <= 4) and not re.search(rb'(..)\1\1\1', s)

def strings(d, start=0):
    out = []
    for m in J.finditer(d, start):
        s = m.group()[:-1]
        if is_text(s): out.append((m.start(), s))
    return out

def ptrs(d, step=4):
    """BE u32 값 → 위치 목록"""
    res = collections.defaultdict(list)
    for i in range(0, len(d) - 3, step):
        res[struct.unpack_from('>I', d, i)[0]].append(i)
    return res

def guess_base(d, ss=None):
    ss = ss or strings(d)
    P = ptrs(d)
    vote = collections.Counter()
    starts = [a for a, s in ss]
    for v in P:
        if v & 0xff000000 not in (0x06000000, 0x00000000, 0x20000000, 0x26000000): continue
        for a in starts:
            b = v - a
            if b >= 0 and b & 0x3 == 0: vote[b] += 1
    if not vote: return None, 0
    b, n = vote.most_common(1)[0]
    return b, n
