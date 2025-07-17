# AI Tutor Admin Dashboard Setup Guide

## 🔐 Security Configuration

### **CRITICAL: Change Default Credentials**

The admin dashboard currently has **default credentials that MUST be changed before production use**.

**Default credentials (CHANGE THESE!):**
- Username: `admin`
- Password: `admin123`

### **Production Setup (Recommended)**

1. **Create Environment File**
   ```bash
   # Create .env file in project root
   touch .env
   ```

2. **Set Secure Environment Variables**
   ```bash
   # Add to .env file
   ADMIN_USERNAME=your_secure_username
   ADMIN_PASSWORD=your_secure_password_here
   FLASK_SECRET_KEY=your_very_long_random_secret_key_here
   FLASK_ENV=production
   ```

3. **Install python-dotenv**
   ```bash
   pip install python-dotenv
   ```

### **Quick Setup (Development Only)**

For development/testing only, you can use the default credentials:
- Username: `admin`
- Password: `admin123`

**⚠️ WARNING: Never use default credentials in production!**

## 🚀 Running the Admin Dashboard

### **Development Mode**
```bash
python admin-server.py
```

### **Production Mode**
```bash
# Set environment variables
export FLASK_ENV=production
export ADMIN_USERNAME="your_username"
export ADMIN_PASSWORD="your_secure_password"
export FLASK_SECRET_KEY="your_secret_key"

# Run with production settings
python admin-server.py
```

### **Access the Dashboard**
- URL: `http://localhost:5000/admin`
- Default login: `admin` / `admin123` (CHANGE THIS!)

## 📋 Features

### **Authentication System**
- Secure password hashing (SHA-256)
- Session-based authentication
- Automatic redirects for unauthorized access

### **Dashboard Pages**
1. **📊 Dashboard** - System overview and statistics
2. **👥 Students** - Student management and viewing
3. **📁 Files** - Data directory browser
4. **⚙️ System** - Phone mappings and system settings

### **Student Management**
- View all students with search and filtering
- Individual student profiles with progress tracking
- Phone number mapping display
- Session history and analytics

### **File Browser**
- Navigate entire data directory
- View JSON files with syntax highlighting
- Breadcrumb navigation
- File size and modification tracking

### **System Monitoring**
- Phone number to student ID mappings
- System health indicators
- MCP server status monitoring
- Data directory statistics

## 🔒 Security Features

### **Authentication**
- SHA-256 password hashing
- Session management with secure tokens
- Automatic logout on session expiry

### **Path Security**
- File browser restricted to data directory only
- Path traversal attack prevention
- Input validation on all file operations

### **Production Considerations**
- Environment variable support for credentials
- Configurable secret keys
- Debug mode disabled in production
- Secure session management

## 📁 File Structure

```
project/
├── admin-server.py          # Main Flask application
├── templates/               # HTML templates
│   ├── base.html           # Base template with navigation
│   ├── login.html          # Login page
│   ├── dashboard.html      # Main dashboard
│   ├── students.html       # Student listing
│   ├── student_detail.html # Individual student view
│   ├── files.html          # File browser
│   ├── file_view.html      # File content viewer
│   └── system.html         # System settings
├── data/                   # Student and system data
│   ├── students/           # Student profiles and sessions
│   ├── curriculum/         # Curriculum data
│   └── phone_mapping.json  # Phone number mappings
└── .env                    # Environment variables (create this)
```

## 🛠️ Dependencies

### **Required Python Packages**
```bash
pip install flask python-dotenv pyyaml
```

### **Existing Integration**
- Integrates with existing MCP server (`session-enhanced-server.py`)
- Uses existing student data structure
- Compatible with phone mapping system

## 🔧 Configuration Options

### **Environment Variables**
| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_USERNAME` | `admin` | Admin username |
| `ADMIN_PASSWORD` | `admin123` | Admin password (plain text) |
| `FLASK_SECRET_KEY` | Random | Session encryption key |
| `FLASK_ENV` | `development` | Flask environment |
| `ADMIN_PORT` | `5000` | Server port |

### **Security Settings**
- All passwords are hashed using SHA-256
- Sessions expire on browser close
- File access restricted to data directory
- CSRF protection enabled

## 🚨 Production Deployment Checklist

- [ ] Change default admin credentials
- [ ] Set secure environment variables
- [ ] Disable debug mode
- [ ] Use HTTPS in production
- [ ] Set up firewall rules
- [ ] Configure backup strategy
- [ ] Set up monitoring/logging
- [ ] Test all functionality

## 🆘 Troubleshooting

### **Cannot Login**
- Check username/password are correct
- Verify environment variables are set
- Check server logs for errors

### **Template Errors**
- Ensure all templates exist in `templates/` directory
- Check template syntax for Jinja2 errors

### **File Browser Issues**
- Verify `data/` directory exists
- Check file permissions
- Ensure path security restrictions

### **Integration Problems**
- Verify `session-enhanced-server.py` exists
- Check MCP server is running
- Validate phone mapping file format

## 📞 Support

For issues or questions about the admin dashboard:
1. Check server logs for error messages
2. Verify all dependencies are installed
3. Ensure proper file permissions
4. Test with default configuration first

---

**⚠️ SECURITY REMINDER: Always change default credentials before production use!**