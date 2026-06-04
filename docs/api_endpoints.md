# 자이 스마트홈 API 엔드포인트 명세서 (XiHome API Endpoints)

본 문서는 자이 스마트홈(XiHome) 비공식 IoT 백엔드 서버와 통신하기 위한 HTTP REST API 명세서입니다.

---

## 1. 서버 정보 및 기본 호스트 (Hosts)

자이 스마트홈 백엔드는 인증 처리 서버와 실제 기기 상태 조회 및 제어를 처리하는 서버가 포트 단위로 분리되어 있습니다.

* **인증 및 세션 서버 (Port 5451)**: `https://camellia-back.xihome.kr:5451/api`
* **기기 목록 및 제어 서버 (Port 5452)**: `https://camellia-back.xihome.kr:5452/api`

---

## 2. 공통 헤더 규격 (Common Headers)

기기 조회 및 제어 API (`:5452` 포트 엔드포인트) 호출 시, 서버 검증을 위해 아래의 HTTP 헤더가 필수로 전달되어야 합니다.

```http
Authorization: Bearer <access_token>
device_token: <UUID>
Origin: https://camellia-front.xihome.kr
User-Agent: Mozilla/5.0 (Linux; Android 16; SM-A366N) AppleWebKit/537.36 XiHome/1.0.0 python-lib
Host: camellia-back.xihome.kr:5452
```

* `Authorization`: 로그인(`POST /auth/login`) API에서 반환받은 `access_token`입니다.
* `device_token`: 각 디바이스(클라이언트)를 구분하기 위해 생성한 고유 UUID 형태의 문자열입니다.
* `Origin` & `Host`: 서버 내부의 접근 제어 필터를 우회하기 위해 반드시 고정 매칭되어야 합니다.

---

## 3. 공통 쿼리 매개변수 (Common Query Parameters)

기기 조회 및 상태 전송 요청 시 세대 식별 및 권한 확인을 위해 아래의 세 가지 변수가 필수로 포함되어야 합니다.
* **`dong_no`**: 동 번호 (문자열 형식이며, 앞자리의 0은 제거되어야 합니다. 예: `"0102"` ➡️ `"102"`)
* **`ho_no`**: 호 번호 (문자열 형식이며, 앞자리의 0은 제거되어야 합니다. 예: `"0503"` ➡️ `"503"`)
* **`apt_code`**: 아파트 단지 코드 (로그인 응답에서 반환되는 문자열)

---

## 4. API 상세 정의

### 🔑 A. 사용자 로그인 (Login)
* **메소드 및 URL**: `POST https://camellia-back.xihome.kr:5451/api/auth/login`
* **설명**: 아이디와 비밀번호를 사용하여 자이 스마트홈 클라우드에 세션을 연결하고, 세션 토큰 및 세대 정보를 조회합니다.
* **요청 헤더**: `Content-Type: application/json`
* **요청 바디 (JSON)**:
  ```json
  {
    "username": "USER_ID",
    "password": "PASSWORD",
    "device_token": "DEVICE_UUID",
    "device_model_name": "Home Assistant"
  }
  ```
* **응답 바디 (성공 - 200/201)**:
  ```json
  {
    "access_token": "access_token_jwt_string...",
    "refresh_token": "refresh_token_jwt_string...",
    "last_selected_household": {
      "last_selected_apt_code": "APT_CODE",
      "last_selected_dong_no": "DONG_NO_RAW",
      "last_selected_ho_no": "HO_NO_RAW"
    }
  }
  ```

---

### 🔄 B. 토큰 갱신 (Token Refresh)
* **메소드 및 URL**: `POST https://camellia-back.xihome.kr:5451/api/auth/token`
* **설명**: 액세스 토큰(`access_token`)이 만료(401 Unauthorized)되었을 때 리프레시 토큰을 이용해 토큰 쌍을 재발급 받습니다.
* **요청 바디 (JSON)**:
  ```json
  {
    "refresh_token": "REFRESH_TOKEN",
    "device_token": "DEVICE_UUID",
    "device_model_name": "Home Assistant"
  }
  ```
