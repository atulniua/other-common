import pandas as pd
import requests
import json
from datetime import datetime

# Function to convert date to EPOCH time
def date_to_epoch(date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    epoch_time = int(dt.timestamp() * 1000)  # Convert to milliseconds
    return epoch_time

# Load the Excel file
excel_file_path = '/Users/atul/Documents/hrms.xlsx'  # Update this path to your actual file path
df = pd.read_excel(excel_file_path)

# Iterate over each row in the dataframe
for index, row in df.iterrows():
    tenant_id = row['tenantId']
    from_date = date_to_epoch(row['fromDate'])  # Convert date string to epoch
    date_of_appointment = date_to_epoch(row['dateOfAppointment'])  # Convert date string to epoch
    employee_type = row['employeeType']
    hierarchy = row['hierarchy']
    boundary = row['boundary']
    mobile_number = row['mobileNumber']
    name = row['name']
    correspondence_address = row['correspondenceAddress']
    gender = row['gender']
    dob = date_to_epoch(row['dob'])  # Convert date string to epoch

    # Create JSON structure
    json_data = {
        "RequestInfo": {
            "apiId": "Rainmaker",
            "authToken": "396904f7-3e7e-443b-8365-f071fa3066d9",
            "userInfo": {
                "id": 208,
                "uuid": "c2541e99-733d-4dfc-9379-630b6e1a9b2f",
                "userName": "CityAAdmin",
                "name": "City A Admin",
                "mobileNumber": "1234567890",
                "emailId": None,
                "locale": None,
                "type": "EMPLOYEE",
                "roles": [
                    {
                        "name": "HRMS Admin",
                        "code": "HRMS_ADMIN",
                        "tenantId": "pg.citya"
                    },
                    {
                        "name": "Superuser",
                        "code": "SUPERUSER",
                        "tenantId": "pg.citya"
                    }
                ],
                "active": True,
                "tenantId": "pg.citya",
                "permanentCity": None
            }
        },
        "Employees": [
            {
                "tenantId": tenant_id,
                "employeeStatus": "EMPLOYED",
                "assignments": [
                    {
                        "fromDate": from_date,
                        "isCurrentAssignment": True,
                        "department": "DEPT_25",
                        "designation": "DESIG_03"
                    }
                ],
                "dateOfAppointment": date_of_appointment,
                "employeeType": employee_type,
                "jurisdictions": [
                    {
                        "hierarchy": hierarchy,
                        "boundaryType": "City",
                        "boundary": boundary,
                        "tenantId": tenant_id,
                        "roles": [
                            {
                                "code": "ASSET_INITIATOR",
                                "name": "Asset Initiator Employee",
                                "tenantId": tenant_id
                            }
                        ]
                    }
                ],
                "user": {
                    "mobileNumber": mobile_number,
                    "name": name,
                    "correspondenceAddress": correspondence_address,
                    "gender": gender,
                    "dob": dob,
                    "roles": [
                        {
                            "code": "ASSET_INITIATOR",
                            "name": "Asset Initiator Employee",
                            "tenantId": tenant_id
                        }
                    ],
                    "tenantId": tenant_id
                },
                "serviceHistory": [],
                "education": [],
                "tests": []
            }
        ]
    }

    # Print JSON data to verify
    print(json.dumps(json_data, indent=4))

    # Send the POST request
    url = 'http://localhost:8084/egov-hrms/employees/_create'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(json_data))

    # Print the response from the API
    print(response.status_code)
    print(response.json())
