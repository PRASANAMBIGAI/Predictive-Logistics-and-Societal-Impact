@echo off
echo ==========================================
echo   GitHub Auto-Push Workflow
echo ==========================================

:: Stage all changes
git add .
echo [1/3] All changes staged.

:: Prompt for commit message
set /p commit_msg="Enter your commit message: "
if "%commit_msg%"=="" set commit_msg="Automated update"

:: Commit the changes
git commit -m "%commit_msg%"
echo [2/3] Changes committed locally.

:: Push to remote repository
git push origin main
echo [3/3] Changes pushed to GitHub successfully!

echo ==========================================
echo   Vercel will now automatically deploy!
echo ==========================================
pause
