"""한글패치 ISO 빌드: 원본 복사 → DATA.0 재조립(수정 엔트리 반영) → ELF/BIN 제자리 패치 → ISO9660·UDF 갱신."""
import os, sys, shutil, struct, time
sys.path.insert(0, os.path.dirname(__file__))
import iso, data0, isopatch
ROOT = iso.ROOT
OUT = os.path.join(ROOT, 'Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan) (Korean).iso')
DIR_LBA, UDF_PART, UDF_FE = 261, 264, range(269, 313)

def write_iso(mods, files=None, out=OUT):
    """mods: DATA.0 {인덱스: bytes}, files: {'/SLPM_657.78': bytes(같은 크기)}."""
    t0 = time.time()
    shutil.copyfile(iso.ISO, out)
    F = iso.files()
    with open(out, 'r+b') as f:
        dl, ds = F['/DATA.0']
        n = data0.rebuild_into(f, mods, dl)
        end = dl + (n + 2047) // 2048
        dfl, dfs = F['/DF.001']
        old_end = dfl + (dfs + 2047) // 2048
        assert end + 16 < old_end, 'DATA.0 이 DF.001 영역을 넘음'
        if n != ds:
            isopatch.relocate(f, 'DATA.0', dl, n, DIR_LBA, 1, UDF_PART, UDF_FE)
            isopatch.relocate(f, 'DF.001', end, (old_end - end) * 2048, DIR_LBA, 1, UDF_PART, UDF_FE)
        for name, d in (files or {}).items():
            l, s = F[name]; assert len(d) == s, name
            f.seek(l * 2048); f.write(d)
    print('ISO 완료 %.0fs, DATA.0 %d → %d (+%d)' % (time.time() - t0, ds, n, n - ds))
    return out
