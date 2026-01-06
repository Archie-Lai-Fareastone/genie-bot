# Quickstart: Teams File Upload

## Prerequisites

1. **Azure AD App Registration**:

   - Ensure the Service Principal has **Application** permissions for Microsoft Graph:
     - `Files.Read.All`
   - Grant **Admin Consent** in the Azure Portal.

2. **Environment Variables**:
   Update your `.env` file with any new variables (if required, though existing `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` should suffice).

## Integration Steps

### 1. Register File Handlers

In your bot class (e.g., `FoundryBot`), ensure you are invoking the file upload prompt.

```python
# Example: Triggering a file upload prompt
await self.file_handler.send_file_consent_card(turn_context, "example.pdf")
```

### 2. Handle the Event

The `BaseBot` will automatically handle `fileConsentAccept`. If you need custom logic:

- Override `on_teams_file_consent_accept` in `foundry_bot.py`.

### 3. Accessing the File

Use the `FileHandler` utility to get the file content:

```python
content = await file_handler.download_file(download_url)
```

## Testing

1. Deploy to an Azure Web App.
2. Open Teams and start a chat with the bot.
3. Trigger a scenario that requests a file.
4. Upload the file and verify the "Success" Adaptive Card.
