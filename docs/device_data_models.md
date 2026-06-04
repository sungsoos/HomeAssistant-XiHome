# 자이 스마트홈 기기 데이터 모델 및 제어 명세 (XiHome Device Models)

본 문서는 자이 스마트홈 API가 반환하는 기기 목록(`GET /device/list-redis/by_room_id`)의 JSON 데이터 구조와 각 기기별 제어 명령(`POST /device/{endpoint}/command`)에 사용되는 `status` 페이로드 규격을 상세히 정의합니다.

---

## 1. 공통 기기 구조 (Common Device Schema)

방 별 기기 목록 조회 시 반환되는 개별 기기 객체의 기본 스키마입니다.

```json
{
  "device_uuid": "기기_고유_UUID_식별자",
  "device_id": "기기_고유_식별자_문자열",
  "device_name": "API가_반환하는_원본_한글_기명",
  "device_name_by_room": "방별_설정_기명_또는_null",
  "name": "기본_지정_기명",
  "type": "기기_구분_타입_문자열",
  "device_type": "기기_구분_타입_문자열_2",
  "status": {
    // 기기 상태 속성 (기기 종류별로 다름)
  },
  "status_custom": {
    // 한국어 상태 문구 및 메타 정보 (선택적 존재)
  }
}
```

* `type` 및 `device_type`: 기기군 판별 시 사용됩니다.
* `device_name` 및 `device_name_by_room`: 장치의 한글 명칭 식별에 사용되며, 자이 백엔드 내부에서는 순번 접두사(`1.디밍조명`, `2.대기`)를 가질 수 있습니다.

---

## 2. 기기군 별 상태 조회 및 제어 페이로드 규격

### 💡 A. 일반 온/오프 조명 (Standard Light)
* **식별 기준**: `device_type` 또는 `type`에 `"light"`가 포함되고, `"alllight"`가 포함되지 않은 기기.
* **조회 상태 (`status`)**:
  ```json
  {
    "power": true // 켜짐: true / 문자열 "on", 꺼짐: false / 문자열 "off"
  }
  ```
* **제어 엔드포인트 경로**: `POST /api/device/light/command`
* **제어 status 페이로드**:
  ```json
  {
    "power": true // 켜기: true, 끄기: false
  }
  ```

---

### 💡 B. 밝기조절 디밍 조명 (Dimming Light)
* **식별 기준**: `device_type` 또는 `type`에 `"dimming"`이 포함된 기기.
* **조회 상태 (`status`)**:
  ```json
  {
    "power": true, // 전원 상태 (true/false)
    "dimming": "3" // 현재 밝기 단계 (문자열 또는 정수: 1 ~ 4)
  }
  ```
* **제어 엔드포인트 경로**: `POST /api/device/dimming/command`
* **제어 status 페이로드**:
  * **전원 켜기 및 단계 제어**:
    ```json
    {
      "power": true,
      "dimming": 4 // 제어할 단계 (정수: 1 ~ 4)
    }
    ```
  * **전원 끄기**:
    ```json
    {
      "power": false,
      "dimming": 0
    }
    ```

---

### 🌡️ C. 온도조절 난방기 (Heating / Thermostat)
* **식별 기준**: `device_type` 또는 `type`에 `"heating"` 또는 `"thermostat"`가 포함된 기기.
* **조회 상태 (`status`)**:
  * **현재 온도**: `current_temperature` 또는 `current_temp` 키에서 소수점 값(예: `23.5`) 형태로 전달됩니다.
  * **설정 온도 (희망 온도)**: API 사양 및 아파트 단지 버전에 따라 아래의 키들 중 하나에 희망 설정 온도(예: `22`)가 담겨 전달됩니다.
    * `temperature`, `target_temperature`, `target_temp`
    * `user_change` / `userChange`, `user_load` / `userLoad`
  * **전원 상태**: `power` 키 (켜짐: true / `"on"`, 꺼짐: false / `"off"`)
* **제어 엔드포인트 경로**: `POST /api/device/heating/command`
* **제어 status 페이로드**:
  * **난방 가동 및 희망 온도 변경**:
    ```json
    {
      "power": true,
      "temperature": 24 // 희망 설정 온도 (정수)
    }
    ```
  * **난방 정지 (외출/꺼짐)**:
    ```json
    {
      "power": false
    }
    ```

