interface LogRequestData {
  endpoint: string;
  request_data: any;
  session_id?: string;
  token_id?: number;
}

interface LogResponseData {
  request_id: string;
  response_data: any;
  http_status_code: number;
}

class MCPLogger {
  private baseUrl: string;
  private authToken: string | null;
  private enabled: boolean;

  constructor() {
    // Get Flask API URL from environment or use default
    this.baseUrl = (process as any).env.FLASK_API_URL || 'http://localhost:5000';
    this.authToken = (process as any).env.MCP_LOGGING_TOKEN || null;
    this.enabled = (process as any).env.MCP_LOGGING_ENABLED !== 'false'; // Default to enabled
  }

  /**
   * Extract token ID from authorization header
   */
  private extractTokenId(authHeader?: string): number | undefined {
    // For now, we'll just return undefined
    // In a real implementation, you might decode the JWT or lookup the token
    return undefined;
  }

  /**
   * Log an incoming MCP request
   */
  async logRequest(endpoint: string, requestData: any, sessionId?: string, authHeader?: string): Promise<string | null> {
    if (!this.enabled) {
      return null;
    }

    try {
      const tokenId = this.extractTokenId(authHeader);
      
      const logData: LogRequestData = {
        endpoint,
        request_data: requestData,
        session_id: sessionId,
        token_id: tokenId
      };

      const headers: any = {
        'Content-Type': 'application/json'
      };

      // Add auth token if available
      if (this.authToken) {
        headers['Authorization'] = `Bearer ${this.authToken}`;
      }

      // Use dynamic import for node-fetch
      const { default: fetch } = await import('node-fetch');
      
      const response = await fetch(`${this.baseUrl}/api/v1/admin/api/mcp/log-request`, {
        method: 'POST',
        headers,
        body: JSON.stringify(logData)
      } as any);

      if (response.ok) {
        const result: any = await response.json();
        return result.request_id;
      } else {
        console.warn(`Failed to log MCP request: ${response.status} ${response.statusText}`);
        return null;
      }
    } catch (error) {
      // Log error but don't fail the main operation
      console.warn(`Error logging MCP request:`, error);
      return null;
    }
  }

  /**
   * Log an MCP response
   */
  async logResponse(requestId: string, responseData: any, statusCode: number = 200): Promise<boolean> {
    if (!this.enabled || !requestId) {
      return false;
    }

    try {
      const logData: LogResponseData = {
        request_id: requestId,
        response_data: responseData,
        http_status_code: statusCode
      };

      const headers: any = {
        'Content-Type': 'application/json'
      };

      // Add auth token if available
      if (this.authToken) {
        headers['Authorization'] = `Bearer ${this.authToken}`;
      }

      // Use dynamic import for node-fetch
      const { default: fetch } = await import('node-fetch');
      
      const response = await fetch(`${this.baseUrl}/api/v1/admin/api/mcp/log-response`, {
        method: 'POST',
        headers,
        body: JSON.stringify(logData)
      } as any);

      if (response.ok) {
        return true;
      } else {
        console.warn(`Failed to log MCP response: ${response.status} ${response.statusText}`);
        return false;
      }
    } catch (error) {
      // Log error but don't fail the main operation
      console.warn(`Error logging MCP response:`, error);
      return false;
    }
  }

  /**
   * Create a wrapper function that logs both request and response
   */
  createLoggedEndpoint(endpoint: string, handler: (req: any, res: any) => Promise<void>) {
    return async (req: any, res: any) => {
      const startTime = Date.now();
      let requestId: string | null = null;
      let statusCode = 200;
      let responseData: any = null;

      try {
        // Log the incoming request
        requestId = await this.logRequest(
          endpoint,
          req.body,
          req.body?.session_id,
          req.headers.authorization
        );

        // Intercept the response to capture data and status
        const originalJson = res.json.bind(res);
        const originalStatus = res.status.bind(res);

        res.status = function(code: number) {
          statusCode = code;
          return originalStatus(code);
        };

        res.json = function(data: any) {
          responseData = data;
          return originalJson(data);
        };

        // Call the original handler
        await handler(req, res);

      } catch (error) {
        statusCode = 500;
        responseData = { error: error instanceof Error ? error.message : 'Unknown error' };
        
        // Send error response if not already sent
        if (!res.headersSent) {
          res.status(500).json(responseData);
        }
        
        console.error(`Error in ${endpoint}:`, error);
      } finally {
        // Log the response
        if (requestId && responseData) {
          await this.logResponse(requestId, responseData, statusCode);
        }

        // Log duration for debugging
        const duration = Date.now() - startTime;
        console.log(`[${new Date().toISOString()}] MCP: ${endpoint} completed in ${duration}ms (status: ${statusCode})`);
      }
    };
  }

  /**
   * Set authentication token for API calls
   */
  setAuthToken(token: string) {
    this.authToken = token;
  }

  /**
   * Enable or disable logging
   */
  setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  /**
   * Get logger status
   */
  getStatus() {
    return {
      enabled: this.enabled,
      baseUrl: this.baseUrl,
      hasAuthToken: !!this.authToken
    };
  }
}

// Export singleton instance
export const mcpLogger = new MCPLogger();