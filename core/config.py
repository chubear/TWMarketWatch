import os

class Config:
    API_URL = os.getenv("API_URL", "https://api1.dottdot.com/api/indistock")
    API_KEY = os.getenv("API_KEY", "guest")
    DEFAULT_ENCODING = "utf-8-sig"
    DEFAULT_DATE_FORMAT = "%Y/%m/%d"
