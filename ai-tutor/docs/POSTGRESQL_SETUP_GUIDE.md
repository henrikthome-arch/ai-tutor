# PostgreSQL Database Setup on Render

This guide walks you through setting up a managed PostgreSQL database on Render.com and configuring the AI Tutor application to use it.

## Step 1: Create a PostgreSQL Database on Render

1. Log in to your [Render Dashboard](https://dashboard.render.com/)
2. Click on the **"New +"** button and select **"PostgreSQL"**
3. Fill in the database details:
   - **Name**: `ai-tutor-db` (or your preferred name)
   - **Database**: `ai_tutor` (this will be your database name)
   - **User**: Leave as default (Render will generate a secure username)
   - **Region**: Choose the same region as your web service for best performance
   - **PostgreSQL Version**: 14 (or latest available)
   - **Plan Type**: Free (or select a paid plan for production use)

4. Click **"Create Database"**

## Step 2: Get Database Connection Details

After your database is created (this may take a few minutes), you'll see a page with your database connection details:

1. Note the following information:
   - **Internal Database URL**: For connecting from other Render services
   - **External Database URL**: For connecting from outside Render
   - **PSQL Command**: For connecting via command line

2. The database URL will be in this format:
   ```
   postgres://user:password@host:port/database
   ```

## Step 3: Update Environment Variables

1. Go to your AI Tutor web service in the Render dashboard
2. Navigate to the **"Environment"** tab
3. Add the following environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the **Internal Database URL** from Step 2

4. If your database URL starts with `postgres://`, you need to change it to `postgresql://` for SQLAlchemy compatibility:
   ```
   # Change this:
   postgres://user:password@host:port/database
   
   # To this:
   postgresql://user:password@host:port/database
   ```

5. Click **"Save Changes"**

## Step 4: Update Production Environment File

Update your local `ai-tutor/config/render-production.env` file to include the database URL:

```
# Add this line to render-production.env
DATABASE_URL=postgresql://user:password@host:port/database
```

Replace the placeholder with your actual database URL.

## Step 5: Run Database Migrations

When you deploy your application to Render, you need to run database migrations to create the tables. Add this to your build command in the Render dashboard:

1. Go to your web service settings
2. Update the **Build Command**:
   ```
   pip install -r requirements.txt && python -m flask db upgrade
   ```

3. Click **"Save Changes"**

## Step 6: Deploy Your Application

1. Trigger a new deployment by clicking **"Manual Deploy"** > **"Clear build cache & deploy"**
2. Wait for the deployment to complete
3. Check the logs to ensure the migrations ran successfully

## Step 7: Verify Database Connection

1. Access your application's health check endpoint:
   ```
   https://your-app-name.onrender.com/health
   ```

2. If everything is working correctly, you should see:
   ```json
   {"status": "healthy"}
   ```

## Troubleshooting

If you encounter database connection issues:

1. **Check Environment Variables**: Ensure the `DATABASE_URL` is correctly set
2. **Check Database Status**: Verify the database is active in the Render dashboard
3. **Check Logs**: Review the application logs for any database-related errors
4. **Test Connection**: Use the PSQL command provided by Render to test the connection directly

## Database Management

- **Backups**: Render automatically creates daily backups for your database
- **Scaling**: You can upgrade your database plan as your needs grow
- **Monitoring**: Use the Render dashboard to monitor database performance

Your AI Tutor application is now using a managed PostgreSQL database on Render!