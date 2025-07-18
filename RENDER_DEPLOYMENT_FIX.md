# Render.com Deployment Troubleshooting Guide

This guide will walk you through the necessary steps to diagnose and fix the persistent student recognition issue. The root cause is not in the Python code, but in the Render.com deployment environment configuration.

## Step 1: Verify Persistent Storage (Crucial)

The most likely cause of this issue is that the `phone_mapping.json` file is being erased on every deploy. This happens when the data directory is not configured as a persistent disk.

1.  Go to your **Render Dashboard** and select your AI Tutor service.
2.  Navigate to the **"Disks"** section in the sidebar.
3.  **Verify** that you have a disk configured with the following settings:
    *   **Mount Path:** `ai-tutor/data`
    *   **Size:** At least 1 GB (or your chosen size).
4.  **If there is no disk configured**, this is the problem. You **must** create one:
    *   Click **"New Disk"**.
    *   Set the **Name** to something descriptive (e.g., `ai-tutor-data`).
    *   Set the **Mount Path** to `ai-tutor/data`. **This must be exact.**
    *   Choose a size and click **"Create Disk"**.
5.  After creating the disk, you **must trigger a new deploy** for the change to take effect.

## Step 2: Clear Build Cache and Manually Deploy

Even with a persistent disk, Render might be using a stale build cache. We need to force a clean build to ensure all of my latest code fixes are included.

1.  In your service's dashboard, go to the **"Manual Deploy"** section.
2.  Select the **`main`** branch.
3.  **Crucially, click the "Clear build cache" option.**
4.  Click **"Deploy latest commit"**.

## Step 3: Run the Definitive Test

After the new deployment is live, we will perform a final test to confirm the fix.

1.  Wait for the deployment to complete successfully.
2.  **Do not place a test call yet.**
3.  Access your admin dashboard and manually add your phone number and a test student ID to the phone mappings.
4.  **Trigger another manual deploy**, again with the **"Clear build cache"** option enabled.
5.  Once the second deployment is complete, access the admin dashboard again.
    *   **If your phone number mapping is still there**, the persistent disk is working. Proceed to place a test call. The issue should now be resolved.
    *   **If your phone number mapping is gone**, the disk is still not configured correctly. Please double-check the mount path and contact Render support if necessary.

Following these steps will resolve the environmental issues and allow the corrected code to function as designed.