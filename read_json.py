#read measure_profile.json
import json
from typing import Dict 
import os
import pandas as pd
def load_measure_profile(file_path: str) -> Dict[str, Dict[str, str]]:
    """
    從指定的 JSON 檔案中讀取指標設定檔
    
    Args:
        file_path: JSON 檔案路徑
        
    Returns:
        Dict[str, Dict[str, str]]: 指標設定檔字典
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到指定的檔案: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            profile = json.load(file)
            return profile
        except json.JSONDecodeError as e:
            raise ValueError(f"無法解析 JSON 檔案: {e}")
# Example usage:
profile = load_measure_profile('measure_profile.json')
print(profile)
