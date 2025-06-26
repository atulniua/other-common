import pandas as pd
import requests
import uuid
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants
EXCEL_FILE_PATH = "/Users/atul/Documents/SVMigrationKit01052025/Users.xlsx"
SHEET_NAME = "Sheet1"
API_URL = "http://localhost:8099/user/users/_createnovalidate"
AUTH_TOKEN = "9d78b340-4ebc-4c66-bff7-53a764b8263d"
ADMIN_USER_ID = 23287
ADMIN_UUID = "4632c941-cb1e-4b83-b2d4-200022c1a137"
ADMIN_USERNAME = "PalashS"
ADMIN_NAME = "Palash S"
DEFAULT_PASSWORD = "eGov@123"
TENANT_ID = "pg.citya"
MAX_WORKERS = 20  # Number of threads to run in parallel (tune this as needed)

# Reusable session
session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

def generate_request_info():
    return {
        "apiId": "Rainmaker",
        "ver": ".01",
        "ts": int(datetime.now().timestamp() * 1000),
        "action": "_update",
        "did": "1",
        "key": "",
        "msgId": str(int(datetime.now().timestamp())) + "|en_IN",
        "authToken": AUTH_TOKEN,
        "userInfo": {
            "id": ADMIN_USER_ID,
            "uuid": ADMIN_UUID,
            "userName": ADMIN_USERNAME,
            "name": ADMIN_NAME,
            "mobileNumber": "9949032246",
            "type": "EMPLOYEE",
            "roles": [
                {"name": "superuser", "code": "SUPERUSER", "tenantId": TENANT_ID},
                {"name": "HRMS Admin", "code": "HRMS_ADMIN", "tenantId": TENANT_ID},
                {"name": "superuser", "code": "SUPERUSER", "tenantId": "pg"}
            ],
            "tenantId": TENANT_ID
        }
    }

def create_user_payload(name, mobile_number):
    return {
        "userName": mobile_number,
        "name": name,
        "gender": None,
        "mobileNumber": mobile_number,
        "type": "CITIZEN",
        "active": True,
        "password": DEFAULT_PASSWORD,
        "roles": [{
            "code": "CITIZEN",
            "name": "Citizen",
            "tenantId": TENANT_ID
        }],
        "tenantId": TENANT_ID
    }

def send_user_creation_request(name, mobile_number):
    payload = {
        "requestInfo": generate_request_info(),
        "user": create_user_payload(name, mobile_number)
    }
    try:
        response = session.post(API_URL, data=json.dumps(payload))
        if response.status_code == 200:
            return (True, f"Success: {name} ({mobile_number})")
        else:
            return (False, f"Failed: {name} ({mobile_number}) => {response.status_code} - {response.text}")
    except Exception as e:
        return (False, f"Error: {name} ({mobile_number}) => {e}")

def migrate_users():
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name=SHEET_NAME)
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    if "name" not in df.columns or "mobile_number" not in df.columns:
        print("Excel file must contain 'name' and 'mobile_number' columns")
        return

    users = [(str(row["name"]).strip(), str(row["mobile_number"]).strip())
             for _, row in df.iterrows() if str(row["name"]).strip() and str(row["mobile_number"]).strip()]

    success, fail = 0, 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(send_user_creation_request, name, mobile) for name, mobile in users]
        for future in as_completed(futures):
            ok, message = future.result()
            print(message)
            if ok:
                success += 1
            else:
                fail += 1

    print(f"\n✅ Migration Complete — Success: {success}, Failures: {fail}")

if __name__ == "__main__":
    migrate_users()
