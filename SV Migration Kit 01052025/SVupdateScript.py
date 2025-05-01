import pandas as pd
import requests
import time
import logging
import sqlite3
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_debug.log'),
        logging.StreamHandler()
    ]
)

# Configuration
EXCEL_PATH = "/Users/atul/Downloads/street_vending_template_filled_output.xlsx"
DB_PATH = "migration.db"
CREATE_API = "http://localhost:8022/sv-services/street-vending/_create"
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": "Bearer 1337128f-f6d7-43e5-b751-7042d5baa083"
}

def init_db():
    """Initialize database with correct schema"""
    with sqlite3.connect(DB_PATH) as conn:
        # Drop existing table if it exists
        conn.execute('DROP TABLE IF EXISTS migration_log')
        # Create new table with correct schema
        conn.execute('''
            CREATE TABLE migration_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_name TEXT,
                mobile_no TEXT,
                status TEXT,
                error TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logging.info("Database initialized with fresh schema")

def log_to_db(vendor_name, mobile_no, status, error=None):
    """Log migration attempt with proper column names"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT INTO migration_log 
            (vendor_name, mobile_no, status, error)
            VALUES (?, ?, ?, ?)
        ''', (str(vendor_name), str(mobile_no), str(status), str(error)))
        conn.commit()

def create_base_payload():
    """Create payload matching the exact API requirements"""
    return {
        "streetVendingDetail": {
            "addressDetails": [],
            "applicationDate": 0,
            "applicationId": "",
            "applicationNo": "",
            "oldApplicationNo": None,
            "applicationStatus": "",
            "approvalDate": 0,
            "auditDetails": {
                "createdBy": "",
                "createdTime": 0,
                "lastModifiedBy": "",
                "lastModifiedTime": 0
            },
            "bankDetail": {
                "accountHolderName": "",
                "accountNumber": "",
                "applicationId": "",
                "bankBranchName": "",
                "bankName": "",
                "id": "",
                "ifscCode": "",
                "refundStatus": "",
                "refundType": "",
                "auditDetails": {
                    "createdBy": "",
                    "createdTime": 0,
                    "lastModifiedBy": "",
                    "lastModifiedTime": 0
                }
            },
            "benificiaryOfSocialSchemes": "",
            "enrollmentId": "",
            "cartLatitude": 0,
            "cartLongitude": 0,
            "certificateNo": None,
            "disabilityStatus": "NONE",
            "draftId": "",
            "documentDetails": [],
            "localAuthorityName": "",
            "tenantId": "pg.citya",
            "termsAndCondition": "Y",
            "tradeLicenseNo": "",
            "vendingActivity": "STATIONARY",
            "vendingArea": "100",
            "vendingLicenseCertificateId": "",
            "vendingOperationTimeDetails": [],
            "vendingZone": "TEST_VALUE_ONE",
            "vendorDetail": [],
            "workflow": {
                "action": "APPLY",
                "comments": "",
                "businessService": "street-vending",
                "moduleName": "sv-services",
                "varificationDocuments": []
            }
        },
        "draftApplication": False,
        "RequestInfo": {
            "apiId": "Rainmaker",
            "authToken": HEADERS['authorization'].split()[1],
            "userInfo": {
                "id": 808,
                "uuid": "38dd895e-95a0-4b72-946f-023a8a782c49",
                "userName": "7000000000",
                "name": "Nikhil",
                "mobileNumber": "7000000000",
                "emailId": None,
                "locale": None,
                "type": "CITIZEN",
                "roles": [
                    {
                        "name": "Citizen",
                        "code": "CITIZEN",
                        "tenantId": "pg"
                    }
                ],
                "active": True,
                "tenantId": "pg",
                "permanentCity": None
            },
            "msgId": f"{int(time.time()*1000)}|en_IN",
            "plainAccessRequest": {}
        }
    }