* **응답 바디 (성공)**:
  ```json
  {
    "result": {
      "access_token": "NEW_ACCESS_TOKEN",
      "refresh_token": "NEW_REFRESH_TOKEN"
    }
  }
  ```
  *(참고: 서버 구현에 따라 `result` 필드로 래핑되어 있거나 루트 레벨에 직접 존재할 수 있으므로 파싱 시 양쪽 구조 모두 대응해야 합니다.)*

---

### 📋 C. 세대 등록 정보 조회 (Get Household Details)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5451/api/auth/household`
* **설명**: 현재 세션 사용자 계정에 등록된 아파트 단지 정보 목록 및 동, 호 정보를 명시적으로 조회합니다.
* **요청 헤더**:
  * `Authorization: Bearer <access_token>`
  * `Content-Type: application/json`
* **응답 바디 (성공)**:
  ```json
  [
    {
      "apt_code": "APT_CODE",
      "dong_no": "DONG_NO_RAW",
      "ho_no": "HO_NO_RAW"
    }
  ]
  ```

---

### 🏠 D. 세대 내 방 목록 조회 (Get Rooms)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/device/room`
* **설명**: 해당 세대에 구성되어 있는 방 목록(방 번호, 방 이름)을 반환합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`
* **응답 바디 (성공)**:
  ```json
  {
    "result": {
      "rooms": [
        {
          "room_id": "1",
          "room_name": "거실"
        },
        {
          "room_id": "2",
          "room_name": "침실 1"
        }
      ]
    }
  }
  ```

---

### 🔌 E. 방 별 기기 목록 조회 (Get Devices by Room)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/device/list-redis/by_room_id`
* **설명**: 특정 방 번호(`room_id`) 내에 위치한 모든 스마트홈 기기들의 목록과 각 기기의 상세 상태 속성값을 일괄 반환합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`, `room_id` (예: `"1"`)
* **응답 바디 (성공)**:
  ```json
  {
    "result": {
      "devices": [
        {
          "device_uuid": "device_uuid_string",
          "device_id": "light_living_1",
          "device_name": "1.디밍조명",
          "device_type": "dimming",
          "status": {
            "power": true,
            "dimming": "3"
          }
        }
      ]
    }
  }
  ```

---

### 📊 F. 메인 대시보드 기기 그룹 요약 조회 (Get Main Summaries)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/main/list-redis-main`
* **설명**: 대시보드 구성을 위해 세대 내 전체 기기 그룹별 상태 요약 정보(가동 중인 기기 개수, 이동 경로 등)를 일괄 반환합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`
* **응답 바디 (성공)**:
  ```json
  {
    "resultCode": "success",
    "messageCode": "success",
    "result": {
      "device_group_heating": { "tot_device_num": 4, "power_on_device_num": 1 },
      "device_group_light": { "tot_device_num": 8, "power_on_device_num": 3 },
      "device_group_standby": { "tot_device_num": 6, "power_on_device_num": 2 },
      "device_group_vent": {
        "device_group_name": "시스클라인",
        "tot_device_num": 2,
        "power_on_device_num": 1,
        "power_off_device_num": 1,
        "webview_route_to": "https://camellia-front.xihome.kr/home/home-device/sysclein/list"
      }
    }
  }
  ```

---

### 🔍 G. 개별 기기 상세 조회 (Get Device Status)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/device`
* **설명**: 특정 디바이스 한 개의 현재 세부 센서값과 파라미터를 정밀 조회합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`, `device_type`, `device_id` (예: `device_type=acs2&device_id=acs_7_0`)
* **응답 바디 (성공)**:
  ```json
  {
    "resultCode": "success",
    "result": {
      "devices": [
        {
          "device_uuid": "device_uuid_string",
          "device_id": "acs_7_0",
          "device_type": "acs2",
          "status": {
            "power": true,
            "erv_runstate": "1",
            "erv_air_volume": "1",
            "co2_value": "501"
          }
        }
      ]
    }
  }
  ```

---

### 🎛️ H. 기기 제어 명령 전송 (Send Command)
* **메소드 및 URL**: `POST https://camellia-back.xihome.kr:5452/api/device/{endpoint}/command`
* **설명**: 특정 기기의 작동 상태(전원, 밝기 단계, 설정 온도 등)를 변경하는 제어 패킷을 송신합니다.
* **경로 변수 `{endpoint}`**: 제어하려는 기기의 API 분류 엔드포인트명
  * `light` (일반 조명)
  * `dimming` (밝기조절 조명)
  * `heating` (온도조절 난방)
  * `standby` (대기전력 콘센트)
  * `acs` (환기/시스클라인 시스템)
