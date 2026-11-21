@echo off
chcp 65001 >nul
cd /d "%~dp0scraper"

if /i "%1"=="review" (
  uv run python -m scraper review
  goto :end
)
if /i "%1"=="add-price" (
  shift
  uv run python -m scraper add-price %1 %2 %3 %4 %5 %6 %7 %8 %9
  goto :end
)

uv run python -m scraper update %*

:end
echo.
pause
