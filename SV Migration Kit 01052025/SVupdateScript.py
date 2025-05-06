import pandas as pd
import requests
import time
import logging
import sqlite3
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, # Keep DEBUG for detailed logs during development
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_debug.log'),
        logging.StreamHandler()
    ]
)

# Configuration
# IMPORTANT: Update these paths and URLs as needed
EXCEL_PATH = "/Users/atul/Desktop/migrate.xlsx" # <-- Verify this path
DB_PATH = "migration.db"
CREATE_API = "http://localhost:8022/sv-services/street-vending/_create" # <-- Verify this URL
UPDATE_API = "http://localhost:8022/sv-services/street-vending/_update" # <-- Verify this URL

# IMPORTANT: Define the Authorization Bearer token here
# Use the token that works for both create (as Citizen) and update (as Employee)
AUTH_TOKEN = "a00d5ebb-9559-404f-a0ef-aadc3019510c" # <-- Use the provided token

# IMPORTANT: Use the exact user details from your successful API calls

# User details for the RequestInfo in the update call (Employee User)
UPDATE_REQUEST_USER_INFO = {
    "id": 832,
    "uuid": "7f4fd980-628e-4266-a992-40fa629e2f05",
    "userName": "SVEMP",
    "name": "SV",
    "mobileNumber": "9509935418",
    "emailId": None,
    "locale": None,
    "type": "EMPLOYEE",
    "roles": [
      {
        "name": "Inspection Officer",
        "code": "INSPECTIONOFFICER",
        "tenantId": "pg.citya"
      },
      {
        "name": "TVC Employee",
        "code": "TVCEMPLOYEE",
        "tenantId": "pg.citya"
      },
      {
        "name": "SV CEMP ",
        "code": "SVCEMP",
        "tenantId": "pg.citya"
      }
    ],
    "active": True,
    "tenantId": "pg.citya", # Ensure this matches your tenant
    "permanentCity": None
}

# User details for the RequestInfo in the create call (Citizen User)
CREATE_REQUEST_USER_INFO = {
    "id": 790,
    "uuid": "7e1ebe9e-d040-413f-896a-5460def381e9",
    "userName": "9999009999",
    "name": "Shivank",
    "mobileNumber": "9999009999",
    "emailId": None,
    "locale": None,
    "type": "CITIZEN",
    "roles": [
        {
            "name": "Citizen",
            "code": "CITIZEN",
            "tenantId": "pg" # Note: Tenant ID is "pg" for the citizen user
        }
    ],
    "active": True,
    "tenantId": "pg", # Ensure this matches your tenant
    "permanentCity": None
}

# Define common headers. Add more headers if needed based on UI network traffic analysis.
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {AUTH_TOKEN}",
    # Potentially add other headers observed in successful UI calls if the fix below isn't enough:
    # "Origin": "http://localhost:3000", # Example: if UI is on port 3000
    # "Referer": "http://localhost:3000/some-page", # Example: specific page
    # "User-Agent": "Mozilla/5.0...", # Example: Mimic a browser
    # "Accept-Language": "en-US,en;q=0.9", # Example: Language preference
    # "Accept-Encoding": "gzip, deflate, br", # Example: Encoding preference
    # "Connection": "keep-alive", # Example: Connection type
}


def init_db():
    """Initialize database with correct schema"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Drop existing table if it exists
            conn.execute('DROP TABLE IF EXISTS migration_log')
            # Create new table with correct schema
            conn.execute('''
                CREATE TABLE migration_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor_name TEXT,
                    mobile_no TEXT,
                    create_status TEXT,
                    update_status TEXT,
                    application_id TEXT,
                    application_no TEXT,
                    error TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            logging.info("Database initialized with fresh schema")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        raise # Re-raise the exception to stop execution if DB is critical


def log_to_db(vendor_name, mobile_no, create_status, update_status="", application_id="", application_no="", error=None):
    """Log migration attempt with proper column names"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO migration_log
                (vendor_name, mobile_no, create_status, update_status, application_id, application_no, error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(vendor_name), str(mobile_no), str(create_status), str(update_status),
                  str(application_id), str(application_no), str(error) if error is not None else None))
            conn.commit()
    except Exception as db_err:
        logging.error(f"Failed to log to database for {vendor_name}/{mobile_no}: {db_err}")


