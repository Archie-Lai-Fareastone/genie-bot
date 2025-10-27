"""
說明: 提供 Azure AI Foundry 與 Databricks Genie 互動的工具函式，包含建立連接、詢問問題和批次建立函式等功能

重要元件:
- genie_to_object: 將 GenieResponse 物件轉換為字典格式
- ask_genie: 向指定的 Genie 詢問問題並回傳 JSON 格式回應
- create_genie_function: 建立綁定特定 Genie 的可呼叫函式
- setup_genie_functions: 批次建立多個 Genie 函式的設定工具

使用範例:
    from databricks.sdk import WorkspaceClient
    
    client = WorkspaceClient()
    configs = {"space_123": {"name": "data_analyst", "description": "資料分析助理"}}
    functions = setup_genie_functions(configs, client)
"""


from databricks_ai_bridge.genie import Genie, GenieResponse
from databricks.sdk import WorkspaceClient
import json
from typing import List, Any, Callable, Set, Dict


def genie_to_object(response: GenieResponse) -> dict:
    """將 GenieResponse 轉換為字典"""
    return {
        "query": response.query,
        "result": response.result,
        "description": response.description
    }

def ask_genie(genie: Genie, questions: List[str]) -> str:
    """詢問 Genie 並回傳 JSON 格式回應"""
    return json.dumps(genie_to_object(genie.ask_question(questions)))

def create_genie_function(genie: Genie, name: str, description: str = None) -> Callable:
    """建立綁定特定 Genie 的函式"""
    
    def genie_function(questions: List[str]) -> str:
        return ask_genie(genie, questions)
    
    # 設定函式名稱和描述
    genie_function.__name__ = name
    genie_function.__doc__ = description or f"詢問 {name} 資料助理"
    
    return genie_function

def setup_genie_functions(configs: Dict[str, Dict[str, str]], client: WorkspaceClient) -> Set[Callable[..., Any]]:
    """批次建立多個 Genie 函式"""
    functions = set()
    
    for space_id, config in configs.items():
        func_name = config["name"]
        description = config["description"]
        
        try:
            print(f"正在建立 {func_name} (space_id: {space_id})")
            genie = Genie(space_id, client=client)
            functions.add(create_genie_function(genie, func_name, description))
            print(f"✓ 成功建立 {func_name}")
        except Exception as e:
            print(f"✗ 建立 {func_name} 失敗: {e}")
    
    return functions