def map_excel_to_payload(record, payload):
    """Complete mapping of all fields from Excel"""
    # Address Details (2 addresses)
    payload['streetVendingDetail']['addressDetails'] = [
        {
            "addressId": "",
            "addressLine1": str(record.get('addressLine1', '')),
            "addressLine2": str(record.get('addressLine2', '')),
            "addressType": "",
            "city": str(record.get('city', 'New Delhi')),
            "cityCode": "pg.citya",
            "doorNo": "",
            "houseNo": str(record.get('houseNo', '')),
            "landmark": str(record.get('landmark', '')),
            "locality": str(record.get('locality', 'Main Road Abadpura')),
            "localityCode": str(record.get('localityCode', 'JLC476')),
            "pincode": str(record.get('pincode', '')),
            "streetName": "",
            "vendorId": ""
        },
        {
            "addressId": "",
            "addressLine1": str(record.get('addressLine1', '')),
            "addressLine2": str(record.get('addressLine2', '')),
            "addressType": "",
            "city": str(record.get('city', 'New Delhi')),
            "cityCode": "pg.citya",
            "doorNo": "",
            "houseNo": str(record.get('houseNo', '')),
            "landmark": str(record.get('landmark', '')),
            "locality": str(record.get('locality', 'Main Road Abadpura')),
            "localityCode": str(record.get('localityCode', 'JLC476')),
            "pincode": str(record.get('pincode', '')),
            "streetName": "",
            "vendorId": "",
            "isAddressSame": True
        }
    ]
    
    # Bank Details
    payload['streetVendingDetail']['bankDetail'].update({
        "accountHolderName": str(record.get('accountHolderName', '')),
        "accountNumber": str(record.get('accountNumber', '')),
        "bankBranchName": str(record.get('bankBranchName', '')),
        "bankName": str(record.get('bankName', '')),
        "ifscCode": str(record.get('ifscCode', ''))
    })
    
    # Vendor Details (3 vendors)
    payload['streetVendingDetail']['vendorDetail'] = [
        {
            "applicationId": "",
            "auditDetails": {
                "createdBy": "",
                "createdTime": 0,
                "lastModifiedBy": "",
                "lastModifiedTime": 0
            },
            "dob": str(record.get('dob_vendor', '2000-01-01')),
            "userCategory": str(record.get('userCategory', 'GEN')),
            "emailId": str(record.get('email', '')),
            "fatherName": str(record.get('fatherName', '')),
            "specialCategory": "NONE",
            "gender": str(record.get('gender', 'M')),
            "id": "",
            "isInvolved": True,
            "mobileNo": str(record.get('mobileNo', '')),
            "name": str(record.get('name', '')),
            "relationshipType": "VENDOR",
            "vendorId": None
        },
        {
            "applicationId": "",
            "auditDetails": {
                "createdBy": "",
                "createdTime": 0,
                "lastModifiedBy": "",
                "lastModifiedTime": 0
            },
            "dob": str(record.get('dob_spouse', '2000-01-01')),
            "userCategory": str(record.get('userCategory', 'GEN')),
            "emailId": "",
            "specialCategory": "NONE",
            "isInvolved": True,
            "fatherName": "",
            "gender": "O",
            "id": "",
            "mobileNo": "",
            "name": str(record.get('spouseName', '')),
            "relationshipType": "SPOUSE",
            "vendorId": None
        },
        {
            "applicationId": "",
            "auditDetails": {
                "createdBy": "",
                "createdTime": 0,
                "lastModifiedBy": "",
                "lastModifiedTime": 0
            },
            "dob": str(record.get('dob_dependent', '2000-01-01')),
            "userCategory": str(record.get('userCategory', 'GEN')),
            "emailId": "",
            "isInvolved": True,
            "specialCategory": "NONE",
            "fatherName": "",
            "gender": "M",
            "id": "",
            "mobileNo": "",
            "name": str(record.get('dependentName', '')),
            "relationshipType": "DEPENDENT",
            "vendorId": None
        }
    ]
    
    # Document Details
    payload['streetVendingDetail']['documentDetails'] = [
        {
            "applicationId": "",
            "documentType": "FAMILY.PHOTO.PHOTOGRAPH",
            "fileStoreId": str(record.get('photoFileStoreId', '')),
            "documentDetailId": str(record.get('photoFileStoreId', '')),
            "auditDetails": {
                "createdBy": "",
                "createdTime": 0,
                "lastModifiedBy": "",
                "lastModifiedTime": 0
            }
        },
        {
            "applicationId": "",
            "documentType": "PROOF.RESIDENCE.VOTERID",
            "fileStoreId": str(record.get('voterIdFileStoreId', '')),
            "documentDetailId": str(record.get('voterIdFileStoreId', '')),
            "auditDetails": {
                "createdBy": "",
                "createdTime": 0,
                "lastModifiedBy": "",
                "lastModifiedTime": 0
            }
        },
        {
            "applicationId": "",
            "documentType": "PHOTOGRAPH.VENDINGSETUP.PHOTO",
            "fileStoreId": str(record.get('setupPhotoFileStoreId', '')),
            "documentDetailId": str(record.get('setupPhotoFileStoreId', '')),
            "auditDetails": {
                "createdBy": "",
                "createdTime": 0,
                "lastModifiedBy": "",
                "lastModifiedTime": 0
            }
        },
        {
            "applicationId": "",
            "documentType": "IDENTITYPROOF.AADHAAR",
            "fileStoreId": str(record.get('aadhaarFileStoreId', '')),
            "documentDetailId": str(record.get('aadhaarFileStoreId', '')),
            "auditDetails": {
                "createdBy": "",
                "createdTime": 0,
                "lastModifiedBy": "",
                "lastModifiedTime": 0
            }
        }
    ]
    
    # Operation Times (all days)
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    payload['streetVendingDetail']['vendingOperationTimeDetails'] = [
        {
            "applicationId": "",
            "auditDetails": {
                "createdBy": "",
                "createdTime": 0, 
                "lastModifiedBy": "",
                "lastModifiedTime": 0
            },
            "dayOfWeek": day,
            "fromTime": str(record.get('operationStartTime', '08:00')),
            "toTime": str(record.get('operationEndTime', '20:00')),
            "id": ""
        } for day in days
    ]
    
    # Other fields
    payload['streetVendingDetail'].update({
        "benificiaryOfSocialSchemes": str(record.get('benificiaryScheme', '')),
        "enrollmentId": str(record.get('enrollmentId', '')),
        "localAuthorityName": str(record.get('localAuthorityName', '')),
        "vendingArea": str(record.get('vendingArea', '100')),
        "draftId": str(record.get('draftId', ''))
    })
    
    return payload