def create_base_payload(record):
    """Create payload matching the exact API requirements for the _create endpoint"""
    current_timestamp = int(time.time() * 1000)
    payload = {
        "streetVendingDetail": {
            # These lists/objects will be populated from the Excel record
            "addressDetails": [],
            "bankDetail": {},
            "documentDetails": [],
            "vendingOperationTimeDetails": [],
            "vendorDetail": [],
            "benificiaryOfSocialSchemes": [], # New field

            # Fields populated from Excel record
            "disabilityStatus": str(record.get('disabilityStatus', 'NONE')),
            "draftId": str(record.get('draftId', '')),
            "localAuthorityName": str(record.get('localAuthorityName', '')),
            "vendingActivity": str(record.get('vendingActivity', 'STATIONARY')), # Mapped from Excel
            "vendingArea": str(record.get('vendingArea', '100')), # Map from Excel
            "vendingZone": str(record.get('vendingZone', 'TEST_VALUE_ONE')), # Mapped from Excel
            "enrollmentId": str(record.get('enrollmentId', '')), # Map from Excel
            "locality": str(record.get('vendingLocality', '')), # New field, map from Excel
            "applicationCreatedBy": str(record.get('applicationCreatedBy', 'citizen')).upper(), # Map from Excel, default citizen, ensure uppercase if API expects it

            # Fields expected to be generated by API or set initially
            "applicationDate": current_timestamp,
            "applicationId": None,
            "applicationNo": None,
            "oldApplicationNo": None,
            "applicationStatus": "APPLIED", # Initial status for a new application
            "approvalDate": "0",
            "certificateNo": None,
            "cartLatitude": float(str(record.get('cartLatitude', 0)).strip()), # Map from Excel, ensure float
            "cartLongitude": float(str(record.get('cartLongitude', 0)).strip()), # Map from Excel, ensure float
            "vendingLicenseCertificateId": "",
            "paymentReceiptId": None,
            "vendingLicenseId": None,
            "validityDate": None,
            "validityDateForPersisterDate": None,
            "expireFlag": False,
            "renewalStatus": None,
            "issuedDate": None,
            "financialYear": str(record.get('financialYear', '')), # Map from Excel
            "validFrom": str(record.get('validFrom', 'NA')),
            "validTo": str(record.get('validTo', 'NA')),
            "tradeLicenseNo": str(record.get('tradeLicenseNo', '')),

            # Audit details for the main object - initialize as empty or None for API to populate
            "auditDetails": None,

             # Terms and Condition - Map from Excel or hardcode
            "termsAndCondition": str(record.get('termsAndCondition', 'Y')),

            # Workflow for the initial APPLY action
            "workflow": {
                "action": "APPLY",
                "comments": "Created via migration script",
                "businessService": "street-vending",
                "moduleName": "sv-services",
                "varificationDocuments": []
            },
             # Tenant ID
            "tenantId": "pg.citya" # Ensure this matches your tenant
        },
        "draftApplication": False,
        "RequestInfo": {
            "apiId": "Rainmaker",
            "authToken": AUTH_TOKEN,
            "userInfo": CREATE_REQUEST_USER_INFO,
            "msgId": f"{int(time.time()*1000)}|en_IN", # Generate a unique msgId
            "plainAccessRequest": {}
        }
    }

    # --- Map data from Excel record into the lists/objects ---
    # Use .get() with default values to handle missing columns gracefully

    # Address Details (Assuming PERMANENT and CORRESPONDENCE addresses are required and potentially the same)
    address_types = ["PERMANENT", "CORRESPONDENCE"]
    is_address_same = str(record.get('isAddressSame', '')).lower() == 'true'

    for i, addr_type in enumerate(address_types):
         prefix = 'corr' if addr_type == 'CORRESPONDENCE' and not is_address_same else ''
         if addr_type == 'CORRESPONDENCE' and is_address_same:
             address_data = {
                "addressId": None,
                "addressLine1": str(record.get('addressLine1', '')),
                "addressLine2": str(record.get('addressLine2', '')),
                "addressType": addr_type,
                "city": str(record.get('city', 'New Delhi')),
                "cityCode": str(record.get('cityCode', 'pg.citya')),
                "doorNo": str(record.get('doorNo', '')),
                "houseNo": str(record.get('houseNo', '')),
                "landmark": str(record.get('landmark', '')),
                "locality": str(record.get('locality', '')),
                "localityCode": str(record.get('localityCode', '')),
                "pincode": str(record.get('pincode', '')),
                "streetName": str(record.get('streetName', '')),
                "vendorId": None,
                "isAddressSame": True,
                "auditDetails": None
             }
         else:
            address_data = {
                "addressId": None,
                "addressLine1": str(record.get(f'{prefix}addressLine1', '')),
                "addressLine2": str(record.get(f'{prefix}addressLine2', '')),
                "addressType": addr_type,
                "city": str(record.get(f'{prefix}city', 'New Delhi')),
                "cityCode": str(record.get(f'{prefix}cityCode', 'pg.citya')),
                "doorNo": str(record.get(f'{prefix}doorNo', '')),
                "houseNo": str(record.get(f'{prefix}houseNo', '')),
                "landmark": str(record.get(f'{prefix}landmark', '')),
                "locality": str(record.get(f'{prefix}locality', '')),
                "localityCode": str(record.get(f'{prefix}localityCode', '')),
                "pincode": str(record.get(f'{prefix}pincode', '')),
                "streetName": str(record.get(f'{prefix}streetName', '')),
                "vendorId": None,
                "isAddressSame": is_address_same if addr_type == 'CORRESPONDENCE' else False,
                 "auditDetails": None
            }
         if address_data.get('pincode') or address_data.get('localityCode') or address_data.get('houseNo'):
              payload['streetVendingDetail']['addressDetails'].append(address_data)


    # Bank Details - Only add if account number is provided
    if str(record.get('accountNumber', '')).strip():
        payload['streetVendingDetail']['bankDetail'] = {
            "accountHolderName": str(record.get('accountHolderName', '')),
            "accountNumber": str(record.get('accountNumber', '')),
            "bankBranchName": str(record.get('bankBranchName', '')),
            "bankName": str(record.get('bankName', '')),
            "ifscCode": str(record.get('ifscCode', '')),
            "applicationId": None,
            "id": None,
            "refundStatus": None,
            "refundType": None,
            "auditDetails": None
        }

    # Vendor Details
    vendor_main = {
        "applicationId": None,
        "auditDetails": None,
        "dob": str(record.get('dob_vendor', '2000-01-01')),
        "userCategory": str(record.get('userCategory', 'GEN')),
        "emailId": str(record.get('email', '')),
        "fatherName": str(record.get('fatherName', '')),
        "specialCategory": str(record.get('specialCategory_vendor', 'NONE')),
        "gender": str(record.get('gender', 'M')),
        "id": None,
        "isInvolved": str(record.get('isVendorInvolved', 'True')).lower() == 'true', # Explicitly check for vendor involved
        "mobileNo": str(record.get('mobileNo', '')),
        "name": str(record.get('name', '')),
        "relationshipType": "VENDOR",
        "vendorId": None,
        "vendorPaymentFrequency": str(record.get('vendorPaymentFrequency', 'MONTHLY'))
    }
    if vendor_main.get('name') and vendor_main.get('mobileNo'):
        payload['streetVendingDetail']['vendorDetail'].append(vendor_main)
    else:
        logging.warning(f"Skipping main vendor for record {record.get('name')}/{record.get('mobileNo')} due to missing name or mobile.")


    spouse_name = str(record.get('spouseName', '')).strip()
    if spouse_name:
        vendor_spouse = {
            "applicationId": None,
            "auditDetails": None,
            "dob": str(record.get('dob_spouse', '2000-01-01')),
            "userCategory": str(record.get('userCategory_spouse', record.get('userCategory', 'GEN'))),
            "emailId": str(record.get('email_spouse', '')),
            "specialCategory": str(record.get('specialCategory_spouse', 'NONE')),
            "isInvolved": str(record.get('isSpouseInvolved', 'True')).lower() == 'true',
            "fatherName": str(record.get('fatherName_spouse', '')),
            "gender": str(record.get('gender_spouse', 'O')),
            "id": None,
            "mobileNo": str(record.get('mobileNo_spouse', '')),
            "name": spouse_name,
            "relationshipType": "SPOUSE",
            "vendorId": None,
            "vendorPaymentFrequency": None
        }
        payload['streetVendingDetail']['vendorDetail'].append(vendor_spouse)

    dependent_name = str(record.get('dependentName', '')).strip()
    if dependent_name:
        vendor_dependent = {
            "applicationId": None,
            "auditDetails": None,
            "dob": str(record.get('dob_dependent', '2000-01-01')),
            "userCategory": str(record.get('userCategory_dependent', record.get('userCategory', 'GEN'))),
            "emailId": str(record.get('email_dependent', '')),
            "specialCategory": str(record.get('specialCategory_dependent', 'NONE')),
            "isInvolved": str(record.get('isDependentInvolved', 'True')).lower() == 'true',
            "fatherName": str(record.get('fatherName_dependent', '')),
            "gender": str(record.get('gender_dependent', 'M')),
            "id": None,
            "mobileNo": str(record.get('mobileNo_dependent', '')),
            "name": dependent_name,
            "relationshipType": "DEPENDENT",
            "vendorId": None,
            "vendorPaymentFrequency": None
        }
        payload['streetVendingDetail']['vendorDetail'].append(vendor_dependent)


    # Document Details
    document_types_map = {
        'photoFileStoreId': "FAMILY.PHOTO.PHOTOGRAPH",
        'voterIdFileStoreId': "PROOF.RESIDENCE.VOTERID",
        'setupPhotoFileStoreId': "PHOTOGRAPH.VENDINGSETUP.PHOTO",
        'aadhaarFileStoreId': "IDENTITYPROOF.AADHAAR",
        # Add other document types and their corresponding Excel column names here
    }

    for col_name, doc_type in document_types_map.items():
        file_store_id = str(record.get(col_name, '')).strip()
        if file_store_id:
            payload['streetVendingDetail']['documentDetails'].append({
                "applicationId": None,
                "documentType": doc_type,
                "fileStoreId": file_store_id,
                "documentDetailId": file_store_id, # As per your example
                "auditDetails": None
            })

    # Operation Times (all days)
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    start_time = str(record.get('operationStartTime', '08:00')).strip()
    end_time = str(record.get('operationEndTime', '20:00')).strip()
    if start_time and end_time and ':' in start_time and ':' in end_time:
        payload['streetVendingDetail']['vendingOperationTimeDetails'] = [
            {
                "applicationId": None,
                "auditDetails": None,
                "dayOfWeek": day,
                "fromTime": start_time,
                "toTime": end_time,
                "id": None
            } for day in days
        ]

    # Beneficiary of Social Schemes
    social_schemes = []
    for i in range(1, 5):
        scheme_name = str(record.get(f'socialScheme{i}Name', '')).strip()
        enrollment_id = str(record.get(f'socialScheme{i}EnrollmentId', '')).strip()

        if scheme_name and enrollment_id:
             try:
                 enrollment_id_val = int(enrollment_id)
             except ValueError:
                 enrollment_id_val = enrollment_id

             social_schemes.append({
                 "schemeName": scheme_name,
                 "enrollmentId": enrollment_id_val
             })
    if social_schemes:
         payload['streetVendingDetail']['benificiaryOfSocialSchemes'] = social_schemes


    try:
        vending_area_val = str(record.get('vendingArea', '0')).strip()
        payload['streetVendingDetail']['vendingArea'] = int(vending_area_val)
    except ValueError:
        logging.warning(f"Could not convert vendingArea '{record.get('vendingArea')}' to int for {record.get('name')}. Using default 0.")
        payload['streetVendingDetail']['vendingArea'] = 0


    return payload

