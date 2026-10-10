"""ELF(MIPS) 분석 도우미: 주소 참조 찾기, 역어셈블."""
import struct, sys, capstone
D = None; BASE = 0xff000   # vaddr = file + BASE (텍스트 세그먼트)
def load(path='work/SLPM_657.78', base=0xff000):
    global D, BASE
    D = open(path, 'rb').read(); BASE = base
def refs(addr):
    """lui+addiu/ori/lw 등 즉시값으로 addr 을 만드는 위치."""
    hi = (addr + 0x8000) >> 16; lo = addr & 0xffff; res = []
    n = len(D) // 4
    for i in range(n):
        w = struct.unpack_from('<I', D, i * 4)[0]
        if w >> 26 == 0xf and (w & 0xffff) == hi:
            r = (w >> 16) & 31
            for j in range(i + 1, min(i + 40, n)):
                w2 = struct.unpack_from('<I', D, j * 4)[0]
                if (w2 >> 21) & 31 == r and (w2 & 0xffff) == lo and w2 >> 26 != 0xf:
                    res.append(j * 4 + BASE); break
    return res
def dis(addr, n=40):
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 + capstone.CS_MODE_LITTLE_ENDIAN)
    off = addr - BASE
    for ins in md.disasm(D[off:off + n * 4], addr):
        print('%08x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))
if __name__ == '__main__':
    load()
    if sys.argv[1] == 'refs': print([hex(x) for x in refs(int(sys.argv[2], 16))])
    else: dis(int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 40)
