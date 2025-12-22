#!/usr/bin/env python3
"""
BPAREG Stakeholder Migration App
Single file for all BPAREG migration operations
"""
import pandas as pd
import requests
import time
import random
import sys
import os

# =============================================================================
# CONFIGURATION
# =============================================================================
USER_API = "http://localhost:8081/user/users/_createnovalidate"
BPAREG_CREATE_API = "http://localhost:8079/tl-services/v1/BPAREG/_create"
BPAREG_UPDATE_API = "http://localhost:8079/tl-services/v1/BPAREG/_update"
TOKEN = "bd64d685-bf1a-451d-afd0-b0ab3156a91b"
EXCEL_FILE = "/Users/atul/Documents/UPASSET/Keshav-UPYOG-NIUA/Migration-Kits/BPAREG/bpareg_template.xlsx"

# Role mapping - Using correct MDMS roles
ROLE_MAPPING = {
    "ARCHITECT.CLASSA": "BPA_ARCHITECT",
    "ARCHITECT.CLASSB": "BPA_ARCHITECT", 
    "STRUCTURALENGINEER.CLASSA": "BPA_ENGINEER",
    "STRUCTURALENGINEER.CLASSB": "BPA_ENGINEER",
    "SUPERVISOR.CLASSA": "BPA_SUPERVISOR",
    "SUPERVISOR.CLASSB": "BPA_SUPERVISOR",
    "TOWNPLANNER.CLASSA": "BPA_TOWN_PLANNER",
    "TOWNPLANNER.CLASSB": "BPA_TOWN_PLANNER",
    "GROUP_AGENCY": "BPA_GROUP_AGENCY",       
    "GEO_TECH_ENGINEER": "BPA_GEO_TECH_ENGINEER",
    "CIVIL_ENGINEER": "BPA_CIVIL_ENGINEER",
    "UTILITY_SERVICE_ENGINEER": "BPA_UTILITY_SERVICE_ENGINEER",
    "LANDSCAPE_ARCHITECT": "BPA_LANDSCAPE_ARCHITECT",
    "URBAN_DESIGNER": "BPA_URBAN_DESIGNER"

}

# =============================================================================
# CORE FUNCTIONS
# =============================================================================
def get_existing_user(mobile, tenant_id="as"):
    """Get existing user by mobile number"""
    search_payload = {
        "RequestInfo": {
            "apiId": "Rainmaker",
            "authToken": TOKEN,
            "userInfo": {"id": 1, "uuid": "admin", "userName": "admin", "type": "EMPLOYEE", "roles": [{"code": "SUPERUSER", "tenantId": "as"}], "tenantId": "as"},
            "msgId": f"{int(time.time() * 1000)}|en_IN"
        },
        "mobileNumber": mobile,
        "tenantId": tenant_id
    }
    
    try:
        r = requests.post("http://localhost:8080/user/_search", json=search_payload, timeout=10)
        if r.status_code == 200:
            users = r.json().get('user', [])
            if users:
                user = users[0]
                return user['uuid'], user['mobileNumber'], [role['code'] for role in user.get('roles', [])]
        return None, None, []
    except Exception as e:
        return None, None, []