def create_update_payload(create_response_data):
    """
    Create update payload using the FULL create API response.
    Expects create_response_data to contain the "SVDetail" key.
    Removes 'status' and 'documents' from workflow object to match UI payload.
    """
    current_timestamp = int(time.time() * 1000)

    street_vending_detail = create_response_data.get('SVDetail')

    if not street_vending_detail or not isinstance(street_vending_detail, dict):
        logging.error("Could not extract SVDetail dictionary from create response for update payload creation.")
        return None

    # Create the update payload by modifying the object from the create response
    update_payload = {
        "streetVendingDetail": street_vending_detail,
        "RequestInfo": {
            "apiId": "Rainmaker",
            "authToken": AUTH_TOKEN,
            "userInfo": UPDATE_REQUEST_USER_INFO,
            "msgId": f"{int(time.time()*1000)}|en_IN", # Generate a new unique msgId for the update
            "plainAccessRequest": {}
        }
    }

    # --- Modify the object for the "APPROVE" action ---
    # Set status back to APPLIED for the transition - This might be necessary depending on API logic
    # If the API expects the current status to be APPLIED to transition to APPROVED, keep this line.
    # If the API determines the current status internally based on the application ID, this line might be unnecessary.
    # Let's keep it for now as it was in your failed payload.
    update_payload['streetVendingDetail']['applicationStatus'] = "APPLIED"

    # Update audit details for the main object
    if update_payload['streetVendingDetail'].get('auditDetails') is None:
         update_payload['streetVendingDetail']['auditDetails'] = {}

    update_payload['streetVendingDetail']['auditDetails']['lastModifiedBy'] = UPDATE_REQUEST_USER_INFO["uuid"]
    update_payload['streetVendingDetail']['auditDetails']['lastModifiedTime'] = current_timestamp

    # Update audit details for sub-objects
    sub_objects_to_audit = [
        update_payload['streetVendingDetail'].get('bankDetail')
    ]
    sub_lists_to_audit = [
        update_payload['streetVendingDetail'].get('addressDetails', []),
        update_payload['streetVendingDetail'].get('documentDetails', []),
        update_payload['streetVendingDetail'].get('vendorDetail', []),
        update_payload['streetVendingDetail'].get('vendingOperationTimeDetails', []),
        update_payload['streetVendingDetail'].get('benificiaryOfSocialSchemes', [])
    ]

    for item in sub_objects_to_audit:
        if isinstance(item, dict):
            if item.get('auditDetails') is None:
                item['auditDetails'] = {}
            item['auditDetails']['lastModifiedBy'] = UPDATE_REQUEST_USER_INFO["uuid"]
            item['auditDetails']['lastModifiedTime'] = current_timestamp

    for obj_list in sub_lists_to_audit:
        if isinstance(obj_list, list):
            for item in obj_list:
                if isinstance(item, dict):
                     if item.get('auditDetails') is None:
                         item['auditDetails'] = {}
                     item['auditDetails']['lastModifiedBy'] = UPDATE_REQUEST_USER_INFO["uuid"]
                     item['auditDetails']['lastModifiedTime'] = current_timestamp


    # Set the workflow action for approval
    # CRITICAL FIX: Remove 'status' and 'documents' fields to match the successful UI payload
    update_payload['streetVendingDetail']['workflow'] = {
        "action": "APPROVE",
        "comments": "Auto-approved by migration script",
        "businessService": "street-vending",
        "moduleName": "sv-services",
        "assignes": None,
        "varificationDocuments": [] # Keeping this as it was in the UI payload
    }

    # Ensure vendingArea is an integer
    try:
        vending_area_val = update_payload['streetVendingDetail'].get('vendingArea')
        update_payload['streetVendingDetail']['vendingArea'] = int(str(vending_area_val).strip())
    except (ValueError, TypeError):
        logging.warning(f"Could not convert vendingArea '{vending_area_val}' to int during update payload creation. Using default 0.")
        update_payload['streetVendingDetail']['vendingArea'] = 0

    # Ensure latitude/longitude are floats
    try:
         update_payload['streetVendingDetail']['cartLatitude'] = float(str(update_payload['streetVendingDetail'].get('cartLatitude', 0)).strip())
    except ValueError:
         logging.warning(f"Could not convert cartLatitude '{update_payload['streetVendingDetail'].get('cartLatitude')}' to float during update payload creation. Using default 0.")
         update_payload['streetVendingDetail']['cartLatitude'] = 0.0
    try:
         update_payload['streetVendingDetail']['cartLongitude'] = float(str(update_payload['streetVendingDetail'].get('cartLongitude', 0)).strip())
    except ValueError:
         logging.warning(f"Could not convert cartLongitude '{update_payload['streetVendingDetail'].get('cartLongitude')}' to float during update payload creation. Using default 0.")
         update_payload['streetVendingDetail']['cartLongitude'] = 0.0


    return update_payload

