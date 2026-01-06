### 程式碼審查

- 阻斷：fileConsentAccept 仍無法取得使用者檔案內容。on_teams_file_consent_accept() 只把 upload_info.content_url 當成下載來源，直接呼叫 download_file()，整個流程完全沒有把任何檔案寫入 Teams 給的 upload_url。base_bot.py:95-169 與 file_handler.py:193-249 可見僅回傳 UploadedFile 後就嘗試下載；而專案附帶的官方樣板 \_example.py:93-152 明確示範必須先 PUT 至 upload_info.upload_url，Teams 才會產生可下載的 content_url。目前根本沒有任何地方上傳或接收真實檔案，因此 FR-002 ～ FR-004 和 SC-001（spec.md:51-69）仍未達成，使用者無法依 User Story 1/2 完成檔案分享。
- 主要：批次完成條件被硬編成「必須收到 5 份同意」，使用者只要少按一次「接受」就永遠拿不到確認卡。\_handle_upload_command() 把 expected_files 固定成 5，送出 5 張卡片後沒有任何機制把預期數量調整為實際需求或在超時時結案。command_handler.py:128-154 與 file_handler.py:358-386 顯示只有當 len(received_files) >= expected_files 才會送出成功卡；若使用者只需上傳 1~2 份、或中途拒絕某張卡，整批就永遠卡在 pending，直接違反 User Story 1 與 SC-002 要求「收到最後一份檔案後 3 秒內回報」(spec.md:12-39、spec.md:67-68)。
- 主要：確認卡片列出的檔名永遠是 document_1.pdf…document_5.pdf 這些樣板，而不是使用者實際挑選的檔案。send_file_consent_card() 只能送出呼叫端指定的檔名，file_handler.py:158-190；\_handle_upload_command() 也只會逐張送出硬編的樣板檔名 command_handler.py:137-154。因為流程中完全沒有讓使用者挑選檔案，也沒有從 Graph 讀取真實 driveItem Metadata，確認卡只能列出這些假資料，file_handler.py:233-247 最後寫回的 UploadedFile.name 也是樣板值，直接違反 User Story 2 要求的「列出所有實際上傳檔案」(spec.md:27-39)。

### 其他觀察

- 先前審查指出的 AttributeError 與檔案大小型別問題已修正：handle_file_consent_accept() 透過 hasattr() 讀欄位並以整數儲存大小，format_file_size() 也能處理未知值。file_handler.py:193-249、card_builder.py:242-306
- 也已在 \_handle_upload_command() 中呼叫 create_upload_state()，多檔案狀態至少會被儲存 command_handler.py:128-150；但如上所述，完成條件仍未符合規格。

### 建議後續

- 依官方樣板流程，在 fileConsentAccept 事件中使用 upload_info.upload_url 上傳（或讀取）真實檔案，再以 Graph 權杖存取 content_url，並擴充 \_get_file_metadata_from_url() 以還原實際檔名與 MIME。
- 讓預期檔案數量由使用者輸入或由實際收到的 Accept/Decline 決定，必要時加入逾時/完成指令，確保少量檔案也能完成批次並滿足 SC-002。
- 改寫同意卡流程，允許使用者挑檔或至少於 Accept 時補寫 Graph Metadata，讓確認卡真正列出使用者上傳的檔案清單。
