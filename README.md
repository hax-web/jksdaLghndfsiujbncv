# 디스코드 통합 봇

## 폴더 구조
```
discord_bot/
├── main.py              # 봇 실행 파일
├── requirements.txt
└── cogs/
    ├── news.py           # ✈️ 항공 뉴스 (/자동, /자동해제, /비행기뉴스, /항공검색)
    ├── ai_chat.py         # 🤖 AI 질문 (/질문)
    ├── leveling.py        # 📈 레벨링 (/레벨, /랭킹)
    ├── tickets.py          # 🎫 티켓 (/티켓생성, /티켓닫기)
    └── help.py            # 📖 도움말 (/도움말)
```

## 설치
```
pip install -r requirements.txt
```

## Railway 환경변수
| 변수명 | 설명 |
|---|---|
| `DISCORD_TOKEN` | 디스코드 봇 토큰 (필수) |
| `GROQ_API_KEY` | AI 질문 기능용 Groq API 키 (무료, console.groq.com 에서 발급, 신용카드 불필요) (없으면 `/질문` 명령어만 비활성화) |

## 실행
```
python main.py
```

## 참고
- 뉴스 자동알림, 레벨 데이터, 뉴스 중복 방지 기록은 `data/` 폴더에 json 파일로 저장됩니다.
  Railway에 배포할 경우 재배포 시 파일이 초기화될 수 있으니, 데이터를 계속 유지하려면 Railway Volume을 연결하는 걸 추천해요.
- `/도움말`을 치면 코그(카테고리)별로 명령어가 묶여서 나옵니다. 나중에 기능(코그)을 추가하면 자동으로 도움말에도 포함됩니다.
- 봇 초대 시 필요한 권한: 채널 관리(티켓용), 메시지 보내기/읽기, 임베드 링크, 애플리케이션 명령어.
- Discord 개발자 포털에서 **Message Content Intent**를 꼭 켜주세요 (레벨링 기능에 필요합니다).