def process_excel():
    """Main processing function"""
    try:
        df = pd.read_excel(EXCEL_PATH, dtype=str)
        if df.empty:
            logging.info("Excel file is empty. No records to process.")
            return
        df = df.fillna('')
    except FileNotFoundError:
        logging.critical(f"Excel file not found at {EXCEL_PATH}")
        return
    except Exception as e:
        logging.critical(f"Error reading Excel file: {e}")
        return

    init_db()

    for index, record_series in df.iterrows():
        record = record_series.to_dict()

        name = record.get('name', f'Unnamed Vendor {index + 1}')
        mobile = record.get('mobileNo', f'No Mobile {index + 1}')

        logging.info(f"Processing record {index + 1}: {name} ({mobile})")

        application_id = ""
        application_no = ""
        create_status = "NOT_ATTEMPTED"
        update_status = "NOT_ATTEMPTED"
        error_message = None
        create_response_data = None
        sv_detail = None

        main_vendor_name = str(record.get('name', '')).strip()
        main_vendor_mobile = str(record.get('mobileNo', '')).strip()
        if not main_vendor_name or not main_vendor_mobile:
            create_status = "SKIPPED_MISSING_VENDOR_INFO"
            error_message = "Skipped due to missing main vendor name or mobile number in Excel."
            logging.warning(f"Skipping record {index + 1} ({name}/{mobile}): {error_message}")
            log_to_db(name, mobile, create_status, update_status="NOT_ATTEMPTED", error=error_message)
            continue

        try:
            # Step 1: Create application
            create_payload = create_base_payload(record)

            logging.debug(f"Record {index + 1} - Create Payload:\n{json.dumps(create_payload, indent=2)}")

            try:
                create_response = requests.post(
                    CREATE_API,
                    headers=HEADERS, # Use the defined HEADERS
                    json=create_payload,
                    timeout=60
                )
                create_response.raise_for_status()
                create_response_data = create_response.json()

                logging.debug(f"Record {index + 1} - Create Response Data:\n{json.dumps(create_response_data, indent=2)}")

                sv_detail = create_response_data.get("SVDetail")

                if sv_detail and isinstance(sv_detail, dict):
                    application_id = sv_detail.get('applicationId', '')
                    application_no = sv_detail.get('applicationNo', '')

                    if application_id and application_no:
                        create_status = "CREATE_SUCCESS"
                        logging.info(f"Create Success: {name} | Mobile: {mobile} | AppID: {application_id} | AppNo: {application_no}")
                    else:
                        create_status = "CREATE_SUCCESS_NO_ID"
                        error_message = "Create API success, but application ID or No missing in SVDetail object."
                        logging.error(f"{error_message} for {name} | Mobile: {mobile}")
                        log_to_db(name, mobile, create_status, update_status="NOT_ATTEMPTED", application_id=application_id, application_no=application_no, error=error_message)
                        continue
                else:
                    create_status = "CREATE_SUCCESS_NO_SVDETAIL"
                    error_message = "Create API success, but SVDetail object missing or not a dictionary in response."
                    logging.error(f"{error_message} for {name} | Mobile: {mobile}")
                    log_to_db(name, mobile, create_status, update_status="NOT_ATTEMPTED", error=error_message)
                    continue

            except requests.exceptions.Timeout:
                 create_status = "CREATE_TIMEOUT"
                 error_message = "Create API request timed out."
                 logging.error(f"{create_status} for {name} | Mobile: {mobile}: {error_message}")
                 log_to_db(name, mobile, create_status, update_status="NOT_ATTEMPTED", error=error_message)
                 continue

            except requests.exceptions.RequestException as e:
                create_status = "CREATE_FAILED"
                error_message = f"Create API Request Error: {str(e)}"
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_response_text = e.response.text
                        error_message += f" | Response: {error_response_text}"
                        logging.error(f"Create Failure Details: {error_response_text}")
                    except:
                        error_message += " | Could not parse error response text."
                logging.error(f"{create_status} for {name} | Mobile: {mobile}: {error_message}")
                log_to_db(name, mobile, create_status, update_status="NOT_ATTEMPTED", error=error_message)
                continue

            except json.JSONDecodeError:
                 create_status = "CREATE_SUCCESS_INVALID_JSON"
                 error_message = "Create API success, but response is not valid JSON."
                 logging.error(f"{create_status} for {name} | Mobile: {mobile}: {error_message}")
                 log_to_db(name, mobile, create_status, update_status="NOT_ATTEMPTED", error=error_message)
                 continue


            # Step 2: Update application (approve)
            if create_status == "CREATE_SUCCESS" and application_id and application_no and sv_detail:
                # Add a small delay to ensure backend has processed the create request
                time.sleep(2)

                update_payload = create_update_payload({"SVDetail": sv_detail})

                if update_payload is None:
                    update_status = "UPDATE_PAYLOAD_ERROR"
                    error_message = "Failed to create update payload from create response."
                    logging.error(f"{update_status} for {name} | Mobile: {mobile}: {error_message}")
                    log_to_db(name, mobile, create_status, update_status, application_id, application_no, error_message)
                    continue

                logging.debug(f"Record {index + 1} - Update Payload:\n{json.dumps(update_payload, indent=2)}")

                try:
                    update_response = requests.post(
                        UPDATE_API,
                        headers=HEADERS, # Use the defined HEADERS
                        json=update_payload,
                        timeout=60
                    )
                    update_response.raise_for_status()
                    update_response_data = update_response.json()

                    logging.debug(f"Record {index + 1} - Update Response:\n{json.dumps(update_response_data, indent=2)}")

                    update_status = "UPDATE_SUCCESS"
                    logging.info(f"Update Success: {name} | Mobile: {mobile} | AppID: {application_id} | AppNo: {application_no}")

                except requests.exceptions.Timeout:
                    update_status = "UPDATE_TIMEOUT"
                    error_message = "Update API request timed out."
                    logging.error(f"{update_status} for {name} | Mobile: {mobile}: {error_message}")

                except requests.exceptions.RequestException as e:
                    update_status = "UPDATE_FAILED"
                    error_message = f"Update API Request Error: {str(e)}"
                    if hasattr(e, 'response') and e.response is not None:
                        try:
                             error_response_text = e.response.text
                             error_message += f" | Response: {error_response_text}"
                             logging.error(f"Update Failure Details: {error_response_text}")
                        except:
                            error_message += " | Could not parse error response text."
                    logging.error(f"{update_status} for {name} | Mobile: {mobile}: {error_message}")

                except json.JSONDecodeError:
                     update_status = "UPDATE_SUCCESS_INVALID_JSON"
                     error_message = "Update API success, but response is not valid JSON."
                     logging.error(f"{update_status} for {name} | Mobile: {mobile}: {error_message}")


            log_to_db(name, mobile, create_status, update_status, application_id, application_no, error_message)

        except Exception as e:
            error_message = f"Unexpected Processing Error: {str(e)}"
            logging.error(f"Failed processing {name} | Mobile: {mobile}: {error_message}", exc_info=True)
            log_to_db(name, mobile, create_status, update_status, application_id, application_no, error_message)

        # Add a small delay between records
        time.sleep(1)