def create_user_with_bpa_role(mobile, name, email="", gender="MALE", trade_type="ARCHITECT.CLASSA", tenant_id="as"):
    """Create user with appropriate BPA role"""
    bpa_role = ROLE_MAPPING.get(trade_type, "BPA_ARCHITECT")
    
    payload = {
        "requestInfo": {
            "apiId": "Rainmaker",
            "authToken": TOKEN,
            "userInfo": {"id": 1, "uuid": "admin", "userName": "admin", "type": "EMPLOYEE", "roles": [{"code": "SUPERUSER", "tenantId": "as"}], "tenantId": "as"},
            "msgId": f"{int(time.time() * 1000)}|en_IN"
        },
        "user": {
            "userName": mobile,
            "name": name,
            "mobileNumber": mobile,
            "emailId": email if email else f"{mobile}@migration.com",
            "gender": gender,
            "type": "CITIZEN",
            "active": True,
            "password": "eGov@123",
            "roles": [
                {"code": "CITIZEN", "tenantId": tenant_id},
                {"code": bpa_role, "tenantId": tenant_id}
            ],
            "tenantId": tenant_id
        }
    }
    
    try:
        r = requests.post(USER_API, json=payload, timeout=10)
        if r.status_code == 200:
            user_data = r.json()['user'][0]
            user_uuid = user_data['uuid']
            actual_mobile = user_data['mobileNumber']
            roles = [role['code'] for role in user_data.get('roles', [])]
            return user_uuid, actual_mobile, roles, "SUCCESS"
        elif "DuplicateUserNameException" in r.text:
            return None, None, [], f"DUPLICATE_MOBILE: {mobile} already exists"
        else:
            print(f"   🔍 Debug - Status: {r.status_code}, Response: {r.text[:200]}")
            return None, None, [], f"Error: {r.status_code}"
    except Exception as e:
        return None, None, [], f"Exception: {e}"

def create_bpareg_application(user_uuid, user_id, mobile, name, email, council_no, trade_type, tenant_id="as"):
    """Create BPAREG application"""
    # Get actual user details to ensure proper roles
    actual_uuid, actual_mobile, actual_roles = get_existing_user(mobile, tenant_id)
    if actual_uuid:
        user_uuid, mobile, user_roles = actual_uuid, actual_mobile, actual_roles
    else:
        user_roles = ["CITIZEN", ROLE_MAPPING.get(trade_type, "BPA_ARCHITECT")]
    
    payload = {
        "Licenses": [{
            "tradeLicenseDetail": {
                "owners": [{
                    "uuid": user_uuid,
                    "gender": "MALE",
                    "mobileNumber": mobile,
                    "name": name,
                    "dob": None,
                    "emailId": email if email and email != 'nan' else f"{mobile}@migration.com",
                    "permanentAddress": "Migration Address",
                    "correspondenceAddress": "Migration Address",
                    "pan": "",
                    "active": True
                }],
                "subOwnerShipCategory": "INDIVIDUAL",
                "tradeUnits": [{"tradeType": trade_type}],
                "additionalDetail": {"counsilForArchNo": council_no if council_no and council_no != 'nan' else 'MIG123'},
                "address": {
                    "tenantId": tenant_id,
                    "city": "Migration City", 
                    "landmark": "Migration Landmark", 
                    "pincode": "123456",
                    "locality": {"code": "MIG_LOCALITY"}
                },
                "institution": None,
                "applicationDocuments": None
            },
            "licenseType": "PERMANENT",
            "businessService": "BPAREG",
            "tenantId": tenant_id,
            "action": "NOWORKFLOW"
        }],
        "RequestInfo": {
            "apiId": "Rainmaker",
            "authToken": TOKEN,
            "userInfo": {
                "id": user_id,
                "uuid": user_uuid,
                "userName": mobile,
                "name": name,
                "mobileNumber": mobile,
                "type": "CITIZEN",
                "roles": [{"name": role, "code": role, "tenantId": tenant_id} for role in user_roles],
                "active": True,
                "tenantId": tenant_id
            },
            "msgId": f"{int(time.time() * 1000)}|en_IN",
            "plainAccessRequest": {}
        }
    }
    
    try:
        r = requests.post(BPAREG_CREATE_API, json=payload, timeout=15)
        if r.status_code == 200:
            license_data = r.json()['Licenses'][0]
            app_num = license_data.get('applicationNumber')
            status = license_data.get('status')
            
            # Try to apply
            time.sleep(1)
            license_data['action'] = "APPLY"
            license_data['tradeLicenseDetail']['applicationDocuments'] = [
                {"fileStoreId": "dummy-file", "fileStore": "dummy-file", "fileName": "doc.pdf", "documentType": "APPL.BPAREG_GOVT_APPROVED_ID_CARD", "tenantId": tenant_id}
            ]
            
            update_payload = {"Licenses": [license_data], "RequestInfo": payload["RequestInfo"]}
            update_payload["RequestInfo"]["msgId"] = f"{int(time.time() * 1000)}|en_IN"
            
            r = requests.post(BPAREG_UPDATE_API, json=update_payload, timeout=15)
            if r.status_code == 200:
                final_license = r.json()['Licenses'][0]
                final_status = final_license.get('status')
                return app_num, final_status, "SUCCESS"
            
            return app_num, status, "APPLY_FAILED"
        else:
            print(f"   🔍 BPAREG Debug - Status: {r.status_code}, Response: {r.text[:300]}")
            return None, None, f"CREATE_FAILED: {r.status_code}"
    except Exception as e:
        return None, None, f"Exception: {e}"

