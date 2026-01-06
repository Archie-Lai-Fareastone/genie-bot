# Quickstart: Testing File Attachment Handling

This feature allows users to send files directly to the bot in Microsoft Teams.

## Prerequisites

- Access to a Microsoft Teams environment where the bot is deployed.
- A PDF, DOC, or DOCX file for testing.

## Testing Steps

1. **Open Teams Chat**: Initiate a chat with the bot.
2. **Send a Supported File**:
   - Drag and drop a PDF file into the chat.
   - Press Enter to send.
3. **Verify Response**:
   - The bot should reply with a confirmation message: "Successfully received: [filename]".
4. **Send an Unsupported File**:
   - Send a JPG or TXT file.
   - The bot should reply with a warning message: "File type not supported: [filename]. Supported types are PDF, DOC, DOCX."
5. **Send Multiple Files**:
   - Send a message with one PDF and one JPG.
   - The bot should confirm the PDF and warn about the JPG.

## Log Verification

Check the `logs/app.log` file for entries like:
`INFO - src.utils.file_handler - Received file: report.pdf from user: user@example.com`
