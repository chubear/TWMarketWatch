import requests
import pandas as pd

# --- 功能函式 ---
def fetch_eurostat(dataset_code, filters=None, lang="EN"):
    base = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
    url = f"{base}/{dataset_code}"
    params = {"lang": lang}
    if filters:
        params.update(filters)
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def jsonstat_to_df(js):
    dims = js.get("dimension", {})
    observations = js.get("value", {}).get("observations", {})
    dim_labels = {
        dim: dims[dim]["category"]["label"]
        for dim in dims
        if "category" in dims[dim]
    }

    records = []
    for obs_key, obs_val in observations.items():
        parts = obs_key.split(":")
        rec = {}
        for i, dim in enumerate(dim_labels):
            rec[dim] = dim_labels[dim][parts[i]]
        rec["value"] = obs_val[0]
        records.append(rec)

    df = pd.DataFrame(records)
    return df

# --- Example 使用 ---
if __name__ == "__main__":
    # 以歐元區 GDP (假設 dataset code 是 nama_10_gdp) 為例
    js = fetch_eurostat("namq_10_gdp", filters={ "time":"2023"})
    df = jsonstat_to_df(js)
    print(df.head())
