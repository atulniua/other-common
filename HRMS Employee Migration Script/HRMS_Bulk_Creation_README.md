# HRMS Employee Bulk Creation Script

## Overview
This Python script reads employee data from Excel file and creates bulk employees through HRMS API.

## Prerequisites
```bash
pip install pandas requests openpyxl
```

## Excel File Format
Excel file should have following columns:

| Column Name | Data Type | Example |
|-------------|-----------|---------|
| tenantId | String | pg.citya |
| fromDate | Date | 2024-01-01 |
| dateOfAppointment | Date | 2024-01-01 |
| employeeType | String | PERMANENT |
| hierarchy | String | REVENUE |
| boundary | String | CITYA |
| mobileNumber | String | 9876543210 |
| name | String | John Doe |
| correspondenceAddress | String | 123 Main St |
| gender | String | MALE |
| dob | Date | 1990-01-01 |

## Configuration
1. **Excel File Path**: Update file path in script
   ```python
   excel_file_path = '/path/to/your/hrms.xlsx'
   ```

2. **API URL**: Update HRMS service URL
   ```python
   url = 'http://localhost:8084/egov-hrms/employees/_create'
   ```

3. **Auth Token**: Update with valid auth token
   ```python
   "authToken": "your-valid-token-here"
   ```

## Usage
```bash
python hrms_bulk_create.py
```

## Adding Roles from Excel

If you want to pick roles from Excel as well:

### 1. Add Role Columns in Excel:
| roleCode | roleName |
|----------|----------|
| ASSET_INITIATOR | Asset Initiator Employee |
| BPA_APPROVER | BPA Approver |

### 2. Add Role Code in Script:
```python
# Read role data from Excel
role_code = row['roleCode'] if pd.notna(row['roleCode']) else 'ASSET_INITIATOR'
role_name = row['roleName'] if pd.notna(row['roleName']) else 'Asset Initiator Employee'

# Update roles in JSON
"roles": [
    {
        "code": role_code,
        "name": role_name,
        "tenantId": tenant_id
    }
]
```

### 3. For Multiple Roles:
```python
# Comma-separated roles in Excel
roles_str = row['roles']  # "ASSET_INITIATOR,BPA_APPROVER"
role_codes = roles_str.split(',') if pd.notna(roles_str) else ['ASSET_INITIATOR']

roles_list = []
for code in role_codes:
    roles_list.append({
        "code": code.strip(),
        "name": f"{code.strip()} Employee",
        "tenantId": tenant_id
    })
```

## Error Handling
Script prints response status and errors. Check failed requests manually.

## Notes
- Date format: YYYY-MM-DD
- Mobile numbers should be unique
- Ensure HRMS service is running
- Valid auth token required

## Sample Excel Data
```
tenantId,fromDate,dateOfAppointment,employeeType,hierarchy,boundary,mobileNumber,name,correspondenceAddress,gender,dob
pg.citya,2024-01-01,2024-01-01,PERMANENT,REVENUE,CITYA,9876543210,John Doe,123 Main St,MALE,1990-01-01
pg.citya,2024-01-01,2024-01-01,PERMANENT,REVENUE,CITYA,9876543211,Jane Smith,456 Oak Ave,FEMALE,1985-05-15
```

## Troubleshooting
- Check if HRMS service is running on correct port
- Verify auth token is valid and not expired
- Ensure Excel file path is correct
- Check mobile numbers are unique across system
- Verify tenant IDs exist in system