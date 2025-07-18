# How to Fix the Render Deployment

The deployment is failing because Render is trying to run a file that no longer exists. This is set by the **Start Command** in your service's settings on Render.

Follow these steps to fix it:

## Step 1: Go to your Render Dashboard

1.  Log in to your Render account.
2.  Find your service named **`ai-tutor`** in the dashboard and click on it.

## Step 2: Find the Settings Page

1.  On your service's page, look for a navigation menu on the left side.
2.  Click on the **"Settings"** link.

## Step 3: Update the Start Command

1.  Scroll down the Settings page until you find the **"Build & Deploy"** section.
2.  You will see a field labeled **"Start Command"**.
3.  The current (incorrect) value is likely `python simple-server-fixed.py` or something similar.
4.  **Delete** the old command and replace it with this exact command:
    ```
    python ai-tutor/backend/admin-server.py
    ```

## Step 4: Save and Deploy

1.  Scroll to the bottom of the page and click the **"Save Changes"** button.
2.  After saving, go back to your service's main page.
3.  Click the **"Manual Deploy"** button and choose **"Deploy latest commit"** to trigger a new deployment with the correct start command.

After this, the deployment should succeed. Please monitor the logs to confirm.