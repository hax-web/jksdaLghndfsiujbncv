# Discord 종합 봇

GitHub → Railway 배포를 기준으로 만든 Discord 종합 봇입니다.

## 포함 기능
- 미니게임: 홀짝, 가위바위보, 주사위, 숫자 맞히기
- 관리: 청소, 추방, 차단, 공지
- 레벨 시스템
- 티켓 시스템
- 정해진 시간 자동 채팅
- 봇 설정
- 음악 재생 / 일시정지 / 재개 / 스킵 / 정지 / 대기열

## 1. Discord 봇 만들기
Discord Developer Portal에서 봇을 만들고 토큰을 발급합니다.

Bot 설정에서 다음 Intent를 켜는 것을 권장합니다.
- Message Content Intent
- Server Members Intent

## 2. GitHub
이 프로젝트 전체를 GitHub 저장소에 업로드합니다.

## 3. Railway
Railway에서 GitHub 저장소를 연결합니다.

Variables에 다음을 추가합니다.

DISCORD_TOKEN=여기에_봇_토큰

토큰은 GitHub에 절대 올리지 마세요.

## 4. 음악 기능
음악 기능은 yt-dlp와 FFmpeg를 사용합니다.
Railway 환경에서 FFmpeg가 필요합니다. 배포 환경에서 FFmpeg가 없다면 Railway/Nixpacks 설정으로 FFmpeg를 추가하세요.

## 5. 시작
Railway가 requirements.txt를 기준으로 패키지를 설치하고 bot.py를 실행하도록 설정하면 됩니다.

권장 Start Command:
python bot.py

## 주요 명령어
/홀짝
/가위바위보
/주사위
/숫자맞히기

/청소
/추방
/차단
/공지

/레벨
/랭킹
/레벨채널

/티켓설정
/티켓카테고리

/반복채팅추가
/반복채팅목록
/반복채팅삭제

/음악재생
/음악일시정지
/음악재개
/음악스킵
/음악정지
/대기열
