import express from 'express';
import cors from 'cors';
import path from 'path';
import fs from 'fs/promises';
import jwt from 'jsonwebtoken';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// JWT Secret - should match the one used in the Flask app
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-here';

// MCP Logging Configuration
const MCP_LOGGING_ENABLED = process.env.MCP_LOGGING_ENABLED !== 'false';
const FLASK_API_URL = process.env.FLASK_API_URL || 'http://localhost:5000';
const MCP_LOGGING_TOKEN = process.env.MCP_LOGGING_TOKEN || null;

// MCP Logging Functions
async function logMCPRequest(endpoint: string, requestData: any, sessionId?: string): Promise<string | null> {
  if (!MCP_LOGGING_ENABLED) {
    return null;
  }

  try {
    const logData = {
      endpoint,
      request_data: requestData,
      session_id: sessionId,
      token_id: undefined // Could be extracted from auth header
    };

    const headers: any = {
      'Content-Type': 'application/json'
    };

    if (MCP_LOGGING_TOKEN) {
      headers['Authorization'] = `Bearer ${MCP_LOGGING_TOKEN}`;
    }

    const fetch = (await import('node-fetch')).default;
    const response = await fetch(`${FLASK_API_URL}/api/v1/admin/api/mcp/log-request`, {
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
    console.warn(`Error logging MCP request:`, error);
    return null;
  }
}

async function logMCPResponse(requestId: string, responseData: any, statusCode: number = 200): Promise<void> {
  if (!MCP_LOGGING_ENABLED || !requestId) {
    return;
  }

  try {
    const logData = {
      request_id: requestId,
      response_data: responseData,
      http_status_code: statusCode
    };

    const headers: any = {
      'Content-Type': 'application/json'
    };

    if (MCP_LOGGING_TOKEN) {
      headers['Authorization'] = `Bearer ${MCP_LOGGING_TOKEN}`;
    }

    const fetch = (await import('node-fetch')).default;
    const response = await fetch(`${FLASK_API_URL}/api/v1/admin/api/mcp/log-response`, {
      method: 'POST',
      headers,
      body: JSON.stringify(logData)
    } as any);

    if (!response.ok) {
      console.warn(`Failed to log MCP response: ${response.status} ${response.statusText}`);
    }
  } catch (error) {
    console.warn(`Error logging MCP response:`, error);
  }
}

function createLoggedEndpoint(endpoint: string, handler: (req: express.Request, res: express.Response) => Promise<void>) {
  return async (req: express.Request, res: express.Response) => {
    const startTime = Date.now();
    let requestId: string | null = null;
    let statusCode = 200;
    let responseData: any = null;

    try {
      // Log the incoming request
      requestId = await logMCPRequest(endpoint, req.body, req.body?.session_id);

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
      
      if (!res.headersSent) {
        res.status(500).json(responseData);
      }
      
      console.error(`Error in ${endpoint}:`, error);
    } finally {
      // Log the response
      if (requestId && responseData) {
        await logMCPResponse(requestId, responseData, statusCode);
      }

      const duration = Date.now() - startTime;
      console.log(`[${new Date().toISOString()}] MCP: ${endpoint} completed in ${duration}ms (status: ${statusCode})`);
    }
  };
}

// Token validation middleware
const validateToken = (requiredScope: string) => {
  return (req: express.Request, res: express.Response, next: express.NextFunction) => {
    // Get token from Authorization header
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        error: 'No token provided'
      });
    }

    const token = authHeader.split(' ')[1];

    try {
      // Verify token
      const decoded = jwt.verify(token, JWT_SECRET) as { scopes: string[] };
      
      // Check if token has the required scope
      if (!decoded.scopes || !decoded.scopes.includes(requiredScope)) {
        return res.status(403).json({
          success: false,
          error: `Token missing required scope: ${requiredScope}`
        });
      }
      
      // Token is valid and has the required scope
      next();
    } catch (error) {
      console.error('Token validation error:', error);
      return res.status(401).json({
        success: false,
        error: 'Invalid or expired token'
      });
    }
  };
};

// Data directory path (relative to project root)
const DATA_DIR = path.join(__dirname, '../../data');

