# Curriculum Database Migration Guide

## Overview
This guide explains how to deploy the database schema migration to fix the curriculum loading issue on render.com production environment.

## Problem Summary
The curriculum page was showing "0 Total Curriculums" and "⚠️ No Default Curriculum" because of a database schema mismatch. The production PostgreSQL database has curriculum tables but is missing critical columns that our updated models expect.

**Root Error:** `(psycopg2.errors.UndefinedColumn) column curriculums.name does not exist`

## Solution
We've created comprehensive migration scripts to update the database schema to match our updated Curriculum, Subject, and CurriculumDetail models.

## Deployment Steps on Render.com

### Step 1: Verify Code Deployment
The schema fixes and migration scripts have been pushed to the main branch:
- ✅ Updated curriculum models with all required fields
- ✅ Created `migrate_curriculum_schema.py` - comprehensive migration script
- ✅ Created `run_migration.py` - simple deployment script

### Step 2: Run Migration on Render.com

#### Option A: Via Render.com Shell (Recommended)
1. Go to your render.com dashboard
2. Open your AI Tutor service
3. Click on "Shell" to access the production environment
4. Navigate to the backend directory:
   ```bash
   cd ai-tutor/backend
   ```
5. Run the migration:
   ```bash
   python run_migration.py
   ```

#### Option B: Direct Migration Script
If Option A doesn't work, run the migration script directly:
```bash
cd ai-tutor/backend
python migrate_curriculum_schema.py
```

### Step 3: Expected Migration Output
You should see output similar to:
```
🚀 Starting curriculum schema migration...
✓ Database connection successful
Migrating curriculums table...
✓ Successfully added name to curriculums
✓ Successfully added curriculum_type to curriculums
✓ Successfully added grade_levels to curriculums
... (more column additions)
✓ curriculums table migration completed
✓ subjects table migration completed  
✓ curriculum_details table migration completed
✓ Table creation check completed
🎉 Curriculum schema migration completed successfully!
```

### Step 4: Restart the Application
After successful migration:
1. Go back to your render.com dashboard
2. Click "Manual Deploy" or restart the service to reload the application
3. This ensures the application picks up the new schema

### Step 5: Verify the Fix
1. Visit your admin dashboard: `https://your-app.onrender.com/admin`
2. Navigate to the Curriculum page
3. You should now see:
   - Correct curriculum count (instead of "0 Total Curriculums")
   - "✅ Default Curriculum: Cambridge Primary 2025" (instead of warning)
   - Cambridge curriculum data properly loaded

## Migration Script Details

### What the Migration Does
The migration script safely adds these missing columns:

**curriculums table:**
- `name` VARCHAR(100) - Curriculum name
- `description` TEXT - Curriculum description  
- `curriculum_type` VARCHAR(50) - Type (e.g., 'Cambridge', 'IB')
- `grade_levels` JSON - Array of supported grade levels
- `is_template` BOOLEAN - Template vs school-specific
- `created_by` VARCHAR(50) - Creator identifier
- `created_at` TIMESTAMP - Creation timestamp
- `updated_at` TIMESTAMP - Last update timestamp

**subjects table:**
- `name` VARCHAR(100) - Subject name
- `description` TEXT - Subject description
- `category` VARCHAR(50) - Subject category 
- `is_core` BOOLEAN - Core vs elective subject
- `created_at` TIMESTAMP - Creation timestamp

**curriculum_details table:**
- `learning_objectives` JSON - Learning objectives array
- `assessment_criteria` JSON - Assessment criteria array
- `recommended_hours_per_week` INTEGER - Weekly hour recommendation
- `prerequisites` JSON - Prerequisites array
- `resources` JSON - Resources array
- `goals_description` TEXT - Learning goals description
- Plus foreign key and constraint columns

### Safety Features
- ✅ Checks if columns already exist before adding them
- ✅ Safe column addition (won't break existing data)
- ✅ Comprehensive error handling and logging
- ✅ Creates missing tables if needed
- ✅ Database connection validation

## Troubleshooting

### If Migration Fails
1. Check the error output from the migration script
2. Verify DATABASE_URL environment variable is set correctly
3. Ensure the PostgreSQL database is accessible
4. Contact support if database permissions issues occur

### If Curriculum Still Shows Zero
1. Check the application logs for any remaining errors
2. Verify the Cambridge curriculum data file exists: `ai-tutor/data/curriculum/cambridge_primary_2025.txt`
3. Restart the application to force curriculum reload
4. Check that the default curriculum loading logic runs on startup

### Migration Success Checklist
- [ ] Migration script completed without errors
- [ ] Application restarted successfully
- [ ] Curriculum page shows correct statistics
- [ ] Cambridge Primary 2025 appears as default curriculum
- [ ] No more "column does not exist" errors in logs

## Files Changed
- `ai-tutor/backend/app/models/curriculum.py` - Updated model schemas
- `ai-tutor/backend/migrate_curriculum_schema.py` - Migration script
- `ai-tutor/backend/run_migration.py` - Deployment helper script

## Post-Migration
Once the migration is successful, the Cambridge Primary 2025 curriculum (49 subjects across grades 1-6) will be automatically loaded and students will be properly assigned to the default curriculum.

The curriculum management system is now fully operational with comprehensive CRUD functionality for managing curriculums, subjects, and curriculum details.