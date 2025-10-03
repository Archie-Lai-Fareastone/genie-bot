"""
Azure AI Agent 操作函式庫

提供建立和刪除 Azure AI Agent 的純函式。

使用方式：
    # 建立代理程式
    agent_id = await create_agent("我的助手", "你是一個有幫助的助理")
    
    # 刪除代理程式
    success = await delete_agent(agent_id)
"""

from typing import Optional, Tuple
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
import os

load_dotenv()


def _get_project_client() -> AIProjectClient:
    """建立並返回 AIProjectClient 實例"""
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    if not endpoint:
        raise ValueError("環境變數 AZURE_AI_AGENT_ENDPOINT 未設定")
    
    credential = DefaultAzureCredential()
    return AIProjectClient(credential=credential, endpoint=endpoint)


async def create_agent(
    agent_name: str, 
    agent_instructions: str,
    model_deployment_name: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    建立新的 Azure AI Agent
    
    Args:
        agent_name: 代理程式名稱
        agent_instructions: 代理程式指令
        model_deployment_name: 模型部署名稱（可選）
        
    Returns:
        (成功標誌, 訊息, Agent ID)
    """
    try:
        model_deployment_name = model_deployment_name or os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
        if not model_deployment_name:
            return False, "未設定模型部署名稱", None
        if not (agent_name := agent_name.strip()):
            return False, "代理程式名稱不能為空", None
        if not (agent_instructions := agent_instructions.strip()):
            return False, "代理程式指令不能為空", None
        
        project_client = _get_project_client()
        
        with project_client:
            agent = project_client.agents.create_agent(
                model=model_deployment_name,
                name=agent_name.strip(),
                instructions=agent_instructions.strip(),
            )
            
            success_message = f"成功建立代理程式 '{agent.name}'"
            return True, success_message, agent.id
            
    except Exception as e:
        error_message = f"建立代理程式時發生錯誤: {e}"
        return False, error_message, None


async def delete_agent(agent_id: str) -> Tuple[bool, str]:
    """
    刪除指定的 Azure AI Agent
    
    Args:
        agent_id: 要刪除的代理程式 ID
        
    Returns:
        (成功標誌, 結果訊息)
    """
    try:
        if not agent_id or not agent_id.strip():
            return False, "代理程式 ID 不能為空"
        
        project_client = _get_project_client()
        
        with project_client:
            try:
                agent = project_client.agents.get_agent(agent_id=agent_id.strip())
                agent_name = agent.name
            except Exception as get_error:
                return False, f"無法找到代理程式 ID '{agent_id}': {get_error}"
            
            project_client.agents.delete_agent(agent_id=agent_id.strip())
            return True, f"成功刪除代理程式 '{agent_name}'"
            
    except Exception as e:
        return False, f"刪除代理程式時發生錯誤: {e}"