from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = {
    "carrier",
    "rate_version",
    "area",
    "age_min",
    "age_max",
    "product_code",
    "product_name",
    "annual_premium",
    "currency",
}


def load_rate_file(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in {".xls", ".xlsx"}:
        df = pd.read_excel(path)
    else:
        raise ValueError("Supported rate formats are CSV, XLS and XLSX.")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required rate columns: {sorted(missing)}")

    return df
