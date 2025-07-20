from flask import jsonify, request, current_app
from admin_vapi_test import run_vapi_integration_test

def handle_vapi_test_route():
    """Handle the VAPI test route."""
    try:
        # Get the base URL from the request or config
        base_url = request.json.get('base_url') if request.is_json else None
        
        # If no base URL was provided, try to get it from the config
        if not base_url:
            base_url = current_app.config.get('BASE_URL')
            
        # Run the VAPI integration test
        results = run_vapi_integration_test(base_url)
        
        # Log the results
        current_app.logger.info(f"VAPI integration test results: {results['overall_success']}")
        
        return jsonify(results)
    except Exception as e:
        current_app.logger.error(f"Error in VAPI test route: {str(e)}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500