def verify_api_connectivity(url):
    """Function to verify API connectivity by hitting a base URL"""
    try:
        # Attempt to hit a common base path or the endpoint itself
        test_url = url.rsplit('/', 1)[0] if '/_' in url else url # Try a slightly more general path if endpoint has _
        if not test_url.endswith('street-vending'): # Fallback to the provided URL if heuristic fails
             test_url = url

        response = requests.get(
            test_url,
            headers=HEADERS, # Use the defined HEADERS for the check
            timeout=10
        )
        logging.info(f"API connection test to {response.url}: Status {response.status_code}")
        # Consider 404 also as reachable if it's a valid API path
        if 200 <= response.status_code < 500 or response.status_code == 404:
             logging.info("API appears to be reachable and responding (status 404 might be expected for a base path).")
             return True
        else:
             logging.warning(f"API returned unexpected status {response.status_code}. It might be reachable but not configured as expected.")
             return False
    except requests.exceptions.ConnectionError:
        logging.error(f"API connection test failed: Could not connect to {url}")
        return False
    except requests.exceptions.Timeout:
         logging.error(f"API connection test failed: Request timed out to {url}")
         return False
    except Exception as e:
        logging.error(f"API connection test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("=== Street Vendor Migration ===")
    start = time.time()

    print("Verifying API connectivity...")
    # Verify connectivity using both URLs
    create_api_reachable = verify_api_connectivity(CREATE_API)
    update_api_reachable = verify_api_connectivity(UPDATE_API)

    api_reachable = create_api_reachable and update_api_reachable

    if not api_reachable:
        print("\nWARNING: Could not confirm API connectivity to both endpoints. Please check your network, the API server status, and the URLs in the script.")
        print("Also, ensure the AUTH_TOKEN in the script is correct and not expired.")
        proceed = input("Do you want to attempt the migration anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Migration canceled.")
            exit(1)
    else:
        print("API connectivity verified.")


    try:
        process_excel()
    except Exception as e:
        logging.critical(f"Fatal error during migration process: {str(e)}", exc_info=True)
    finally:
        end = time.time()
        print(f"\nCompleted in {end - start:.2f}s")
        print(f"Database log file: {DB_PATH}")
        print(f"Debug log file: migration_debug.log")

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT create_status, COUNT(*) FROM migration_log GROUP BY create_status")
                create_stats = cursor.fetchall()

                cursor.execute("SELECT update_status, COUNT(*) FROM migration_log WHERE update_status != 'NOT_ATTEMPTED' GROUP BY update_status")
                update_stats = cursor.fetchall()

                print("\nMigration Summary:")
                print("=================")
                print("Create API Statuses:")
                if create_stats:
                    for status, count in create_stats:
                        print(f"  {status}: {count}")
                else:
                    print("  No create attempts logged.")

                print("\nUpdate API Statuses:")
                if update_stats:
                    for status, count in update_stats:
                        print(f"  {status}: {count}")
                else:
                     print("  No update attempts logged.")

                cursor.execute("SELECT vendor_name, mobile_no, create_status, update_status, error FROM migration_log WHERE error IS NOT NULL")
                error_records = cursor.fetchall()
                if error_records:
                    print("\nRecords with Errors:")
                    print("====================")
                    for name, mobile, c_status, u_status, err in error_records:
                        print(f"- {name} ({mobile}) | Create: {c_status} | Update: {u_status} | Error: {err}")

        except Exception as e:
            print(f"\nCould not generate summary from database: {str(e)}")
