# SQL-Based Storage Testing Guide

This guide provides instructions for testing the SQL-based storage implementation of the AI Tutor platform.

## Automated Testing

We've created automated tests to verify that the SQL-based storage implementation works correctly. These tests cover:

- CRUD operations for all entities (schools, curriculums, students, sessions, assessments)
- Relationships between entities
- Transcript analysis functionality

### Running the Automated Tests

To run the automated tests:

1. Navigate to the `ai-tutor/backend` directory
2. Run the following command:

```bash
python run_sql_tests.py
```

This will run all the tests and display the results. If all tests pass, the SQL-based storage implementation is working correctly.

## Manual Testing

In addition to the automated tests, you should also perform manual testing to verify that the application works correctly with SQL-based storage. Here are the key areas to test:

### 1. Database Initialization

1. Start the application with a clean database:
   ```bash
   python admin-server.py
   ```
2. Verify that the database tables are created correctly by checking the console output.

### 2. School Management

1. Navigate to the Schools page in the admin UI.
2. Create a new school:
   - Enter a name and location
   - Click "Add School"
   - Verify that the school appears in the list
3. Edit an existing school:
   - Click "Edit" next to a school
   - Change the name or location
   - Click "Update School"
   - Verify that the changes are saved
4. Delete a school:
   - Click "Delete" next to a school
   - Confirm the deletion
   - Verify that the school is removed from the list

### 3. Curriculum Management

1. Navigate to the Curriculum page in the admin UI.
2. Create a new curriculum:
   - Enter a name, grade, and subject
   - Add units and topics
   - Click "Add Curriculum"
   - Verify that the curriculum appears in the list
3. Edit an existing curriculum:
   - Click "Edit" next to a curriculum
   - Change the name, grade, subject, or content
   - Click "Update Curriculum"
   - Verify that the changes are saved
4. Delete a curriculum:
   - Click "Delete" next to a curriculum
   - Confirm the deletion
   - Verify that the curriculum is removed from the list
5. Associate a curriculum with a school:
   - Navigate to the Schools page
   - Click "Edit" next to a school
   - Select one or more curriculums
   - Click "Update School"
   - Verify that the curriculums are associated with the school

### 4. Student Management

1. Navigate to the Students page in the admin UI.
2. Create a new student:
   - Enter a name, grade, and select a school
   - Add profile information
   - Click "Add Student"
   - Verify that the student appears in the list
3. Edit an existing student:
   - Click "Edit" next to a student
   - Change the name, grade, school, or profile information
   - Click "Update Student"
   - Verify that the changes are saved
4. Delete a student:
   - Click "Delete" next to a student
   - Confirm the deletion
   - Verify that the student is removed from the list
5. View a student's profile:
   - Click "View" next to a student
   - Verify that the profile information is displayed correctly

### 5. Session Management

1. Navigate to a student's profile page.
2. Create a new session:
   - Click "Add Session"
   - Enter a date, duration, transcript, and summary
   - Click "Add Session"
   - Verify that the session appears in the list
3. Edit an existing session:
   - Click "Edit" next to a session
   - Change the date, duration, transcript, or summary
   - Click "Update Session"
   - Verify that the changes are saved
4. Delete a session:
   - Click "Delete" next to a session
   - Confirm the deletion
   - Verify that the session is removed from the list
5. View a session's details:
   - Click "View" next to a session
   - Verify that the transcript and summary are displayed correctly

### 6. Transcript Analysis

1. Navigate to a student's profile page.
2. Create a new session with a transcript.
3. Verify that the student's profile is updated with information extracted from the transcript.

### 7. Database Browser

1. Navigate to the Database Browser page in the admin UI.
2. Verify that you can browse the database tables:
   - Schools
   - Curriculums
   - Students
   - Sessions
   - Assessments
3. Verify that you can view the details of each record.

### 8. Error Handling

1. Test error handling by attempting to:
   - Create a record with invalid data
   - Update a record with invalid data
   - Delete a record that doesn't exist
   - Access a record that doesn't exist
2. Verify that appropriate error messages are displayed.

## Troubleshooting

If you encounter any issues during testing, here are some common problems and solutions:

### Database Connection Issues

- Verify that the database URL is correct in the configuration.
- Check that the database server is running.
- Ensure that the database user has the necessary permissions.

### Missing Tables

- Check the console output for any errors during table creation.
- Verify that the models are correctly defined.
- Try dropping and recreating the tables.

### Data Not Being Saved

- Check for any validation errors in the console output.
- Verify that the repositories are correctly implemented.
- Check that the database session is being committed.

### Relationship Issues

- Verify that the foreign keys are correctly defined.
- Check that the relationship properties are correctly defined.
- Ensure that related records exist before creating a record with a foreign key.

## Conclusion

By following this testing guide, you can verify that the SQL-based storage implementation of the AI Tutor platform works correctly. If you encounter any issues, please report them to the development team.