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

// MCP Tool: Get comprehensive student data
app.post('/mcp/get-student-context', async (req, res) => {
  try {
    const { student_id } = req.body;
    
    if (!student_id) {
      return res.status(400).json({ error: 'student_id is required' });
    }

    // Get all the student data in one call
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
        profile,
        progress,
        recent_sessions: recentSessions,
        curriculum_context: {
          grade_subjects: gradeData,
          school_type: curriculum.school_type,
          curriculum_system: curriculum.curriculum_system
        }
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

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