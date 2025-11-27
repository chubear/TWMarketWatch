import akshare as ak
import pandas as pd
startdate = "2020-01-01"
enddate = "2025-12-31"
df = ak.macro_euro_industrial_production_mom()
df.set_index("日期", inplace=True)
# df.index = pd.to_datetime(df.index)
# df = df.loc[startdate:enddate,'今值']
print(df)