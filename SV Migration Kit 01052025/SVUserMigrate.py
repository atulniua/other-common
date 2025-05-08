import pandas as pd
import requests
import uuid
from datetime import datetime
import json

# Configuration
EXCEL_FILE_PATH = "/Users/atul/Documents/SVMigrationKit01052025/Users.xlsx"  # Path to your Excel file
SHEET_NAME = "Sheet1"           # Sheet name in Excel
API_URL = "http://localhost:8099/user/users/_createnovalidate"
AUTH_TOKEN = "9d78b340-4ebc-4c66-bff7-53a764b8263d"
ADMIN_USER_ID = 23287
ADMIN_UUID = "4632c941-cb1e-4b83-b2d4-200022c1a137"
ADMIN_USERNAME = "PalashS"
ADMIN_NAME = "Palash S"
DEFAULT_PASSWORD = "eGov@123"
TENANT_ID = "pg.citya"

def generate_request_info():
    """Generate the request info payload"""
    return {
        "apiId": "Rainmaker",
        "ver": ".01",
        "ts": int(datetime.now().timestamp() * 1000),  # current timestamp in milliseconds
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
            "emailId": None,
            "type": "EMPLOYEE",
            "roles": [
                {
                    "name": "superuser",
                    "code": "SUPERUSER",
                    "tenantId": TENANT_ID
                },
                {
                    "name": "HRMS Admin",
                    "code": "HRMS_ADMIN",
                    "tenantId": TENANT_ID
                },
                {
                    "name": "superuser",
                    "code": "SUPERUSER",
                    "tenantId": "pg"
                }
            ],
            "tenantId": TENANT_ID
        }
    }

def create_user_payload(name, mobile_number):
    """Create the user payload for the API"""
    return {
        "userName": mobile_number,
        "name": name,
        "gender": None,
        "mobileNumber": mobile_number,
        "type": "CITIZEN",
        "active": True,
        "password": DEFAULT_PASSWORD,
        "roles": [
            {
                "code": "CITIZEN",
                "name": "Citizen",
                "tenantId": TENANT_ID
            }
        ],
        "tenantId": TENANT_ID
    }

def migrate_users():
    # Read Excel file
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name=SHEET_NAME)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # Check required columns
    if "name" not in df.columns or "mobile_number" not in df.columns:
        print("Excel file must contain 'name' and 'mobile_number' columns")
        return
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json"
    }
    
    success_count = 0
    failure_count = 0
    
    for index, row in df.iterrows():
        name = str(row["name"]).strip()
        mobile_number = str(row["mobile_number"]).strip()
        
        # Skip empty rows
        if not name or not mobile_number:
            continue
            
        # Prepare payload
        payload = {
            "requestInfo": generate_request_info(),
            "user": create_user_payload(name, mobile_number)
        }
        
        try:
            # Make API request
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
            
            if response.status_code == 200:
                print(f"Successfully migrated user: {name} ({mobile_number})")
                success_count += 1
            else:
                print(f"Failed to migrate user {name} ({mobile_number}). Status code: {response.status_code}, Response: {response.text}")
                failure_count += 1
                
        except Exception as e:
            print(f"Error migrating user {name} ({mobile_number}): {e}")
            failure_count += 1
    
    print(f"\nMigration complete. Success: {success_count}, Failures: {failure_count}")

if __name__ == "__main__":
    migrate_users()