---

### 🔌 D. 대기전력 차단 콘센트 (Standby Power Switch)
* **식별 기준**: `device_type` 또는 `type`에 `"standby"`가 포함된 기기.
* **조회 상태 (`status`)**:
  ```json
  {
    "power": true // 차단 해제(상시 전원): true, 대기전력 차단 상태: false
  }
  ```
* **제어 엔드포인트 경로**: `POST /api/device/standby/command`
* **제어 status 페이로드**:
  ```json
  {
    "power": true // 콘센트 통전(ON): true, 차단(OFF): false
  }
  ```

---

### 🍃 E. 시스클라인 환기 및 공기청정 시스템 (Syscline / Ventilation)
* **식별 기준**: `device_type`이 `"acs2"`이거나, `device_id`에 `["vent", "purifier", "sysclein", "air", "환기", "공기청정", "acs"]` 키워드가 포함된 기기.
* **시스템 구조**: 환기 기능인 **ERV** (전열교환기) 유닛과 청정 기능인 **FAU** (외기도입 공기청정기) 유닛이 하나로 결합된 하이브리드 구조입니다.

#### 1. 조회 상태 (`status` 및 `status_custom`)
```json
{
  "status": {
    "power": true,               // 시스템 메인 전원 (FAU 동작상태 기준으로 동작)
    "erv_runstate": "1",         // ERV 전원 상태 ("0": 꺼짐, "1": 켜짐)
    "erv_air_volume": "1",       // ERV 풍량 단계 (아래 풍량 정의 참조)
    "erv_mode": "manual",        // ERV 동작 모드 (manual, auto, sleep)
    "erv_reserve_time": "0",     // ERV 꺼짐 예약 시간 (비활성화 시 "0")
    "erv_state": "0",            // ERV 내부 작동 상세 상태 코드
    "fau_runstate": "1",         // FAU 전원 상태 ("0": 꺼짐, "1": 켜짐)
    "fau_air_volume": "2",       // FAU 풍량 단계 (아래 풍량 정의 참조)
    "fau_mode": "manual",        // FAU 동작 모드 (manual, auto, sleep, reserve)
    "fau_reserve_time": "0",     // FAU 꺼짐 예약 시간
    "fau_state": "0",            // FAU 내부 작동 상세 상태 코드
    "dust_value": "40",          // 현재 주 센서 미세먼지 측정값 (ug/m3)
    "dust_unit": "PM1.0",        // 측정 미세먼지 규격
    "co2_value": "501",          // 이산화탄소 농도 (ppm)
    "smell_value": "1",          // 냄새/가스 오염도 단계
    "humidity_value": "55"       // 실내 상대 습도 (%)
  },
  "status_custom": {
    "status_txt": "켜짐",
    "device_status_txt": "정상",
    "filter_status_txt": "정상",
    "smell_status_txt": "좋음",
    "co2_status_txt": "농도:501ppm",
    "co2_statusEn": "good",
    "arr_dust": [
      {
        "dust_unit": "PM1.0",
        "dust_value": "40",
        "dust_label": "극초미세먼지",
        "status_txt": "농도:40µg/㎥",
        "statusEn": "bad",
        "statusValue": "2",
        "retreve_from_server": true
      },
      {
        "dust_unit": "PM2.5",
        "dust_value": "",
        "dust_label": "초미세먼지",
        "status_txt": "",
        "retreve_from_server": false
      },
      {
        "dust_unit": "PM10",
        "dust_value": "",
        "dust_label": "미세먼지",
        "status_txt": "",
        "retreve_from_server": false
      }
    ]
  }
}
```

#### 2. 풍량 및 동작 모드 상숫값 정의
* **풍량 단계 (`erv_air_volume` / `fau_air_volume`)**:
  * `"1"`: 약풍 (Low)
  * `"2"`: 중풍 (Medium)
  * `"3"`: 강풍 (High)
  * `"4"`: 터보 (Turbo)
  * `"9"`: 취침풍 (Sleep)