def retry_failed_bpareg():
    """Retry BPAREG creation for PARTIAL/FAILED records"""
    try:
        if not os.path.exists(EXCEL_FILE):
            return 0
        
        df = pd.read_excel(EXCEL_FILE)

        # Ensure result columns exist and have string dtype to prevent warnings
        result_columns = ['user_uuid', 'final_mobile', 'bpa_roles', 'application_number', 'app_status', 'migration_status', 'result']
        for col in result_columns:
            if col not in df.columns:
                df[col] = ''
            df[col] = df[col].astype(str)
        
        # Find records with PARTIAL status (user created but BPAREG failed)
        failed_records = df[
            (df['migration_status'] == 'PARTIAL') | 
            (df['migration_status'] == 'FAILED') |
            (df['application_number'].isna() & df['user_uuid'].notna())
        ]
        
        if len(failed_records) == 0:
            return 0
            
        print(f"🔄 Retrying {len(failed_records)} failed BPAREG applications...")
        
        retry_success = 0
        for i, row in failed_records.iterrows():
            name = str(row.get('name', f'Stakeholder_{i}'))
            mobile = str(row.get('mobile', f'999999{i:04d}'))
            user_uuid = str(row.get('user_uuid', ''))
            trade_type = str(row.get('trade_type', 'ARCHITECT.CLASSA'))
            council_no = str(row.get('council_no', 'MIG123'))
            tenant_id = str(row.get('tenant_id', 'as'))
            email = str(row.get('email', ''))
            
            print(f"\n🔄 Retry: {name} ({mobile})")
            
            # Get user details first
            existing_uuid, existing_mobile, existing_roles = get_existing_user(mobile, tenant_id)
            
            if existing_uuid:
                print(f"   🔍 Found user: {existing_uuid}")
                final_uuid, final_mobile, final_roles = existing_uuid, existing_mobile, existing_roles
            else:
                print(f"   🔍 User not found, creating new user...")
                # Create user first
                final_uuid, final_mobile, final_roles, user_result = create_user_with_bpa_role(
                    mobile, name, email, 'MALE', trade_type, tenant_id
                )
                if not final_uuid:
                    print(f"   ❌ User creation failed: {user_result}")
                    continue
                print(f"   ✅ User created: {final_mobile}")
            
            # Try BPAREG creation
            app_num, app_status, bpareg_result = create_bpareg_application(
                final_uuid, 4000 + i, final_mobile, name, email, council_no, trade_type, tenant_id
            )
            
            # Update Excel with user info
            df.at[i, 'user_uuid'] = str(final_uuid)
            df.at[i, 'final_mobile'] = str(final_mobile)
            df.at[i, 'bpa_roles'] = ', '.join(final_roles)
            
            if app_num:
                print(f"   ✅ BPAREG: {app_num} ({app_status})")
                df.at[i, 'application_number'] = str(app_num)
                df.at[i, 'app_status'] = str(app_status)
                df.at[i, 'migration_status'] = 'MIGRATED'
                df.at[i, 'result'] = 'Retry successful - Complete migration'
                retry_success += 1
            else:
                print(f"   ❌ Still failed: {bpareg_result}")
                df.at[i, 'result'] = f'Retry failed: {bpareg_result}'
        
        # Save updated results
        df.to_excel(EXCEL_FILE, index=False)
        print(f"✅ Retry completed: {retry_success}/{len(failed_records)} successful")
        return retry_success
        
    except Exception as e:
        print(f"❌ Retry error: {e}")
        return 0

