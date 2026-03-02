import pandas as pd

file_path = "ghg-emission-factors-hub.xlsx"

def load_clean_sheet(sheet):
    raw = pd.read_excel(file_path, sheet_name=sheet, header=None)

    # Find row containing real headers (must contain CO2 somewhere)
    header_row = None
    for i in range(len(raw)):
        if raw.iloc[i].astype(str).str.contains("CO2", case=False).any():
            header_row = i
            break

    if header_row is None:
        raise ValueError(f"Could not find header row in {sheet}")

    df = pd.read_excel(file_path, sheet_name=sheet, header=header_row)

    # Clean column names
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
        .str.replace("  ", " ", regex=False)
    )

    return df

# Load sheets properly
table1 = load_clean_sheet("table_1")
table2 = load_clean_sheet("table_2")
table6 = load_clean_sheet("table_6")
table9 = load_clean_sheet("table_9")
table10 = load_clean_sheet("table_10")

print("Loaded successfully.")
print("Table 6 Columns:")
print(table6.columns.tolist())