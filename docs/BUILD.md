# 재빌드

필요: Python 3 (numpy, Pillow, opencv-python), xdelta3, 원본 ISO, 글꼴.

1. 저장소 루트에 원본 `Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan).iso` 를 둡니다.
2. 글꼴을 저장소 루트에 둡니다: [나눔스퀘어 네오](https://campaign.naver.com/nanumsquare_neo/) 의 `NanumSquareNeo-cBd.ttf`·`NanumSquareNeo-dEb.ttf`, [서울서체](https://www.seoul.go.kr/seoul/font.do) 의 `SeoulHangangEB.ttf`.
3. (선택) 원문 단위 생성(원문은 저장소에 없음): `python -X utf8 tools/extract.py` → `translation/units.json`
4. 빌드: `python -X utf8 tools/build_all.py` → 루트에 `Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan) (Korean).iso`
5. 패치: `xdelta3 -e -0 -S none -A -B 2147483648 -s "<원본>.iso" "<한글판>.iso" DragonForce_PS2_KO_v1.2.xdelta`

번역 파일은 모두 `{원문 SHA-1 앞 12자리: 한국어}` 형태입니다.

- `translation/out/j*.json` — 작업 단위별 번역
- `translation/ko/halfkana.json` — 반각 칸 문자열(장수명·병종 등), `fix_nation.json` — 교정, `bin_alt.json` — 바이너리 칸 전용 짧은 번역, `fit.json` — 원문 쪽 수에 맞춰 줄인 대사, `pages.json` — 여러 쪽 발언의 쪽별 번역(원문 쪽 내용·음성과 일치, `{키: [쪽1, 쪽2, …]}`)
- `translation/glossary.json` — 고유명사(전투 이름 그림에 사용), 사람이 읽는 표는 `glossary.md`
- `translation/images.json` — 그림 글자 번역

빌드 결과 SHA-1 이 `3010f43eed95ba1273ec9bc045ef4fe10769faec` 이면 릴리즈와 같습니다.
