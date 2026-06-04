# ⚠️ 바이브 코딩 되었습니다! ⚠️
# HomeAssistant-XiHome
🐟 자이 홈과 Home Assistant를 연결해주는 커스텀 컴포넌트.

# 이게 뭔가요?
자이 홈 앱과 홈 어시스턴트를 연동해주는 컴포넌트입니다.
현재 지원되는 기능은 다음과 같습니다.
| 기능 | 지원 |
| -- | -- |
| 조명 컨트롤 | <span title="조명 켜고 끄기 / 디밍 4단계 조절 지원">✅</span> |
| 난방 컨트롤 | <span title="온도 조절 / 외출 모드 토글 지원">✅</span> |
| 시스클라인(Sysclein) 지원 | <span title="일부 오류가 있는 채로 미세먼지 확인 지원">⚠️</span> |
| 가스밸브 컨트롤 | <span title="인덕션 사용중, 테스트 불가">❌</span> |
| 기타 편의 기능 | <span title="현재 개발중">❌</span> |
> 아이콘에 마우스를 올려서 지원되는 것을 확인해 보세요.

# 설치
1. [HACS](https://hacs.xyz) 사용
   1. HACS 대시보드에서 더보기 ⋮ 클릭
   2. Custom repositories 클릭
   3. Repository에 `https://github.com/sungsoos/HomeAssistant-XiHome`를 입력 후, Type는 `Integration`로 선택, 추가.
   4. "자이 홈 연동"을 검색 후, 설치
   5. Home Assistant 재시작
2. 직접 설치
   1. [여기](https://download-directory.github.io/?url=https%3A%2F%2Fgithub.com%2Fsungsoos%2FHomeAssistant-XiHome%2Ftree%2Fmain%2Fcustom_components%2F)에서 파일 다운로드
   2. 설정 폴더의 custom_components에서 압축 해제
   3. Home Assistant 재시작

## 기여하기 위한 정보
- 내부 api를 얻기 위해서 [mitmproxy](https://www.mitmproxy.org/)를 사용했습니다.
- 개발을 위한 정보는 [/docs](docs)를 확인하세요.