def process_excel():
    """Main processing function"""
    init_db()
    df = pd.read_excel(EXCEL_PATH)
    
    for _, record in df.iterrows():
        name = record.get('name', '')
        mobile = record.get('mobileNo', '')
        
        try:
            # Prepare payload
            payload = create_base_payload()
            payload = map_excel_to_payload(record, payload)
            
            # Debug output
            logging.debug(f"Payload:\n{json.dumps(payload, indent=2)}")
            
            # Submit to API
            response = requests.post(
                CREATE_API,
                headers=HEADERS,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Log success
            app_id = response.json().get('streetVending', {}).get('streetVendingDetail', {}).get('applicationId', '')
            log_to_db(name, mobile, "SUCCESS", f"AppID: {app_id}")
            logging.info(f"Success: {name} | Mobile: {mobile} | AppID: {app_id}")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API Error: {str(e)}"
            if hasattr(e, 'response'):
                error_msg += f" | Response: {e.response.text}"
            log_to_db(name, mobile, "FAILED", error_msg)
            logging.error(f"Failed {name}: {error_msg}")
        except Exception as e:
            error_msg = f"Processing Error: {str(e)}"
            log_to_db(name, mobile, "FAILED", error_msg)
            logging.error(f"Failed {name}: {error_msg}")
        
        time.sleep(1)  # Rate limiting

if __name__ == "__main__":
    print("=== Street Vendor Migration ===")
    start = time.time()
    try:
        process_excel()
    except Exception as e:
        logging.critical(f"Fatal error: {str(e)}", exc_info=True)
    finally:
        print(f"Completed in {time.time()-start:.2f}s")
        print(f"Database: {DB_PATH}")
        print(f"Logs: migration_debug.log")