def migrate_from_excel():
    """Main migration function"""
    try:
        # First, retry any failed BPAREG applications
        retry_count = retry_failed_bpareg()
        if retry_count > 0:
            print(f"\n📋 Retried {retry_count} failed applications\n")
        
        # Read Excel file
        if not os.path.exists(EXCEL_FILE):
            print(f"❌ Excel file not found: {EXCEL_FILE}")
            return False
        
        df = pd.read_excel(EXCEL_FILE)
        print(f"📊 Processing {len(df)} stakeholders from Excel")
        
        # Ensure result columns exist and have string dtype to prevent warnings
        result_columns = ['user_uuid', 'final_mobile', 'bpa_roles', 'application_number', 'app_status', 'migration_status', 'result']
        for col in result_columns:
            if col not in df.columns:
                df[col] = ''
            df[col] = df[col].astype(str)
        
        success = 0
        for i, row in df.iterrows():
            name = str(row.get('name', f'Stakeholder_{i}'))
            mobile = str(row.get('mobile', f'999999{i:04d}'))
            email = str(row.get('email', ''))
            gender = str(row.get('gender', 'MALE'))
            trade_type = str(row.get('trade_type', 'ARCHITECT.CLASSA'))
            council_no = str(row.get('council_no', 'MIG123'))
            tenant_id = str(row.get('tenant_id', 'as'))
            
            print(f"\n🔄 {i+1}/{len(df)}: {name} ({mobile}) - {trade_type} - {tenant_id}")
            print(f"   🎯 Expected BPA Role: {ROLE_MAPPING.get(trade_type, 'BPA_ARCHITECT')}")
            
            # Check if user already exists
            existing_uuid, existing_mobile, existing_roles = get_existing_user(mobile, tenant_id)
            
            if existing_uuid:
                print(f"   🔍 Found existing user: {existing_mobile}")
                print(f"   📋 Existing roles: {existing_roles}")
                user_uuid, final_mobile, roles = existing_uuid, existing_mobile, existing_roles
                user_result = "EXISTING_USER"
            else:
                # Create new user with BPA role
                user_uuid, final_mobile, roles, user_result = create_user_with_bpa_role(
                    mobile, name, email, gender, trade_type, tenant_id
                )
            
            if user_uuid:
                if user_result != "EXISTING_USER":
                    print(f"   ✅ User: {final_mobile}")
                    print(f"   📋 Roles: {roles}")
                
                df.at[i, 'user_uuid'] = str(user_uuid)
                df.at[i, 'final_mobile'] = str(final_mobile)
                df.at[i, 'bpa_roles'] = ', '.join(roles)
                
                # Create BPAREG application
                app_num, app_status, bpareg_result = create_bpareg_application(
                    user_uuid, 4000 + i, final_mobile, name, email, council_no, trade_type, tenant_id
                )
                
                if app_num:
                    print(f"   ✅ BPAREG: {app_num} ({app_status})")
                    df.at[i, 'application_number'] = str(app_num)
                    df.at[i, 'app_status'] = str(app_status)
                    df.at[i, 'migration_status'] = 'MIGRATED'
                    df.at[i, 'result'] = 'Complete migration with BPA role and application'
                else:
                    print(f"   ⚠️ BPAREG failed but user has BPA role")
                    df.at[i, 'migration_status'] = 'PARTIAL'
                    df.at[i, 'result'] = f'User created with BPA role, BPAREG failed: {bpareg_result}'
                
                success += 1
            else:
                print(f"   ❌ Failed: {user_result}")
                df.at[i, 'migration_status'] = 'FAILED'
                df.at[i, 'result'] = str(user_result)
                df.at[i, 'result'] = user_result
            
            # Save progress every 3 records
            if (i + 1) % 3 == 0:
                df.to_excel(EXCEL_FILE, index=False)
                print(f"   💾 Progress saved")
            
            time.sleep(1)
        
        # Final save
        df.to_excel(EXCEL_FILE, index=False)
        
        print(f"\n🎉 MIGRATION COMPLETED!")
        print(f"✅ Success: {success}/{len(df)} stakeholders")
        print(f"📁 Updated file: {EXCEL_FILE}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_excel_template():
    """Create Excel template with sample data"""
    data = {
        'name': [
            'KRISHNA KAMAL CHALIHA',
            'BIKRAM ADITYA NATH', 
            'RAJESH KUMAR',
            'PRIYA SHARMA',
            'AMIT SINGH'
        ],
        'mobile': [
            '7065723738',
            '8118250128',
            '9876543210',
            '9876543211', 
            '9876543212'
        ],
        'email': [
            'krishna.chaliha@example.com',
            'bikram.aditya.nath@gmail.com',
            'rajesh.architect@example.com',
            'priya.engineer@example.com',
            'amit.supervisor@example.com'
        ],
        'gender': [
            'MALE',
            'MALE',
            'MALE',
            'FEMALE',
            'MALE'
        ],
        'address': [
            'House No 123 Guwahati',
            'Villa 456 Dispur',
            'Plot 789 Sector 15',
            'House 321 Model Town',
            'Flat 654 Banjara Hills'
        ],
        'pan': [
            'KRISHPAN123',
            'BIKRAMPAN456',
            'RAJESHPAN789',
            'PRIYAPAN321',
            'AMITPAN654'
        ],
        'trade_type': [
            'STRUCTURALENGINEER.CLASSA',
            'STRUCTURALENGINEER.CLASSA',
            'ARCHITECT.CLASSB',
            'STRUCTURALENGINEER.CLASSA',
            'SUPERVISOR.CLASSA'
        ],
        'council_no': [
            'TP/RTP/03/Arch.Nov/22/029',
            'TP/RTP/03/Arch.Nov/22/018',
            'ARCH/2024/001',
            'ENG/2024/001',
            'SUP/2024/001'
        ],
        'city': [
            'Guwahati',
            'Guwahati',
            'Delhi',
            'Mumbai',
            'Hyderabad'
        ],
        'landmark': [
            'Kamakhya Temple',
            'Brahmaputra River',
            'India Gate',
            'Gateway of India',
            'Charminar'
        ],
        'pincode': [
            '781001',
            '781005',
            '110001',
            '400001',
            '500034'
        ],
        'tenant_id': [
            'as',
            'as',
            'as',
            'as',
            'as'
        ]
    }
    
    df = pd.DataFrame(data)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Excel template created: {EXCEL_FILE}")

def show_help():
    """Show help menu"""
    print("🏗️ BPAREG Migration App")
    print("=" * 40)
    print("Commands:")
    print("  migrate    - Run migration from Excel")
    print("  retry      - Retry failed BPAREG applications")
    print("  template   - Create Excel template")
    print("  help       - Show this help")
    print("=" * 40)
    print(f"Excel file: {EXCEL_FILE}")
    print(f"Token: {TOKEN[:20]}...")

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "migrate":
        print("🚀 Starting BPAREG migration...")
        migrate_from_excel()
    elif command == "retry":
        print("🔄 Retrying failed BPAREG applications...")
        retry_count = retry_failed_bpareg()
        if retry_count == 0:
            print("✅ No failed applications to retry")
    elif command == "template":
        print("📊 Creating Excel template...")
        create_excel_template()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()
