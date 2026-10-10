# 드래곤 포스 (Dragon Force) PS2 한글패치

PS2 일본판 **SEGA AGES 2500 シリーズ Vol.18 ドラゴンフォース (SLPM-65778)** 용 비공식 한국어 패치입니다. 8개국 시나리오의 이벤트 대사 전체, 장수 대사, 전투 함성, 메뉴·시스템 문자열, EXTRA 도감, 군주 소개·지도 등 그림 속 글자, 전투 화면의 이름·제목 그림까지 한국어로 바꿨습니다(번역 단위 18,350개). 현재 배포판은 **v1.1 (2026-10-11)** 입니다.

[패치 다운로드](https://github.com/snake759494/dragon-force-ps2-korean-patch/releases/latest) · [기술 설명](docs/TECHNICAL.md) · [재빌드](docs/BUILD.md) · [변경 기록](CHANGELOG.md) · [권리 안내](RIGHTS.md)

릴리즈 첨부 파일은 **DragonForce_PS2_KO_v1.1.xdelta 하나**입니다. 저장소에는 제작 도구·번역 결과·검증 자료만 공개합니다. 원본 및 완성 디스크 이미지, 게임에서 추출한 파일, 일본어 원문 대사, 글꼴 파일, 외부 실행 파일은 포함하지 않습니다.

> ⚠️ `translation/` 폴더에는 게임 대사 번역 전문이 들어 있어 **줄거리 스포일러**가 포함됩니다.

## 대상 버전

이 패치는 **PS2 일본판 SLPM-65778 의 DVD ISO (2,048 바이트 섹터)** 에만 적용합니다.

| 항목 | 값 |
| --- | --- |
| 게임 ID | SLPM-65778 |
| 원본 형식 | 수정되지 않은 일본판 DVD ISO |
| 원본 ISO 크기 | 4,690,051,072 바이트 |
| **원본 ISO MD5** | `ce3864ac5a611a5313adac4257826da1` |
| 원본 ISO SHA-1 | `d2ec59db4790c6c26e4cc9f87a2827cc6f0b1281` |
| 원본 ISO SHA-256 | `1f31435239c2e5a9967a4a3acbc4dac978283b3a3d9b3a45af673ce057a87a60` |
| xdelta 파일 크기 | 27,652,786 바이트 |
| xdelta SHA-256 | `3be4a7a8ec43fa172ecbbcb9a350990f35b1e87caaeb5e5aa4119185b355fdce` |
| 적용 결과 ISO 크기 | 4,690,051,072 바이트 (원본과 같음) |
| 적용 결과 ISO SHA-1 | `66fe3820c2fbb2fda067757aa6e2dc1c9af6f39c` |
| 적용 결과 ISO SHA-256 | `66d0e9cb454ea614ad9f459ea55a3916272400a42d36592ccecf908ceab69224` |

## 패치 적용 방법

### 원본 확인 (Windows)

```powershell
Get-FileHash -Algorithm MD5 -LiteralPath ".\Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan).iso"
```

위 표와 다르면 적용을 중단하세요. CHD·CSO 로 변환한 이미지에는 적용할 수 없습니다.

### xdelta UI 사용

1. 릴리즈에서 `DragonForce_PS2_KO_v1.1.xdelta` 를 받습니다.
2. xdelta3 패치 도구의 **Apply Patch** 를 엽니다.
3. **Patch** 에 xdelta 파일, **Source File** 에 해시가 일치하는 원본 ISO 를 선택합니다.
4. **Output File** 에 새 파일명(예: `Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan) (Korean).iso`)을 지정합니다.

xdelta 는 호환성을 위해 압축 없이(`-0`), 2차 압축과 파일 경로 헤더 없이 만들었습니다.

### 명령줄 사용

```powershell
.\xdelta3.exe -d -s ".\Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan).iso" .\DragonForce_PS2_KO_v1.1.xdelta ".\Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan) (Korean).iso"
```

해시를 자동 검사하는 도구도 있습니다(Python 3 + xdelta3 필요, 기존 출력 파일은 덮어쓰지 않음).

```powershell
python tools/apply_release.py --xdelta .\xdelta3.exe --source ".\Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan).iso" --patch .\DragonForce_PS2_KO_v1.1.xdelta --output ".\Sega Ages 2500 Series Vol. 18 - Dragon Force (Japan) (Korean).iso"
```

### PCSX2 에서 실행

한글판 ISO 를 여세요. **원본판에서 만든 세이브 스테이트는 불러오지 마세요**(글꼴·문자열이 메모리에 남아 있어 글자가 깨집니다). 메모리 카드 세이브는 원본판과 호환됩니다.

## 작업 내용과 범위

| 구분 | 내용 |
| --- | --- |
| 대사 | 8개국(하이랜드·판다리아·문팰리스·이즈모·트라드노아·토파즈·보자크·트리스탄) 이벤트 대사 전체, 동료 영입·마물 이벤트, 엔딩, 장수별 출진·교섭·등용·일기토·승패 대사 |
| 전투 | 전투 함성, 마드룩 결전 대사, 여신 아스테아 부활 대사, VS 화면 장수명·국가·병종·軍·師団·地形効果 그림, 陣形選択·一騎討ち 제목 그림 |
| 메뉴 | 데이터 화면, 국가 선택, 성 메뉴, 전공 일람표, 무장 정보(작은 글꼴 포함), 아이템, 진형·명령, 메모리 카드 메시지 |
| EXTRA | 창성기·장성록·잊을 수 없는 기억·아이템 도감·대륙 전도·병법 해설 |
| 그림 글자 | 8개국 군주 소개 그림, 병법 해설 2쪽, 레젠드라 대륙 지도의 지명 39개 — 원본 글자를 지우고 같은 자리에 한글 |
| 글꼴 | 원본(32×32 굵은 둥근 고딕)과 가장 비슷한 나눔스퀘어 네오 ExtraBold 로 한글 2,351자(KS X 1001 2,350자 + 추가 1자), 16px 작은 글꼴용 글리프 별도 제작 |
| 번역 | 외부 기계번역 없이 직접 번역, 용어집(약 510항목)으로 고유명사 통일 |
| 그대로 둔 것 | **동영상(오프닝·데모·엔딩) — 자막 없음**, 저작권 표기, 영문 로고, 개발용 디버그 문자열 |

## 안정성

PS2 판은 PS2 계층 위에서 새턴 SH-2 프로그램을 실행하는 구조입니다. 실행 코드는 바꾸지 않았고, 문자열·글꼴·그림 데이터만 교체했습니다. 바이너리 안 문자열은 원래 칸 안에서 제자리 교체했고, 데이터 아카이브(DATA.0)는 재조립 후 ISO9660·UDF 디렉터리를 갱신했습니다(ISO 크기는 원본과 같음). 구조는 [docs/TECHNICAL.md](docs/TECHNICAL.md) 에 있습니다.

## 알려진 점

- v1.1 에서 음성과 대사가 어긋나던 문제를 고쳤습니다(대사를 원문과 같은 쪽 수로 나눔).

- 동영상 자막은 넣지 못했습니다. PS2 동영상 재생기가 다시 인코딩한 영상에서 멈추는 문제가 있어 원본 영상을 그대로 둡니다.
- PCSX2 에서 부팅, 데이터 화면, 국가 선택, 군주 소개, 오프닝 이벤트, 전공 일람표, 성 메뉴, 무장 정보, 전투 진입까지 확인했습니다. 전체 스토리 완주와 모든 전투 장면은 확인하지 못했습니다.
- 성 메뉴가 4글자씩 겹쳐 보이는 배치는 원본과 같은 동작입니다.
- 멈춤·줄 넘침·오역은 이슈로 알려 주세요.
