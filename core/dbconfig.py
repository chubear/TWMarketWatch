import os
from dotenv import dotenv_values
from typing import Optional, Dict, Any


def default_dbconfig(schema: Optional[str] = None) -> Dict[str, Any]:
    """
    從 .env 檔案載入資料庫設定
    
    Args:
        schema: 指定的資料庫名稱，如果為 None 則使用 .env 中的 DB_NAME
        
    Returns:
        包含資料庫連線資訊的字典
        
    Raises:
        ValueError: 當必要的環境變數缺失時
    """
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"找不到環境設定檔: {env_path}")
    
    config = dotenv_values(env_path)
    
    # 驗證必要的環境變數
    required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME']
    missing_vars = [var for var in required_vars if not config.get(var)]
    
    if missing_vars:
        raise ValueError(f"缺少必要的環境變數: {', '.join(missing_vars)}")
    
    return {
        'user': config.get('DB_USER'),
        'password': config.get('DB_PASSWORD'),
        'host': config.get('DB_HOST'),
        'port': int(config.get('DB_PORT')),  # 確保 port 是整數
        'database': config.get('DB_NAME') if schema is None else schema
    }

def default_engine(schema: Optional[str] = None):
    """
    建立 SQLAlchemy 資料庫引擎
    
    Args:
        schema: 指定的資料庫名稱
        
    Returns:
        SQLAlchemy Engine 物件
    """
    from sqlalchemy import create_engine
    
    db_config = default_dbconfig(schema)
    
    # 使用 f-string 更清晰地組建連接字串
    connection_string = (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    
    return create_engine(
        connection_string,
        pool_pre_ping=True,
        pool_recycle=3600,  # 自動回收超時連線
        echo=False  # 設為 True 可以看到 SQL 語句
    )


if __name__ == "__main__":
    print("注意：測試功能已移至 tests/test_dbconnection.py")
    print("請使用以下命令執行測試：")
    print("  python -m dbimporter.tests.test_dbconnection check  # 執行連線檢查")
    print("  python -m dbimporter.tests.test_dbconnection        # 執行單元測試")
    
    # 簡單顯示設定資訊
    try:
        config = default_dbconfig()
        print(f"\n目前設定：")
        print(f"  Database: {config['database']}")
        print(f"  Host: {config['host']}:{config['port']}")
        print(f"  User: {config['user']}")
    except Exception as e:
        print(f"載入設定失敗：{e}")
