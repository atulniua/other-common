# BPAREG Stakeholder Migration Kit 🏗️

Complete Excel-to-BPAREG stakeholder migration solution for UPYOG platform.

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Check Python version (3.8+ required)
python3 --version

# Install required packages
pip3 install pandas requests openpyxl
```

### 2. Setup Services
```bash
# Terminal 1 - User Service
kubectl port-forward svc/egov-user 8081:8080

# Terminal 2 - TL Services
kubectl port-forward svc/tl-services 8079:8080
```

### 3. Get Auth Token
1. Login to UPYOG in browser
2. Open Developer Tools (F12) → Network tab
3. Make any API call
4. Copy `authorization` header value (without "Bearer ")
5. Update `TOKEN` in `BPAREGAPP.py`

### 4. Configure Script
Edit `BPAREGAPP.py`:
```python
# Line 15: Update auth token
TOKEN = "your-auth-token-here"

# Line 16: Update Excel file path
EXCEL_FILE = "/full/path/to/your/bpareg_template.xlsx"
```

### 5. Run Migration
```bash
# Create Excel template (first time only)
python3 BPAREGAPP.py template

# Run migration
python3 BPAREGAPP.py migrate

# Show help
python3 BPAREGAPP.py help
```

## 📊 Excel Template

### Required Columns:
| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `name` | ✅ | Full name | KRISHNA KAMAL CHALIHA |
| `mobile` | ✅ | Mobile number | 7065723738 |
| `email` | ❌ | Email address | krishna@example.com |
| `gender` | ❌ | MALE/FEMALE | MALE |
| `address` | ❌ | Full address | House No 123 Guwahati |
| `pan` | ❌ | PAN number | KRISHPAN123 |
| `trade_type` | ❌ | Stakeholder type | ARCHITECT.CLASSA |
| `council_no` | ❌ | Council registration | TP/RTP/03/Arch.Nov/22/029 |
| `city` | ❌ | City name | Guwahati |
| `landmark` | ❌ | Landmark | Kamakhya Temple |
| `pincode` | ❌ | PIN code | 781001 |

### Trade Types Supported:
- `ARCHITECT.CLASSA` / `ARCHITECT.CLASSB`
- `STRUCTURALENGINEER.CLASSA` / `STRUCTURALENGINEER.CLASSB`
- `SUPERVISOR.CLASSA` / `SUPERVISOR.CLASSB`
- `TOWNPLANNER.CLASSA` / `TOWNPLANNER.CLASSB`

## 🔄 Migration Process

The script performs these steps for each stakeholder:

1. **User Creation** → Creates citizen user with appropriate BPA role
2. **BPAREG Application** → Creates stakeholder registration
3. **APPLY Action** → Submits application
4. **Excel Update** → Updates file with results

## 📈 Output Columns

After migration, Excel will have these additional columns:
- `user_uuid` - Generated user UUID
- `final_mobile` - Actual mobile used (may differ if original exists)
- `bpa_roles` - Assigned BPA roles
- `application_number` - BPAREG application number
- `app_status` - Application status
- `migration_status` - MIGRATED/FAILED/PARTIAL
- `result` - Detailed result message

## 🛠️ Troubleshooting

### Common Issues:

**"Connection refused"**
```bash
# Check services are running
curl http://localhost:8081/user/health
curl http://localhost:8079/tl-services/health

# Restart port forwarding if needed
kubectl port-forward svc/egov-user 8081:8080
kubectl port-forward svc/tl-services 8079:8080
```

**"Authentication failed"**
- Get fresh token from browser dev tools
- Make sure token doesn't have "Bearer " prefix
- Check user permissions

**"Excel file not found"**
- Update `EXCEL_FILE` path in script
- Use absolute path
- Check file permissions

**"User creation failed"**
- Mobile number might already exist (script handles this automatically)
- Check user service logs
- Verify API permissions

## 📁 File Structure
```
BPAREG-Migration/
├── BPAREGAPP.py              # Main migration script
├── bpareg_template.xlsx      # Excel template with data
└── README.md                 # This documentation
```

## 🎯 Commands

```bash
# Show help and available commands
python3 BPAREGAPP.py help

# Create Excel template with sample data
python3 BPAREGAPP.py template

# Run migration from Excel file
python3 BPAREGAPP.py migrate
```

## ✅ Success Indicators

- **Services Running**: Port forwarding active on 8081, 8079
- **Auth Valid**: Token works for API calls
- **Excel Ready**: Template created with stakeholder data
- **Migration Success**: Users created with BPA roles
- **Applications Created**: BPAREG applications generated

## 🔒 Security Notes

- Keep `AUTH_TOKEN` secure and don't commit to version control
- Use environment variables for production deployments
- Regularly rotate authentication tokens
- Backup Excel data before migration

## 📞 Support

### Before Running:
1. ✅ Python 3.8+ installed
2. ✅ Required packages installed (`pandas`, `requests`, `openpyxl`)
3. ✅ kubectl configured and services accessible
4. ✅ Services port-forwarded (8081, 8079)
5. ✅ Auth token updated in script
6. ✅ Excel file path configured
7. ✅ Excel template created with data

### During Migration:
- Monitor console output for real-time progress
- Check Excel file for updated results
- Verify created users in UPYOG UI
- Review any error messages in console

### After Migration:
- Check `migration_status` column in Excel
- Verify users have appropriate BPA roles
- Confirm BPAREG applications are created
- Test user login with generated credentials

---

**Happy Migrating! 🚀**

For issues or questions, check the troubleshooting section above or review UPYOG documentation.