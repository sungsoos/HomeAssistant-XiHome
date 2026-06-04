import requests

# Base configurations derived from decompiled resources
BASE_URL = "https://camellia-back.xihome.kr:5451/api"  # Prod URL
# For Dev: BASE_URL = "https://dev-camellia-back.xihome.kr:5451/api"


def get_auth_token(username, password, device_token, device_model_name):
    """
    Simulates the POST /auth/login request to obtain access and refresh tokens.
    """
    url = f"{BASE_URL}/auth/login"
    # Safeguard against 400 Bad Request by ensuring required device strings are not empty/None
    if not device_token:
        device_token = "SAMPLE_FCM_DEVICE_TOKEN_STRING"
    if not device_model_name:
        device_model_name = "Python Script Client"

    payload = {
        "username": username,
        "password": password,
        "device_token": device_token,
        "device_model_name": device_model_name,
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in (200, 201):
        return response.json()  # Contains access_token, refresh_token, etc.
    else:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")


def get_device_token(refresh_token, device_token_value, device_model):
    """
    Simulates the POST /auth/token endpoint to register/refresh device tokens.
    """
    url = f"{BASE_URL}/auth/token"
    if not device_token_value:
        device_token_value = "SAMPLE_FCM_DEVICE_TOKEN_STRING"
    if not device_model:
        device_model = "Python Script Client"

    payload = {
        "refresh_token": refresh_token,
        "device_token": device_token_value,
        "device_model_name": device_model,
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in (200, 201):
        res_json = response.json()
        # Tokens are nested inside the "result" dictionary in this response
        return res_json.get("result") or res_json
    else:
        raise Exception(
            f"Failed to refresh/set device token: {response.status_code} - {response.text}"
        )


def get_user_household_info(access_token):
    """
    Retrieves the household registry information which contains aptCode, dong, and ho.
    """
    url = f"{BASE_URL}/auth/household"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code in (200, 201):
        return response.json()  # Returns household information list/object
    else:
        raise Exception(
            f"Failed to get household details: {response.status_code} - {response.text}"
        )


# --- Example Execution Flow ---
if __name__ == "__main__":
    # Input credentials
    USER_ID = "YOUR_USER_ID"
    USER_PW = "YOUR_PASSWORD"

    try:
        # Step 1: Log in to get tokens
        print("Logging in...")
        dummy_fcm_token = "SAMPLE_FCM_DEVICE_TOKEN_STRING"
        auth_data = get_auth_token(
            USER_ID, USER_PW, dummy_fcm_token, "Python Script Client"
        )

        access_token = auth_data.get("access_token")
        refresh_token = auth_data.get("refresh_token")

        print("Login successful.")
        print(f"Access Token: {access_token[:20]}...")
        print(f"Refresh Token: {refresh_token[:20]}...")

        # Step 2: Retrieve device token and household details directly from login response
        # The login response already contains the last selected household details!
        last_house = auth_data.get("last_selected_household") or {}
        apt_code = last_house.get("last_selected_apt_code")
        dong = last_house.get("last_selected_dong_no")
        ho = last_house.get("last_selected_ho_no")

        # Check registered device tokens under otherLogin, fallback to dummy if none
        other_logins = auth_data.get("otherLogin") or []
        registered_tokens = [
            item.get("device_token")
            for item in other_logins
            if item.get("device_token")
        ]
        device_token = registered_tokens[0] if registered_tokens else dummy_fcm_token

        # Note: If needed, we can also refresh the token:
        # device_info = get_device_token(refresh_token, dummy_fcm_token, "Python Script Client")

        print("\n--- Retrieved Information ---")
        print(f"Apartment Code (aptcode) : {apt_code}")
        print(f"Dong                     : {dong}")
        print(f"Ho                       : {ho}")
        print(f"Device Token             : {device_token}")
        print(f"Access Token             : {access_token}")
        print(f"Refresh Token            : {refresh_token}")

    except Exception as e:
        print(f"Error occurred: {e}")