* **요청 헤더**: 공통 헤더 규격 적용
* **요청 바디 (JSON)**:
  ```json
  {
    "dong_no": "DONG_NO",
    "ho_no": "HO_NO",
    "apt_code": "APT_CODE",
    "device_id": "DEVICE_ID",
    "status": {
      // 제어용 상태 필드 데이터 세트 (기기별 상세 스키마는 기기 데이터 모델 문서 참조)
    }
  }
  ```
* **응답 상태**: 성공 시 HTTP Status Code `200` 또는 `204` 반환. 실패 시 에러 코드 필드가 포함된 에러 응답 객체 반환.

---

### 🍃 I. 환기 장치 미세먼지 수치 요청 (Get Dust Level)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/device/acs/dust`
* **설명**: 환기 공기청정 시스템(시스클라인 등) 장치의 정밀 미세먼지(PM1.0, PM2.5, PM10 등) 값을 개별 조회합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`, `device_id`, `dust_unit` (예: `PM1.0`, `PM2.5`, `PM10`)
* **응답 바디 (성공)**:
  ```json
  {
    "resultCode": "success",
    "result": {
      "dust_value": "53",
      "dust_unit": "PM2.5",
      "status_txt": "농도:53µg/㎥",
      "statusEn": "bad",
      "statusValue": "2",
      "retreve_from_server": true
    }
  }
  ```

---

### 🚪 J. 공동현관 로비폰/도어락 목록 조회 (Get Lobby/Doorlocks)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/public/doorlock`
* **설명**: 세대와 연동된 공동현관(1층 입구, 지하 주차장 입구 등) 로비폰 및 도어락 목록을 조회합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`
* **응답 바디 (성공 - 200 OK)**:
  ```json
  {
    "result": {
      "list": [
        {
          "lobbydong": "DONG_NO",
          "lobbyho": "9001",
          "comment": "1_2라인1F",
          "label": "DONG_NO동 1_2라인1F"
        },
        {
          "lobbydong": "DONG_NO",
          "lobbyho": "9011",
          "comment": "1_2라인B1",
          "label": "DONG_NO동 1_2라인B1"
        },
        {
          "lobbydong": "DONG_NO",
          "lobbyho": "9021",
          "comment": "1_2라인B2",
          "label": "DONG_NO동 1_2라인B2"
        }
      ]
    },
    "resultCode": "success",
    "messageCode": "success",
    "resultMessage": "정상적으로 처리되었습니다.",
    "resultTitle": "성공"
  }
  ```

---

### 🚗 K. 세대 차량 주차 위치 조회 (Get Parking Location)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/public/parking_location`
* **설명**: 아파트 지하 주차장의 주차인식 카메라 등을 통해 식별된 세대 등록 차량의 주차 위치 정보를 조회합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`
* **응답 바디 (성공 - 200 OK)**:
  ```json
  {
    "result": {
      "result": "0",
      "list": [
        {
          "tagid": "0",
          "carno": "****CAR_NUMBER_LAST_4_DIGITS",
          "floor": "B1_2",
          "block": "DONG_NO-B_PARKING_BLOCK",
          "label": "지하 1_2층 DONG_NO-B_PARKING_BLOCK",
          "in_parking_datetime_label": "",
          "image_filename": ""
        }
      ],
      "errmsg": "",
      "status": {
        "parking_register_method": "camera",
        "FAVORITE_PARKING_yn": "Y"
      }
    },
    "resultCode": "success",
    "messageCode": "success",
    "resultMessage": "정상적으로 처리되었습니다.",
    "resultTitle": "성공"
  }
  ```

---

### 📅 L. 방문 차량 예약 목록 조회 (Get Parking Reservations)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/public/parking_reservation`
* **설명**: 세대에 등록된 방문 차량 예약 목록을 조회합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`
* **응답 바디 (성공 - 200 OK - 예약 데이터 없음 예시)**:
  ```json
  {
    "resultCode": "success",
    "resultMessage": "정상적으로 처리되었습니다.",
    "result": {
      "list": [],
      "result": "3206",
      "errmsg": "데이터를 찾을 수 없습니다."
    },
    "messageCode": "success",
    "resultTitle": "성공"
  }
  ```

---

### ⏰ M. 방문 차량 예약 가능 시간 조회 (Get Parking Reservation Available Times)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/public/parking_reservation/available_time`
* **설명**: 방문 차량 예약을 신청할 때 허용되는 예약 시간대 정책 및 활성화 여부를 조회합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`, `year` (예: `2026`), `month` (예: `6`)
* **응답 바디 (성공 - 200 OK)**:
  ```json
  {
    "result": {
      "status": {
        "VISIT_PARKING_TIME_yn": "N",
        "VISIT_WELCOME_yn": "N"
      }
    },
    "resultCode": "success",
    "messageCode": "success",
    "resultMessage": "정상적으로 처리되었습니다.",
    "resultTitle": "성공"
  }
  ```

---

### 🛡️ N. 공동현관 방문자 사진/동영상 및 출입 로그 조회 (Get Security/Visitor Logs)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/public/security`
* **설명**: 공동현관 로비폰에서 세대 호출 시 촬영된 방문자 사진(Base64 이미지 데이터) 및 호출 당시 녹화된 비디오(murl 동영상 스트림 경로) 목록을 조회합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`, `page` (예: `1`), `list_count` (예: `5`)
* **응답 바디 (성공 - 200 OK)**:
  ```json
  {
    "resultCode": "success",
    "resultMessage": "정상적으로 처리되었습니다.",
    "result": {
      "list": [
        {
          "seq": 1,
          "date": "**************",
          "filename": "outdoor_**************_0.jpg",
          "mfilename": "outdoor_**************_0.mp4",
          "murl": "aHR0cHM6Ly9bSVBf****************************************Tk9dL1tIT19OT10vb3V0ZG9vci9vdXRkb29yXzIwMjYwNjA0MDg0MDA2XzAubXA0",
          "data": "<BASE64_IMAGE_DATA>",
          "link": "base64",
          "location": "mv_outdoor"
        }
      ],
      "result": "0",
      "comment": "방문자 이력은 최근 6개월까지만 조회됩니다.",
      "total": 32
    },
    "messageCode": "success",
    "resultTitle": "성공"
  }
  ```

---

### ⚙️ O. 사용자 지정 스마트 모드 조회 (Get Custom Smart Modes)
* **메소드 및 URL**: `GET https://camellia-back.xihome.kr:5452/api/smartmode/by_me`
* **설명**: 사용자가 모바일 앱 또는 월패드에서 사전에 설정해 둔 스마트 홈 모드(예: 전체 소등, 외출 모드, 귀가 모드 등)의 목록과 적용 상태를 조회합니다.
* **요청 헤더**: 공통 헤더 규격 적용
* **쿼리 매개변수**: `dong_no`, `ho_no`, `apt_code`, `mode` (예: `all`)
* **응답 상태**: 캐시 데이터가 일치할 시 `304 Not Modified`를 반환하며, 데이터 변경 시 신규 설정 목록(`200 OK`)을 반환합니다.

