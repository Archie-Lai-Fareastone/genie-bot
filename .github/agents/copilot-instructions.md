# genie-bot Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-06

## Active Technologies
- Python 3.10+ (as indicated by `requirements.txt`) + `botbuilder-core`, `botbuilder-schema`, `botbuilder-integration-aiohttp` (001-teams-file-upload)
- N/A (requirements explicitly state to remove upload state recording) (001-teams-file-upload)

- Python 3.12+ + `botbuilder-core`, `botbuilder-schema`, `msgraph-sdk-python` (or `requests` for Graph API), `fastapi` (001-teams-file-upload)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.12+: Follow standard conventions

## Recent Changes
- 001-teams-file-upload: Added Python 3.10+ (as indicated by `requirements.txt`) + `botbuilder-core`, `botbuilder-schema`, `botbuilder-integration-aiohttp`

- 001-teams-file-upload: Added Python 3.12+ + `botbuilder-core`, `botbuilder-schema`, `msgraph-sdk-python` (or `requests` for Graph API), `fastapi`

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
