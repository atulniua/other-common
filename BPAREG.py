import pandas as pd
import requests
import json
import time

# URLs from curl
USER_API_URL = "http://localhost:8092/user/users/_createnovalidate"
BPAREG_CREATE_URL = "http://localhost:8282/tl-services/v1/BPAREG/_create"
BPAREG_UPDATE_URL = "http://localhost:8282/tl-services/v1/BPAREG/_update"
AUTH_TOKEN = "8e9458b6-9a31-415d-b574-fe8459be1c03"
TENANT_ID = "pg"

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json;charset=UTF-8",
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "origin": "https://niuatt.niua.in",
    "referer": "https://niuatt.niua.in/digit-ui/citizen/obps/stakeholder/apply/acknowledgement",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
})

def create_user(name, mobile):
    payload = {
        "requestInfo": {
            "apiId": "Rainmaker",
            "authToken": AUTH_TOKEN,
            "userInfo": {
                "id": 4094,
                "uuid": "5ab861f6-e258-4759-830a-47209c606e88",
                "userName": "7889165771",
                "name": "Atul",
                "mobileNumber": "7889165771",
                "type": "EMPLOYEE",
                "roles": [{"name": "superuser", "code": "SUPERUSER", "tenantId": TENANT_ID}],
                "tenantId": TENANT_ID
            },
            "msgId": f"{int(time.time())}|en_IN"
        },
        "user": {
            "userName": mobile,
            "name": name,
            "mobileNumber": mobile,
            "type": "CITIZEN",
            "active": True,
            "password": "eGov@123",
            "roles": [{"code": "CITIZEN", "name": "Citizen", "tenantId": TENANT_ID}],
            "tenantId": TENANT_ID
        }
    }
    
    try:
        response = session.post(USER_API_URL, json=payload)
        if response.status_code == 200:
            user_data = response.json().get('user', [{}])[0]
            return (True, user_data.get('uuid'), f"User created: {name} ({mobile})")
        else:
            if "DuplicateUserNameException" in response.text:
                import random
                new_mobile = "9" + str(random.randint(100000000, 999999999))
                return create_user(name, new_mobile)
            return (False, None, f"User failed: {response.status_code}")
    except Exception as e:
        return (False, None, f"User error: {e}")

def create_bpareg_step1(name, mobile, email, gender, address, pan, trade_type, council_no, user_uuid):
    payload = {
        "Licenses": [{
            "tradeLicenseDetail": {
                "owners": [{
                    "gender": gender or "MALE",
                    "mobileNumber": mobile,
                    "name": name,
                    "emailId": email or "",
                    "permanentAddress": address or "",
                    "correspondenceAddress": address or "",
                    "pan": pan or ""
                }],
                "subOwnerShipCategory": "INDIVIDUAL",
                "tradeUnits": [{"tradeType": trade_type or "ARCHITECT.CLASSA"}],
                "additionalDetail": {"counsilForArchNo": council_no or ""},
                "address": {"city": "", "landmark": "", "pincode": ""},
                "applicationDocuments": []
            },
            "licenseType": "PERMANENT",
            "businessService": "BPAREG",
            "tenantId": TENANT_ID,
            "action": "NOWORKFLOW"
        }],
        "RequestInfo": {
            "apiId": "Rainmaker",
            "authToken": AUTH_TOKEN,
            "userInfo": {
                "id": 4176,
                "uuid": user_uuid,
                "userName": mobile,
                "name": name,
                "mobileNumber": mobile,
                "type": "CITIZEN",
                "roles": [{"name": "Citizen", "code": "CITIZEN", "tenantId": TENANT_ID}],
                "active": True,
                "tenantId": TENANT_ID
            },
            "msgId": f"{int(time.time() * 1000)}|en_IN"
        }
    }
    
    try:
        response = session.post(BPAREG_CREATE_URL, json=payload)
        if response.status_code == 200:
            license_data = response.json().get('Licenses', [{}])[0]
            return license_data, f"BPAREG Step1: {name}"
        else:
            return None, f"Step1 failed: {response.status_code}"
    except Exception as e:
        return None, f"Step1 error: {e}"

