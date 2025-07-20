# VAPI Test Integration Guide

This guide explains how to integrate the VAPI webhook testing functionality into the admin system page.

## 1. Add the VAPI Testing Module

First, copy the `admin_vapi_test.py` file to the `ai-tutor/backend` directory. This module contains the functions for testing the VAPI webhook integration.

## 2. Add the VAPI Test Route to admin-server.py

Add the following code to `admin-server.py`:

```python
# Import the VAPI testing module
from admin_vapi_test import run_vapi_test

# Add a new route for testing the VAPI webhook integration
@app.route('/admin/system/test-vapi', methods=['POST'])
def admin_test_vapi():
    """Test the VAPI webhook integration"""
    if not check_auth():
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get the base URL from the request
        base_url = request.form.get('base_url')
        if not base_url:
            # Use the request's host URL as the base URL
            base_url = request.host_url.rstrip('/')
        
        # Run the VAPI test
        test_results = run_vapi_test(db, base_url, VAPI_SECRET)
        
        # Log the test
        log_admin_action('test_vapi', session.get('admin_username', 'unknown'),
                        success=test_results['success'],
                        call_id=test_results['call_id'],
                        ip_address=request.remote_addr)
        
        # Return the results
        return jsonify(test_results)
    
    except Exception as e:
        log_error('ADMIN', 'Error testing VAPI webhook integration', e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

## 3. Add the VAPI Test Section to system.html

Add the HTML and JavaScript from the `vapi_test_template.html` file to the `system.html` template. The HTML should be added to the "System Information" section, and the JavaScript should be added at the bottom of the template.

### Where to Add the HTML

Look for the "System Information" section in the `system.html` template, which typically looks like this:

```html
<div class="card mb-4">
    <div class="card-header">
        <h5 class="mb-0">
            <i class="fas fa-server me-2"></i> System Information
        </h5>
    </div>
    <div class="card-body">
        <!-- System information content -->
    </div>
</div>
```

Add the VAPI Webhook Testing card after this section.

### Where to Add the JavaScript

Look for the JavaScript section at the bottom of the `system.html` template, which typically looks like this:

```html
<script>
    $(document).ready(function() {
        // Existing JavaScript
    });
</script>
```

Add the VAPI Webhook Testing JavaScript inside the `$(document).ready(function() { ... })` block.

## 4. Test the Integration

After adding the code to admin-server.py and system.html, restart the server and navigate to the Admin System page. You should see a new "VAPI Webhook Testing" section with a "Run VAPI Integration Test" button.

Click the button to run the test. The test will:

1. Check if the system_logs table exists
2. Generate a test webhook payload
3. Send a test webhook to the VAPI webhook endpoint
4. Check if webhook logs are created
5. Check if a test student is created
6. Check if a test session is created

The test results will be displayed in an accordion, with each step showing its success or failure status.

## 5. Troubleshooting

If you encounter any issues with the integration, check the following:

1. Make sure the `admin_vapi_test.py` file is in the correct location
2. Make sure the import statement in admin-server.py is correct
3. Make sure the route is properly defined in admin-server.py
4. Make sure the HTML and JavaScript are properly added to system.html
5. Check the browser console for any JavaScript errors
6. Check the server logs for any Python errors

If the test fails, check the specific step that failed and address the issue accordingly. For example:

- If the system_logs table doesn't exist, make sure the database initialization is working correctly
- If the webhook sending fails, check the base URL and make sure the VAPI webhook endpoint is accessible
- If no webhook logs are created, check the system_logger implementation
- If no student or session is created, check the webhook handler implementation