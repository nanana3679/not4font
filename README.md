# NOT4FONT

NOT4FONT는 리듬 게임 NOT4K의 UI 글꼴이다. 로고 1판의 굵기에서 나온 Bold와 일반 UI에 쓰는 Regular, 두 굵기가 있다. 글자는 대문자 A～Z와 숫자 0～9다.

## 지금 상태

- 1판(2026-11-26): 모양을 정했다. `ed1/`에 글자마다 SVG가 있다.
- Regular와 Bold의 시험용 TTF와 WOFF2를 만들 수 있다. R 다음 글자가 겹치면 OpenType `calt`로 잘라 둔 글리프를 쓴다.
- 시험용 글꼴에서 Z의 위아래 가로획 끝은 T 상단과 같은 52도 사선으로 자른다.
- Bold의 `calt`는 검토에서 허용한 삐침을 낱말 첫 글자 왼쪽과 마지막 글자 오른쪽에 붙인다. 영문과 숫자가 이어지면 한 낱말로 본다.

## 폴더

- `not4k_font/`: 1판의 글자 윤곽, 굵기별 숫자, 간격 규칙을 정의한다. SVG와 글꼴 파일을 만드는 두 스크립트가 이 모듈을 사용한다.
- `rounds/`: 디자인 세션에서 회차마다 쓴 스크립트를 보관한다. 기록을 재현할 때 앞 회차 파일을 읽으므로 같은 폴더에 둔다.
- `export_ed1.py`: 1판을 `ed1/`로 내보낸다.
- `export_fonts.py`: 1판의 두 굵기를 TTF와 WOFF2로 내보낸다.
- `specimen.html`: 브라우저에서 WOFF2와 1판 SVG 견본을 겹쳐 본다.
- `ed1/`: 1판 글자 SVG(`regular/`, `bold/`), 견본(`specimen-*.svg`), 굵기 숫자와 간격 규칙(`font-ed1.json`).
- `history/`: 회차마다 정한 것과 그 이유다. 게임 저장소 디자인 보드의 기록에서 옮겨 왔다.

## 실행

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python export_ed1.py
.venv/bin/python export_fonts.py
.venv/bin/python -m unittest
```

글꼴 파일은 `out/fonts/`에 `NOT4FONT-Regular`, `NOT4FONT-Bold`(TTF, WOFF2)로 생성된다. `.venv/bin/python -m http.server 8000`을 실행한 뒤 [견본 비교 페이지](http://localhost:8000/specimen.html)를 연다.
CSS에서 이 판의 글꼴을 사용할 때는 `font-family: NOT4FONT`와 `font-kerning: normal`을 지정한다.
Bold에서 위쪽 삐침을 우선하려면 `font-feature-settings: "ss01" 1`을, 아래쪽을 우선하려면 `font-feature-settings: "ss02" 1`을 지정한다. 한 위치만 허용된 글자는 그 위치를 쓴다.
숫자 자리를 맞추려면 `font-variant-numeric: tabular-nums`를 지정한다. 가장 넓은 숫자의 윤곽에 글자 사이 간격을 더해 공통 너비를 정하고 각 숫자의 윤곽을 가운데에 둔다.

시험용 글꼴 파일은 두 굵기에 기호 38개를 담는다. 문장 부호와 연산 기호 `.…,:;-/%+()'"!?#&×<>$^~@`, 곡 목록과 튜토리얼에서 쓰는 `·—=←→↑↓`, 키보드 표시에 쓰는 기호 `` []\`* ``, 판정 표시에 붙는 `◇`와 같은 크기의 채운 `◆`를 지원한다. 두 마름모는 게임의 트릴 노트처럼 가로:세로가 5:1이다. CSS `text-overflow: ellipsis`에 쓰는 줄임표 `…`(U+2026)는 위 커닝 설정에서 게임이 쓰는 마침표 세 개 `...`와 점 모양, 위치, 간격, 전체 너비가 같다.

## 정한 것

- 단위는 대문자 높이 100, 기준선 0이다. 사선은 모두 52도(가로 0.78 : 세로 1)이고, 모서리는 높이 26으로 깎는다.
- Bold 굵기: 세로 30, 쌓이는 가로 24, O 계열 가로 26, 사선 26, 스텐실 틈 6, 글자 사이 6.
- Regular 굵기: 세로 16, 쌓이는 가로 14, O 계열 가로 15, 사선 14, 스텐실 틈 4, 글자 사이 12. 네모 글자(B C D E F G H J L O Q S T U, 0 2 3 5 6 8 9)는 Bold 너비의 90%다.
- 간격: 이웃한 두 글자의 가장 가까운 점 사이를 글자 사이 값으로 맞춘다. R은 위쪽(기둥과 둥근 칸)으로 재서 다리가 다음 글자 쪽으로 들어간다. 4는 기둥으로 재서 가로획이 글자 사이만큼 나와 다음 글자에 닿는다.
- 겹치면 왼쪽 글자가 이기고, 오른쪽 글자를 틈 하나만큼 둘레로 잘라 낸다. 닿기만 하는 것은 겹침이 아니다.
- 커닝은 RA만 25% 띄운다(Regular 18.9, Bold 14.3).
- 글자별: A는 4처럼 짠다. G는 C와 ㄱ을 세로 틈으로 나누고 ㄱ의 발은 직각이다. J는 갈고리 쪽 직각·기둥 쪽 40, U는 오른쪽 직각·왼쪽 40, V는 오른쪽 아래 모서리를 52도로 깎는다. K는 비대칭이다. Q 꼬리는 위가 40에서 평평하다. Z는 N처럼 나누고 작은 조각을 없앤다. 6과 9는 기둥 쪽이 평평하다. P와 R의 둥근 칸은 Regular 72, Bold 88이다.
- 디자인 보드는 게임 저장소의 `lab/image-galleries/menu-direction-20261122/`이다. 지난 작업 목록은 `index.html#relogo`에 있다.