def update_bpareg_step2(license_data, name, mobile, user_uuid):
    license_data["action"] = "APPLY"
    
    docs = [
        {"fileStoreId": "fa7a4eac-d970-411c-862b-fec27a185992", "fileStore": "fa7a4eac-d970-411c-862b-fec27a185992", "fileName": f"{name}.pdf", "fileUrl": "", "documentType": "APPL.BPAREG_GOVT_APPROVED_ID_CARD", "tenantId": TENANT_ID},
        {"fileStoreId": "8eccbf3c-b0f1-4d17-81b8-b5a6a60eda2c", "fileStore": "8eccbf3c-b0f1-4d17-81b8-b5a6a60eda2c", "fileName": f"{name}.pdf", "fileUrl": "", "documentType": "APPL.BPAREG_EDC_CERTIFICATE", "tenantId": TENANT_ID},
        {"fileStoreId": "663cffed-2b9f-4e0a-8bc7-c1a23bd812cc", "fileStore": "663cffed-2b9f-4e0a-8bc7-c1a23bd812cc", "fileName": f"{name}.pdf", "fileUrl": "", "documentType": "APPL.BPAREG_EXP_CERTIFICATE", "tenantId": TENANT_ID},
        {"fileStoreId": "e0c1df66-829f-49c4-8708-c1163cf597d4", "fileStore": "e0c1df66-829f-49c4-8708-c1163cf597d4", "fileName": f"{name}.pdf", "fileUrl": "", "documentType": "APPL.BPAREG_PASS_PORT_SIZE_PHOTO", "tenantId": TENANT_ID},
        {"fileStoreId": "59e10748-2c54-4013-ab26-aa67c5dbc1ba", "fileStore": "59e10748-2c54-4013-ab26-aa67c5dbc1ba", "fileName": f"{name}.pdf", "fileUrl": "", "documentType": "APPL.BPAREG_REGISTRATION_CERTIFICATE", "tenantId": TENANT_ID}
    ]
    
    license_data["tradeLicenseDetail"]["applicationDocuments"] = docs
    
    payload = {
        "Licenses": [license_data],
        "RequestInfo": {
            "apiId": "Rainmaker",
            "authToken": AUTH_TOKEN,
            "userInfo": {
                "id": 4176,
                "uuid": user_uuid,
                "userName": mobile,
                "name": name,
                "mobileNumber": mobile,
                "type": "CITIZEN",
                "roles": [{"name": "Citizen", "code": "CITIZEN", "tenantId": TENANT_ID}],
                "active": True,
                "tenantId": TENANT_ID
            },
            "msgId": f"{int(time.time() * 1000)}|en_IN",
            "plainAccessRequest": {}
        }
    }
    
    try:
        response = session.post(BPAREG_UPDATE_URL, json=payload)
        if response.status_code == 200:
            app_no = license_data.get('applicationNumber')
            return (True, f"BPAREG completed: {name} => {app_no}")
        else:
            return (False, f"Update failed: {response.status_code}")
    except Exception as e:
        return (False, f"Update error: {e}")

def create_bpareg(name, mobile, email, gender, address, pan, trade_type, council_no, user_uuid):
    license_data, step1_msg = create_bpareg_step1(name, mobile, email, gender, address, pan, trade_type, council_no, user_uuid)
    print(step1_msg)
    
    if license_data:
        time.sleep(1)
        return update_bpareg_step2(license_data, name, mobile, user_uuid)
    else:
        return (False, f"BPAREG failed at step1: {name}")

def process_record(name, mobile, email, gender, address, pan, trade_type, council_no, fees):
    user_success, user_uuid, user_msg = create_user(name, mobile)
    print(user_msg)
    
    if not user_success or not user_uuid:
        return (False, f"Failed user: {name}")
    
    actual_mobile = user_msg.split('(')[1].split(')')[0] if '(' in user_msg else mobile
    
    bpareg_success, bpareg_msg = create_bpareg(name, actual_mobile, email, gender, address, pan, trade_type, council_no, user_uuid)
    print(bpareg_msg)
    
    return (bpareg_success, f"Complete: {name}")

def migrate_users_and_bpareg():
    try:
        df = pd.read_excel("/Users/atul/Documents/BPAREG.xlsx", sheet_name="Sheet1")
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    success, fail = 0, 0
    for _, row in df.iterrows():
        if str(row["name"]).strip() and str(row["mobile"]).strip():
            name = str(row["name"]).strip()
            mobile = str(row["mobile"]).strip()
            email = str(row.get("email", "")).strip() if pd.notna(row.get("email")) else ""
            gender = str(row.get("gender", "MALE")).strip().upper() if pd.notna(row.get("gender")) else "MALE"
            address = str(row.get("address", "")).strip() if pd.notna(row.get("address")) else ""
            pan = str(row.get("pan", "")).strip() if pd.notna(row.get("pan")) else ""
            trade_type = str(row.get("trade_type", "ARCHITECT.CLASSA")).strip() if pd.notna(row.get("trade_type")) else "ARCHITECT.CLASSA"
            council_no = str(row.get("council_no", "")).strip() if pd.notna(row.get("council_no")) else ""
            fees = int(row.get("fees", 500)) if pd.notna(row.get("fees")) else 500
            
            ok, message = process_record(name, mobile, email, gender, address, pan, trade_type, council_no, fees)
            if ok:
                success += 1
            else:
                fail += 1

    print(f"\n✅ Migration Complete — Success: {success}, Failures: {fail}")

if __name__ == "__main__":
    migrate_users_and_bpareg()