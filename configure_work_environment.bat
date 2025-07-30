@echo off
echo Configuring Control-UX for Work Environment...
echo.

REM Set the evidence path environment variable
echo Setting evidence path...
setx CONTROL_UX_EVIDENCE_PATH "..\..\scripts\evidence"

echo.
echo Configuration complete!
echo.
echo The API will now look for evidence in: ..\..\scripts\evidence
echo (relative to the control-ux\api directory)
echo.
echo If your scripts folder is in a different location, edit this file
echo and change the path accordingly.
echo.
pause