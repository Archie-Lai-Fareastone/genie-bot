# Quickstart: Testing File Attachment Handling

This feature allows users to send files directly to the bot in Microsoft Teams.

## Prerequisites

- Access to a Microsoft Teams environment where the bot is deployed.
- A PDF, DOC, or DOCX file for testing.

## Testing Steps

### Test 1: Send a Supported File

1. **Open Teams Chat**: Initiate a chat with the bot.
2. **Send a Supported File**:
   - Drag and drop a PDF file into the chat.
   - Press Enter to send.
3. **Verify Response**:
   - The bot should reply with a confirmation message: "Successfully received: [filename]".
   - Example: "Successfully received: report.pdf"

### Test 2: Send an Unsupported File

1. **Send an Unsupported File**:
   - Send a JPG or TXT file.
2. **Verify Response**:
   - The bot should reply with a warning message: "File type not supported: [filename]. Supported types are PDF, DOC, DOCX."
   - Example: "File type not supported: image.jpg. Supported types are PDF, DOC, DOCX."

### Test 3: Send Multiple Files

1. **Send Multiple Files**:
   - Send a message with one PDF and one JPG.
2. **Verify Response**:
   - The bot should confirm the PDF: "Successfully received: document.pdf"
   - The bot should warn about the JPG: "File type not supported: image.jpg. Supported types are PDF, DOC, DOCX."

### Test 4: Send File with Text Message

1. **Send File with Text**:
   - Send a PDF file along with a text message (e.g., "Please analyze this document").
2. **Verify Response**:
   - The bot should first confirm the file: "Successfully received: document.pdf"
   - The bot should then process the text message normally.

## Log Verification

Check the `logs/app.log` file for entries like:

```
INFO - src.utils.file_handler - Received file: report.pdf from user: <user-id>
WARNING - src.utils.file_handler - Unsupported file type: image.jpg (type: jpg)
```

## Implementation Details

The file attachment handling is implemented in:

- **File Handler**: `src/utils/file_handler.py` - Contains the core logic for extraction, validation, and logging
- **Bot Integration**: `src/bot/foundry_bot.py` - Integrates file handling into the message processing flow

### Supported File Types

- **PDF**: `.pdf` (application/pdf)
- **DOC**: `.doc` (application/msword)
- **DOCX**: `.docx` (application/vnd.openxmlformats-officedocument.wordprocessingml.document)

### Processing Flow

1. **Extract**: Bot extracts file metadata from Teams message activity
2. **Validate**: Check if file type is supported (PDF, DOC, DOCX)
3. **Log**: Record successful file reception with user information
4. **Respond**: Send confirmation or error message to user