* **동작 모드 (`erv_mode` / `fau_mode`)**:
  * `"manual"`: 수동 제어 모드
  * `"auto"`: 자동 스마트 케어 모드
  * `"sleep"`: 저소음 야간 운전 모드
  * `"reserve"`: 예약 타이머 모드 (`fau_reserve_time` 필요)

#### 3. 제어 엔드포인트 및 필수 규격
* **제어 엔드포인트 경로**: `POST /api/device/acs/command`
* **🚨 필수 요구 사항**: 자이 백엔드는 제어 신호를 처리할 때 ERV와 FAU의 전원 및 모드 설정값 전체가 누락 없이 동시에 전달되어야 합니다. **따라서 아래의 `status` 객체 내 8개 속성이 반드시 모두 포함되어야만 400 Bad Request 에러가 발생하지 않습니다.**

```json
{
  "device_id": "acs_7_0",
  "dong_no": "DONG_NO",
  "ho_no": "HO_NO",
  "apt_code": "APT_CODE",
  "status": {
    "erv_runstate": "1",      // ERV 전원 ("0" 또는 "1")
    "erv_air_volume": "1",    // ERV 풍량 ("1"~"4", "9")
    "erv_mode": "manual",     // ERV 모드 ("manual", "auto", "sleep")
    "erv_reserve_time": "0",  // ERV 타이머 ("0"~"12")
    "fau_runstate": "1",      // FAU 전원 ("0" 또는 "1")
    "fau_air_volume": "2",    // FAU 풍량 ("1"~"4", "9")
    "fau_mode": "manual",     // FAU 모드 ("manual", "auto", "sleep", "reserve")
    "fau_reserve_time": "0"   // FAU 타이머 ("0"~"12")
  }
}
```

#### 4. 대표 제어 페이로드 예시

##### A. 공기청정 전용 모드 (FAU 가동, ERV 미풍)
```json
{
  "device_id": "acs_7_0",
  "dong_no": "DONG_NO",
  "ho_no": "HO_NO",
  "apt_code": "APT_CODE",
  "status": {
    "erv_runstate": "1",
    "erv_air_volume": "1",
    "erv_mode": "manual",
    "erv_reserve_time": "0",
    "fau_runstate": "1",
    "fau_air_volume": "3", // 강풍 가동
    "fau_mode": "manual",
    "fau_reserve_time": "0"
  }
}
```

##### B. 전체 시스템 OFF (전체 꺼짐)
```json
{
  "device_id": "acs_7_0",
  "dong_no": "DONG_NO",
  "ho_no": "HO_NO",
  "apt_code": "APT_CODE",
  "status": {
    "erv_runstate": "0",
    "erv_air_volume": "1",
    "erv_mode": "manual",
    "erv_reserve_time": "0",
    "fau_runstate": "0",
    "fau_air_volume": "1",
    "fau_mode": "manual",
    "fau_reserve_time": "0"
  }
}
```

---

### 🔒 F. 가스 밸브 제어기 (Gas Valve Switch)
* **식별 기준**: `device_type` 또는 `type`에 `"gas"`가 포함된 기기.
* **조회 상태 (`status`)**:
  ```json
  {
    "power": false // 열림: true, 닫힘: false
  }
  ```
  *(참고: `status_custom.status_txt` 필드를 통해 현재 가스 밸브의 한글 개폐 상태("닫힘" 또는 "열림")가 함께 표시됩니다.)*
* **제어 가능 여부**: 아파트 연동 가스 제어기 장치의 안전 규격 정책에 따라, 백엔드 API를 통한 원격 밸브 **열기(Open) 제어는 불가능하며 닫기(Close) 제어만 가능**하거나 상태만 조회할 수 있습니다. 

---

### 💡 G. 일괄 소등 스위치 (Master/Global Light Switch)
* **식별 기준**: `device_type` 또는 `type`에 `"alllight"`가 포함된 기기.
* **조회 상태 (`status`)**:
  ```json
  {
    "power": true // 일괄 소등 켜짐(소등 상태 활성화): true, 꺼짐(일반): false
  }
  ```
  *(참고: `status_custom.status_txt` 필드를 통해 한글 상태("켜짐" 또는 "꺼짐")가 함께 표시됩니다.)*

