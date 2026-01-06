# Implementation Plan: Teams File Upload

**Branch**: `001-teams-file-upload` | **Date**: 2026-01-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-teams-file-upload/spec.md`

## Summary

本功能旨在讓使用者能透過 Teams 上傳檔案（儲存於 OneDrive），並讓機器人透過 Service Principal 取得 Microsoft Graph API 的讀取權限來存取這些檔案。預計將上傳邏輯抽象化至共用模組，使 `FoundryBot` 及未來其他機器人皆可使用。

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: `botbuilder-core`, `botbuilder-schema`, `msgraph-sdk-python` (or `requests` for Graph API), `fastapi`  
**Storage**: OneDrive (User-side), Local temporary storage (if needed for processing)  
**Testing**: `pytest`  
**Target Platform**: Azure Web App, Microsoft Teams  
**Project Type**: Python Bot Service  
**Performance Goals**: 反饋 Adaptive Card 需在 3 秒內送達。  
**Constraints**: 使用 Service Principal 進行驗證，需處理 `fileConsentAccept` 與 `fileConsentDecline` 事件。  
**Scale/Scope**: 支援多個檔案上傳。

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

| Gate              | Status | Rationale                                        |
| ----------------- | ------ | ------------------------------------------------ |
| Code Quality      | PASS   | 將檔案處理邏輯移至共用模組符合「可維護性」原則。 |
| Testing Standards | PASS   | 需包含針對 `file_handler` 的單元測試。           |
| User Experience   | PASS   | 使用 Adaptive Card 提供即時反饋符合一致性。      |
| Performance       | PASS   | 目標響應時間設定為 3 秒內。                      |

## Project Structure

### Documentation (this feature)

```text
specs/001-teams-file-upload/
├── plan.md              # This file
├── research.md          # 關於 Graph API 驗證與檔案下載的研究
├── data-model.md        # 檔案中繼資料物件定義
├── quickstart.md        # 如何設定 Service Principal 權限與測試
└── contracts/           # 定義內部 API 或訊息格式
```

### Source Code (repository root)

```text
src/
├── bot/
│   ├── base_bot.py         # 擴充以支援檔案事件處理
│   └── foundry_bot.py      # 實作具體的檔案處理觸發器
├── core/
│   └── settings.py         # 新增 Graph API 相關設定
├── utils/
│   └── file_handler.py     # (NEW) 封裝 Graph API 與檔案下載邏輯
│   └── card_builder.py     # 擴充以支援檔案上傳反饋卡片
```

**Structure Decision**: 採用單一專案結構。建立新的 `src/utils/file_handler.py` 來處理共享邏輯，並在 `base_bot.py` 中處理 Teams 特有的 Invoke 活動。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation                  | Why Needed         | Simpler Alternative Rejected Because |
| -------------------------- | ------------------ | ------------------------------------ |
| [e.g., 4th project]        | [current need]     | [why 3 projects insufficient]        |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient]  |
