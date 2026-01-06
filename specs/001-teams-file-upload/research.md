# Research: Teams File Upload Implementation

## Unknowns & Clarifications

### 1. Microsoft Graph API Authentication

- **Question**: How to use the existing Service Principal (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`) to access files in a user's OneDrive?
- **Finding**: Use the Client Credentials flow. The Service Principal needs `Files.Read.All` (for all OneDrives) or `Sites.Read.All` (for SharePoint/Teams files) Application permissions.
- **Decision**: Implement a `GraphService` in `src/utils/file_handler.py` that uses `MSAL` or `requests` to get an access token.

### 2. File Retrieval from Teams

- **Question**: When a user uploads a file, Teams sends a `fileConsentAccept` event with a `downloadUrl`. Does this URL require authentication?
- **Finding**: The `downloadUrl` provided in `FileDownloadInfo` is typically a short-lived authenticated URL. However, the spec says "System MUST use the Service Principal's credentials to authenticate with Microsoft Graph API for file access." This implies we might need to use the `uniqueId` or other metadata to fetch it via Graph API if the `downloadUrl` is not sufficient or if long-term access is needed.
- **Decision**: First attempt to download via `downloadUrl`. If Graph API is required for better integration (e.g., permanent link), use the `uniqueId` to query `/drives/{drive-id}/items/{item-id}`.

### 3. File Consent Flow in Python SDK

- **Question**: How to correctly handle `fileConsentAccept` in `botbuilder-python`?
- **Finding**: Referencing `src/bot/_example.py`, we should override `on_teams_file_consent_accept` and `on_teams_file_consent_decline`.
- **Decision**: Update `BaseBot` to include these handlers, allowing child bots to override or use default behavior.

## Best Practices

- **Token Caching**: Cache the Graph API access token to avoid redundant auth calls.
- **Error Handling**: Handle `403 Forbidden` (missing permissions) and `404 Not Found` gracefully.
- **Chunked Upload/Download**: For large files, use Graph API's upload sessions/range downloads. (Initial implementation will focus on standard downloads).

## Alternatives Considered

- **Direct Download vs. Graph SDK**: `requests` is simpler for a few calls; `msgraph-sdk` is better for complex Graph operations. Since we only need download and maybe metadata, `requests` + `MSAL` is chosen for lightness.
- **Storage**: Initially, keep files in memory or temporary local storage before passing to Foundry/Genie.
