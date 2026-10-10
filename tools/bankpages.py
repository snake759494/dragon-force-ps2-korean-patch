"""뱅크 항목 ↔ 페이지 목록.
항목은 0D 로 나눈 줄의 연속. 줄 맨 앞이 0x20 미만(0x10 변수 제외)이면 '제어 줄', 아니면 텍스트 줄.
연속된 텍스트 줄 묶음 = 페이지. 제어 줄은 그대로 보존. 항목 끝(마지막 0D 뒤 꼬리, 예 {06})도 보존."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import textcodec

def is_text_line(l):
    return bool(l) and (l[0] >= 0x20 or l[0] == 0x10 or (l[0] == 0x07 and len(l) > 2 and any(c >= 0x20 for c in l[2:])))

def split(ent):
    """→ 조각 목록: ('c', bytes 제어줄) / ('p', [텍스트줄 bytes...]). 줄 구분 0D 는 조각 사이에 암묵적으로 존재."""
    lines = ent.split(b'\r')
    out = []
    for l in lines:
        if is_text_line(l):
            # 텍스트 줄 끝에 붙은 제어(예: '…。{06}')는 떼어 낸다
            tail = b''
            while l and l[-1] < 0x20 and not (len(l) >= 2 and l[-2] in (0x10, 0x07)):
                tail = l[-1:] + tail; l = l[:-1]
            if out and out[-1][0] == 'p' and not out[-1][2]:
                out[-1][1].append(l); out[-1][2] = tail
            else:
                out.append(['p', [l], tail])
        else:
            out.append(['c', l, b''])
    return out

def join(parts):
    lines = []
    for k, v, tail in parts:
        if k == 'c': lines.append(v)
        else:
            vv = list(v); vv[-1] = vv[-1] + tail; lines.extend(vv)
    return b'\r'.join(lines)

def page_text(lines):
    return '\n'.join(textcodec.to_text(l) for l in lines)