// Helper function to read JSON files
async function readJsonFile(filePath: string): Promise<any> {
  try {
    const fullPath = path.join(DATA_DIR, filePath);
    const data = await fs.readFile(fullPath, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error);
    throw new Error(`Failed to read file: ${filePath}`);
  }
}

// Helper function to read text files
async function readTextFile(filePath: string): Promise<string> {
  try {
    const fullPath = path.join(DATA_DIR, filePath);
    const data = await fs.readFile(fullPath, 'utf-8');
    return data;
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error);
    throw new Error(`Failed to read file: ${filePath}`);
  }
}

// Helper function to list files in a directory
async function listFiles(dirPath: string): Promise<string[]> {
  try {
    const fullPath = path.join(DATA_DIR, dirPath);
    const files = await fs.readdir(fullPath);
    return files;
  } catch (error) {
    console.error(`Error listing directory ${dirPath}:`, error);
    throw new Error(`Failed to list directory: ${dirPath}`);
  }
}

// MCP Tool: Get student profile
app.post('/mcp/get-student-profile', async (req, res) => {
  const startTime = Date.now();
  try {
    const { student_id } = req.body;
    
    console.log(`[${new Date().toISOString()}] MCP: get-student-profile called for student_id: ${student_id}`);
    
    if (!student_id) {
      console.log(`[${new Date().toISOString()}] MCP: get-student-profile error - student_id is required`);
      return res.status(400).json({ error: 'student_id is required' });
    }

    const profile = await readJsonFile(`students/${student_id}/profile.json`);
    
    const duration = Date.now() - startTime;
    console.log(`[${new Date().toISOString()}] MCP: get-student-profile completed for ${student_id} in ${duration}ms`);
    
    res.json({
      success: true,
      data: profile
    });
  } catch (error) {
    const duration = Date.now() - startTime;
    console.log(`[${new Date().toISOString()}] MCP: get-student-profile error for ${req.body?.student_id} in ${duration}ms: ${error instanceof Error ? error.message : 'Unknown error'}`);
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// MCP Tool: Get student progress
app.post('/mcp/get-student-progress', async (req, res) => {
  try {
    const { student_id } = req.body;
    
    if (!student_id) {
      return res.status(400).json({ error: 'student_id is required' });
    }

    const progress = await readJsonFile(`students/${student_id}/progress.json`);
    
    res.json({
      success: true,
      data: progress
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// MCP Tool: Get curriculum data
app.post('/mcp/get-curriculum', async (req, res) => {
  try {
    const { curriculum_name, grade, subject } = req.body;
    
    if (!curriculum_name) {
      return res.status(400).json({ error: 'curriculum_name is required' });
    }

    const curriculum = await readJsonFile(`curriculum/${curriculum_name}.json`);
    
    // If specific grade and subject requested, filter the data
    if (grade && subject) {
      const gradeData = curriculum.grades?.[grade];
      if (gradeData && gradeData.subjects?.[subject]) {
        return res.json({
          success: true,
          data: {
            subject_info: gradeData.subjects[subject],
            grade: grade,
            subject: subject,
            school_type: curriculum.school_type,
            curriculum_system: curriculum.curriculum_system
          }
        });
      }
    }
    
    res.json({
      success: true,
      data: curriculum
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// MCP Tool: Get session summary
app.post('/mcp/get-session-summary', async (req, res) => {
  try {
    const { student_id, session_date } = req.body;
    
    if (!student_id || !session_date) {
      return res.status(400).json({ error: 'student_id and session_date are required' });
    }

    const summary = await readJsonFile(`students/${student_id}/sessions/${session_date}_summary.json`);
    
    res.json({
      success: true,
      data: summary
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// MCP Tool: Get session transcript
app.post('/mcp/get-session-transcript', async (req, res) => {
  try {
    const { student_id, session_date } = req.body;
    
    if (!student_id || !session_date) {
      return res.status(400).json({ error: 'student_id and session_date are required' });
    }

    const transcript = await readTextFile(`students/${student_id}/sessions/${session_date}_transcript.txt`);
    
    res.json({
      success: true,
      data: transcript
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// MCP Tool: Get recent sessions
app.post('/mcp/get-recent-sessions', async (req, res) => {
  try {
    const { student_id, limit = 5 } = req.body;
    
    if (!student_id) {
      return res.status(400).json({ error: 'student_id is required' });
    }

    const sessionFiles = await listFiles(`students/${student_id}/sessions`);
    
    // Filter for summary files and sort by date (newest first)
    const summaryFiles = sessionFiles
      .filter(file => file.endsWith('_summary.json'))
      .sort((a, b) => b.localeCompare(a))
      .slice(0, limit);

    const sessions = [];
    for (const file of summaryFiles) {
      const sessionDate = file.replace('_summary.json', '');
      const summary = await readJsonFile(`students/${student_id}/sessions/${file}`);
      sessions.push({
        date: sessionDate,
        summary: summary
      });
    }
    
    res.json({
      success: true,
      data: sessions
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// MCP Tool: Get comprehensive student data (v4 context)
app.post('/mcp/get-student-context', createLoggedEndpoint('/mcp/get-student-context', async (req, res) => {
  const { student_id } = req.body;
  
  if (!student_id) {
    return res.status(400).json({ error: 'student_id is required' });
  }

  try {
    // Call the Flask API to get the v4 context from StudentContextService
    const fetch = (await import('node-fetch')).default;
    const response = await fetch(`${FLASK_API_URL}/api/v1/student-context/${student_id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    } as any);

    if (!response.ok) {
      if (response.status === 404) {
        return res.status(404).json({
          success: false,
          error: `Student not found: ${student_id}`
        });
      }
      
      const errorText = await response.text();
      throw new Error(`Flask API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const apiResponse: any = await response.json();
    
    if (!apiResponse.success) {
      throw new Error(apiResponse.error || 'Flask API returned unsuccessful response');
    }

    // Return the v4 context directly from the Flask API
    res.json({
      success: true,
      data: apiResponse.data
    });

  } catch (error) {
    console.error(`Error fetching v4 context for student ${student_id}:`, error);
    
    // Fallback to legacy behavior if Flask API is unavailable
    try {
      const profile = await readJsonFile(`students/${student_id}/profile.json`);
      const progress = await readJsonFile(`students/${student_id}/progress.json`);
      
      // Get recent sessions
      const sessionFiles = await listFiles(`students/${student_id}/sessions`);
      const recentSummaryFiles = sessionFiles
        .filter(file => file.endsWith('_summary.json'))
        .sort((a, b) => b.localeCompare(a))
        .slice(0, 3);

      const recentSessions = [];
      for (const file of recentSummaryFiles) {
        const sessionDate = file.replace('_summary.json', '');
        const summary = await readJsonFile(`students/${student_id}/sessions/${file}`);
        recentSessions.push({
          date: sessionDate,
          summary: summary
        });
      }

      // Get curriculum data based on student's grade
      const curriculum = await readJsonFile('curriculum/international_school_greece.json');
      const gradeData = curriculum.grades?.[profile.grade];
      
      res.json({
        success: true,
        data: {
          context_version: 3, // Legacy version
          profile,
          progress,
          recent_sessions: recentSessions,
          curriculum_context: {
            grade_subjects: gradeData,
            school_type: curriculum.school_type,
            curriculum_system: curriculum.curriculum_system
          },
          _fallback_note: 'Using legacy context due to Flask API unavailability'
        }
      });
    } catch (fallbackError) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }
}));

// MCP Tool: Get comprehensive VAPI context by phone number
app.post('/mcp/get-vapi-context', async (req, res) => {
  const startTime = Date.now();
  try {
    const { phone_number, call_type = 'tutoring' } = req.body;
    
    console.log(`[${new Date().toISOString()}] MCP: get-vapi-context called for phone: ${phone_number}, call_type: ${call_type}`);
    
    if (!phone_number) {
      console.log(`[${new Date().toISOString()}] MCP: get-vapi-context error - phone_number is required`);
      return res.status(400).json({ error: 'phone_number is required' });
    }

    // Load phone mapping to find student
    let phoneMapping;
    let student_id = null;
    
    try {
      phoneMapping = await readJsonFile('phone_mapping.json');
      student_id = phoneMapping.phone_to_student?.[phone_number];
    } catch (error) {
      console.log(`[${new Date().toISOString()}] MCP: Phone mapping not found, treating as first call`);
    }

    // Load school information (enhanced with rich context)
    let schoolData;
    try {
      schoolData = await readJsonFile('schools/school_data.json');
    } catch (error) {
      console.log(`[${new Date().toISOString()}] MCP: Could not load school data: ${error.message}`);
      schoolData = { schools: [] };
    }

    // Default school (International School of Greece)
    const defaultSchool = schoolData.schools?.find(s => s.school_id === 'international_school_greece') || {
      school_id: 'international_school_greece',
      name: 'International School of Greece',
      location: 'Athens, Greece',
      background: 'A prestigious international school offering a blend of Greek and international curriculum for students from diverse backgrounds.',
      curriculum_type: 'International Baccalaureate'
    };

    // If no student found (first call scenario)
    if (!student_id) {
      const duration = Date.now() - startTime;
      console.log(`[${new Date().toISOString()}] MCP: get-vapi-context first call scenario for ${phone_number} in ${duration}ms`);
      
      return res.json({
        success: true,
        data: {
          is_first_call: true,
          phone_number: phone_number,
          call_type: call_type,
          school_context: {
            info: defaultSchool,
            enhanced_info: defaultSchool.enhanced_info || {},
            message: "Welcome to our AI tutoring system! This appears to be your first call."
          },
          curriculum_overview: {
            available_grades: ['1', '2', '3', '4', '5', '6'],
            main_subjects: ['mathematics', 'english', 'science', 'modern_greek_language'],
            curriculum_system: 'Cambridge Primary + Greek National Requirements',
            approach: 'Personalized learning adapted to each student\'s interests and learning style'
          },
          session_guidance: {
            first_call_approach: 'Introduction and assessment',
            recommended_duration: '20-30 minutes',
            focus_areas: ['getting to know the student', 'identifying interests', 'assessing current level', 'explaining how the tutoring works'],
            next_steps: 'After this call, we\'ll create a personalized learning profile for future sessions'
          }
        }
      });
    }

    // Student found - get comprehensive context
    const profile = await readJsonFile(`students/${student_id}/profile.json`);
    let progress = null;
    let recentSessions = [];
    
    try {
      progress = await readJsonFile(`students/${student_id}/progress.json`);
    } catch (error) {
      console.log(`[${new Date().toISOString()}] MCP: No progress file for ${student_id}`);
    }

    // Get recent sessions
    try {
      const sessionFiles = await listFiles(`students/${student_id}/sessions`);
      const recentSummaryFiles = sessionFiles
        .filter(file => file.endsWith('_summary.json'))
        .sort((a, b) => b.localeCompare(a))
        .slice(0, 3);

      for (const file of recentSummaryFiles) {
        const sessionDate = file.replace('_summary.json', '');
        const summary = await readJsonFile(`students/${student_id}/sessions/${file}`);
        recentSessions.push({
          date: sessionDate,
          summary: summary
        });
      }
    } catch (error) {
      console.log(`[${new Date().toISOString()}] MCP: No sessions found for ${student_id}`);
    }

    // Get curriculum data based on student's grade and school
    let curriculumContext = {};
    try {
      const curriculum = await readJsonFile('curriculum/international_school_greece.json');
      const gradeData = curriculum.grades?.[profile.student_info?.grade?.toString()];
      
      curriculumContext = {
        grade_subjects: gradeData,
        school_type: curriculum.school_type,
        curriculum_system: curriculum.curriculum_system,
        learning_goals: curriculum.learning_goals_by_subject || {}
      };
    } catch (error) {
      console.log(`[${new Date().toISOString()}] MCP: Could not load curriculum for ${student_id}`);
    }

    const duration = Date.now() - startTime;
    console.log(`[${new Date().toISOString()}] MCP: get-vapi-context completed for ${student_id} (${phone_number}) in ${duration}ms`);
    
    res.json({
      success: true,
      data: {
        is_first_call: false,
        phone_number: phone_number,
        student_id: student_id,
        call_type: call_type,
        student_context: {
          profile: profile,
          progress: progress,
          recent_sessions: recentSessions,
          session_count: recentSessions.length
        },
        school_context: {
          info: defaultSchool,
          enhanced_info: defaultSchool.enhanced_info || {}
        },
        curriculum_context: curriculumContext,
        tutoring_guidance: {
          optimal_duration: profile.session_preferences?.optimal_duration || '30-40 minutes',
          attention_span: profile.session_preferences?.attention_span || '10-15 minutes',
          preferred_rewards: profile.session_preferences?.preferred_rewards || [],
          key_strategies: profile.practical_session_guidance?.map(g => ({
            strategy: g.strategy,
            implementation: g.implementation
          })) || [],
          areas_for_growth: profile.areas_for_growth || [],
          motivational_triggers: profile.key_takeaways?.motivational_triggers || {}
        }
      }
    });
  } catch (error) {
    const duration = Date.now() - startTime;
    console.log(`[${new Date().toISOString()}] MCP: get-vapi-context error for ${req.body?.phone_number} in ${duration}ms: ${error instanceof Error ? error.message : 'Unknown error'}`);
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// MCP Tool: Get school information with enhanced details
app.post('/mcp/get-school-info', async (req, res) => {
  try {
    const { school_id = 'international_school_greece' } = req.body;
    
    const schoolData = await readJsonFile('schools/school_data.json');
    const school = schoolData.schools?.find(s => s.school_id === school_id);
    
    if (!school) {
      return res.status(404).json({
        success: false,
        error: `School not found: ${school_id}`
      });
    }
    
    res.json({
      success: true,
      data: school
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// MCP Tool: Set game state
app.post('/mcp/set-game-state', createLoggedEndpoint('/mcp/set-game-state', async (req, res) => {
  const { student_id, game_id, json_blob, is_active } = req.body;
  
  if (!student_id || !game_id || json_blob === undefined) {
    return res.status(400).json({
      success: false,
      error: 'student_id, game_id, and json_blob are required'
    });
  }

  try {
    const fetch = (await import('node-fetch')).default;
    const response = await fetch(`${FLASK_API_URL}/api/v1/students/${student_id}/game-state`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        game_id,
        json_blob,
        is_active: is_active !== undefined ? is_active : true
      })
    } as any);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Flask API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const apiResponse: any = await response.json();
    
    res.json({
      success: true,
      data: apiResponse.data || { message: 'Game state updated successfully' }
    });

  } catch (error) {
    console.error(`Error setting game state for student ${student_id}:`, error);
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}));

// MCP Tool: Set memory
app.post('/mcp/set-memory', createLoggedEndpoint('/mcp/set-memory', async (req, res) => {
  const { student_id, key, value, scope } = req.body;
  
  if (!student_id || !key || value === undefined) {
    return res.status(400).json({
      success: false,
      error: 'student_id, key, and value are required'
    });
  }

  // Validate scope if provided
  const validScopes = ['personal_fact', 'game_state', 'strategy_log'];
  if (scope && !validScopes.includes(scope)) {
    return res.status(400).json({
      success: false,
      error: `Invalid scope. Must be one of: ${validScopes.join(', ')}`
    });
  }

  try {
    const fetch = (await import('node-fetch')).default;
    const response = await fetch(`${FLASK_API_URL}/api/v1/students/${student_id}/memory`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        key,
        value,
        scope: scope || 'personal_fact' // Default scope
      })
    } as any);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Flask API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const apiResponse: any = await response.json();
    
    res.json({
      success: true,
      data: apiResponse.data || { message: 'Memory updated successfully' }
    });

  } catch (error) {
    console.error(`Error setting memory for student ${student_id}:`, error);
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}));

// MCP Tool: Log session event
app.post('/mcp/log-session-event', createLoggedEndpoint('/mcp/log-session-event', async (req, res) => {
  const { student_id, event_json } = req.body;
  
  if (!student_id || !event_json) {
    return res.status(400).json({
      success: false,
      error: 'student_id and event_json are required'
    });
  }

  try {
    const fetch = (await import('node-fetch')).default;
    const response = await fetch(`${FLASK_API_URL}/api/v1/students/${student_id}/session-events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        event_data: event_json,
        timestamp: new Date().toISOString()
      })
    } as any);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Flask API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const apiResponse: any = await response.json();
    
    res.json({
      success: true,
      data: apiResponse.data || { message: 'Session event logged successfully' }
    });

  } catch (error) {
    console.error(`Error logging session event for student ${student_id}:`, error);
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// MCP Tool: Get system logs
app.post('/mcp/get-system-logs', validateToken('logs:read'), async (req, res) => {
  try {
    const { date, level, limit = 100, category } = req.body;
    const days = req.body.days || 7;
    
    // Get the token from the request
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        error: 'No token provided'
      });
    }
    
    const token = authHeader.split(' ')[1];
    
    // Make a request to the admin server API
    const apiUrl = new URL('http://localhost:5000/api/v1/logs');
    
    // Add query parameters
    if (date) apiUrl.searchParams.append('date', date);
    if (level) apiUrl.searchParams.append('level', level);
    if (category) apiUrl.searchParams.append('category', category);
    if (days) apiUrl.searchParams.append('days', days.toString());
    if (limit) apiUrl.searchParams.append('limit', limit.toString());
    
    try {
      // Use node-fetch to make the request
      const fetch = (await import('node-fetch')).default;
      const response = await fetch(apiUrl.toString(), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API request failed: ${response.status} ${response.statusText} - ${errorText}`);
      }
      
      const apiResponse = await response.json();
      
      // Return the API response directly
      return res.json(apiResponse);
      
    } catch (error) {
      console.error('Error fetching logs from API:', error);
      
      // Fallback to empty logs if API is unavailable
      return res.json({
        success: true,
        data: {
          count: 0,
          logs: [],
          message: `Could not fetch logs from API: ${error instanceof Error ? error.message : 'Unknown error'}`
        }
      });
    }
  } catch (error) {
    console.error('Error retrieving system logs:', error);
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Add the new tool to the tools manifest
app.get('/mcp/tools', (req, res) => {
  res.json({
    tools: [
      {
        name: 'get-vapi-context',
        description: 'VAPI-OPTIMIZED: Get comprehensive context for VAPI calls including student data, school info, curriculum, and tutoring guidance. Handles both existing students and first-call scenarios using phone number lookup.',
        inputSchema: {
          type: 'object',
          properties: {
            phone_number: {
              type: 'string',
              description: 'The phone number used to identify the student (e.g., "+12345678901")'
            },
            call_type: {
              type: 'string',
              description: 'Type of call: "tutoring", "assessment", "introduction" (default: "tutoring")'
            }
          },
          required: ['phone_number']
        }
      },
      {
        name: 'get-school-info',
        description: 'Get comprehensive school information including mission, values, teaching philosophy, and programs',
        inputSchema: {
          type: 'object',
          properties: {
            school_id: {
              type: 'string',
              description: 'School identifier (default: "international_school_greece")'
            }
          }
        }
      },
      {
        name: 'get-student-profile',
        description: 'Get detailed profile information for a student including personality, interests, and learning preferences',
        inputSchema: {
          type: 'object',
          properties: {
            student_id: {
              type: 'string',
              description: 'The unique identifier for the student (e.g., "emma_smith")'
            }
          },
          required: ['student_id']
        }
      },
      {
        name: 'get-student-progress',
        description: 'Get current progress assessment for a student across all subjects',
        inputSchema: {
          type: 'object',
          properties: {
            student_id: {
              type: 'string',
              description: 'The unique identifier for the student'
            }
          },
          required: ['student_id']
        }
      },
      {
        name: 'get-curriculum',
        description: 'Get curriculum requirements and learning goals for a specific grade and subject',
        inputSchema: {
          type: 'object',
          properties: {
            curriculum_name: {
              type: 'string',
              description: 'Name of the curriculum file (e.g., "international_school_greece")'
            },
            grade: {
              type: 'string',
              description: 'Grade level (optional, for filtering)'
            },
            subject: {
              type: 'string',
              description: 'Subject name (optional, for filtering)'
            }
          },
          required: ['curriculum_name']
        }
      },
      {
        name: 'get-session-summary',
        description: 'Get detailed summary and analysis of a specific tutoring session',
        inputSchema: {
          type: 'object',
          properties: {
            student_id: {
              type: 'string',
              description: 'The unique identifier for the student'
            },
            session_date: {
              type: 'string',
              description: 'Date of the session in YYYY-MM-DD format'
            }
          },
          required: ['student_id', 'session_date']
        }
      },
      {
        name: 'get-session-transcript',
        description: 'Get the full conversation transcript from a specific tutoring session',
        inputSchema: {
          type: 'object',
          properties: {
            student_id: {
              type: 'string',
              description: 'The unique identifier for the student'
            },
            session_date: {
              type: 'string',
              description: 'Date of the session in YYYY-MM-DD format'
            }
          },
          required: ['student_id', 'session_date']
        }
      },
      {
        name: 'get-recent-sessions',
        description: 'Get summaries of recent tutoring sessions for a student',
        inputSchema: {
          type: 'object',
          properties: {
            student_id: {
              type: 'string',
              description: 'The unique identifier for the student'
            },
            limit: {
              type: 'number',
              description: 'Maximum number of recent sessions to retrieve (default: 5)'
            }
          },
          required: ['student_id']
        }
      },
      {
        name: 'get-student-context',
        description: 'Get comprehensive context for a student including profile, progress, recent sessions, and relevant curriculum data',
        inputSchema: {
          type: 'object',
          properties: {
            student_id: {
              type: 'string',
              description: 'The unique identifier for the student'
            }
          },
          required: ['student_id']
        }
      },
      {
        name: 'get-system-logs',
        description: 'Get system logs for debugging and testing purposes (requires logs:read scope)',
        inputSchema: {
          type: 'object',
          properties: {
            date: {
              type: 'string',
              description: 'Date of logs to retrieve in YYYY-MM-DD format (defaults to current date)'
            },
            level: {
              type: 'string',
              description: 'Log level to filter by (e.g., "ERROR", "INFO", "WARNING")'
            },
            limit: {
              type: 'number',
              description: 'Maximum number of log entries to retrieve (default: 100)'
            }
          }
        }
      },
      {
        name: 'set-game-state',
        description: 'Set or update game state data for a student. Used by VAPI to persist game progress and state.',
        inputSchema: {
          type: 'object',
          properties: {
            student_id: {
              type: 'string',
              description: 'The unique identifier for the student'
            },
            game_id: {
              type: 'string',
              description: 'Identifier for the specific game or activity'
            },
            json_blob: {
              type: 'object',
              description: 'JSON object containing the game state data'
            },
            is_active: {
              type: 'boolean',
              description: 'Whether this game state is currently active (default: true)'
            }
          },
          required: ['student_id', 'game_id', 'json_blob']
        }
      },
      {
        name: 'set-memory',
        description: 'Set or update a memory item for a student with scoped storage. Used by VAPI to remember facts, strategies, and game state.',
        inputSchema: {
          type: 'object',
          properties: {
            student_id: {
              type: 'string',
              description: 'The unique identifier for the student'
            },
            key: {
              type: 'string',
              description: 'The memory key/identifier'
            },
            value: {
              type: 'string',
              description: 'The memory value to store'
            },
            scope: {
              type: 'string',
              description: 'Memory scope: "personal_fact", "game_state", or "strategy_log" (default: "personal_fact")',
              enum: ['personal_fact', 'game_state', 'strategy_log']
            }
          },
          required: ['student_id', 'key', 'value']
        }
      },
      {
        name: 'log-session-event',
        description: 'Log a session event for tracking and analysis. Used by VAPI to record important session moments.',
        inputSchema: {
          type: 'object',
          properties: {
            student_id: {
              type: 'string',
              description: 'The unique identifier for the student'
            },
            event_json: {
              type: 'object',
              description: 'JSON object containing the event data to log'
            }
          },
          required: ['student_id', 'event_json']
        }
      }
    ]
  });
});

app.listen(PORT, () => {
  console.log(`AI Tutor MCP Server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Tools manifest: http://localhost:${PORT}/mcp/tools`);
  console.log(`Data directory: ${DATA_DIR}`);
});