# Teams Attachment Contract

This document describes the structure of the attachment object received from Microsoft Teams for file uploads.

## Activity Structure

Incoming `Activity` containing a file attachment:

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.teams.file.download.info",
      "name": "example.pdf",
      "content": {
        "downloadUrl": "https://...",
        "uniqueId": "...",
        "fileType": "pdf",
        "etag": "..."
      }
    }
  ]
}
```

## Internal Processing Interface

The logic in `src/utils/file_handler.py` should expose an interface or function to parse these activities.

### `FileHandler.extract_attachments(activity: Activity) -> List[FileAttachmentInfo]`

- **Input**: The `Activity` object from `botbuilder-core`.
- **Output**: A list of validated file information objects.
