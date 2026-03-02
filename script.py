import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# FILE PATH
# =====================================================
file_path = "ghg-emission-factors-hub.xlsx"

# =====================================================
# LOAD TABLES
# =====================================================

def load_sheet(sheet, header_row):
    df = pd.read_excel(file_path, sheet_name=sheet, header=header_row)
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
        .str.replace("  ", " ", regex=False)
    )
    return df

# Table 1 has two header rows
table1 = pd.read_excel(file_path, sheet_name="table_1", header=[0, 1])
table1.columns = [
    f"{c1} {c2}".strip()
    for c1, c2 in table1.columns
]

# Other tables
table2 = load_sheet("table_2", 0)
table6 = load_sheet("table_6", 1)
table9 = load_sheet("table_9", 0)
table10 = load_sheet("table_10", 0)

print("Sheets loaded successfully.\n")

# =====================================================
# GLOBAL WARMING POTENTIALS (IPCC AR5)
# =====================================================
GWP_CH4 = 28
GWP_N2O = 265

# =====================================================
# MODELED CAMPUS ACTIVITY DATA (Example Scenario)
# =====================================================
activity = {
    "Natural Gas (therms)": 2_500_000,
    "Gasoline (gallons)": 150_000,
    "Diesel (gallons)": 50_000,
    "Electricity (MWh)": 45_000,
    "Waste (short tons)": 8_000,
    "Employee Commuting (vehicle miles)": 12_000_000,
    "Business Air Travel (passenger miles)": 5_000_000
}

results = {}

# =====================================================
# SCOPE 1 — STATIONARY COMBUSTION (Natural Gas)
# =====================================================

fuel_col = table1.columns[0]

ng_row = table1[
    (table1[fuel_col] == "Natural Gas") &
    (table1["CO2 Factor kg CO2 per mmBtu"].notna())
].iloc[0]

NG_CO2 = float(ng_row["CO2 Factor kg CO2 per mmBtu"])
NG_CH4 = float(ng_row["CH4 Factor g CH4 per mmBtu"])
NG_N2O = float(ng_row["N2O Factor g N2O per mmBtu"])

THERM_TO_MMBTU = 0.1
ng_mmbtu = activity["Natural Gas (therms)"] * THERM_TO_MMBTU

ng_co2 = ng_mmbtu * NG_CO2
ng_ch4 = (ng_mmbtu * NG_CH4) / 1000
ng_n2o = (ng_mmbtu * NG_N2O) / 1000

ng_total = ng_co2 + (ng_ch4 * GWP_CH4) + (ng_n2o * GWP_N2O)
results["Scope 1 - Natural Gas"] = ng_total / 1000

# =====================================================
# SCOPE 1 — MOBILE COMBUSTION
# =====================================================

gas_row = table2[table2["Fuel Type"] == "Motor Gasoline"].iloc[0]
diesel_row = table2[table2["Fuel Type"] == "Diesel Fuel"].iloc[0]

GAS_CO2 = float(gas_row["kg CO2 per unit"])
DIESEL_CO2 = float(diesel_row["kg CO2 per unit"])

results["Scope 1 - Gasoline Fleet"] = (
    activity["Gasoline (gallons)"] * GAS_CO2
) / 1000

results["Scope 1 - Diesel Fleet"] = (
    activity["Diesel (gallons)"] * DIESEL_CO2
) / 1000

# =====================================================
# SCOPE 2 — ELECTRICITY (CAMX Subregion)
# =====================================================

camx_row = table6[table6["eGRID Subregion Acronym"] == "CAMX"].iloc[0]

ELEC_LB = float(camx_row["CO2 Factor"])
LB_TO_KG = 0.453592
ELEC_KG = ELEC_LB * LB_TO_KG

results["Scope 2 - Electricity"] = (
    activity["Electricity (MWh)"] * ELEC_KG
) / 1000

# =====================================================
# SCOPE 3 — WASTE (Landfilled Mixed MSW)
# =====================================================

waste_row = table9[table9["Material"] == "Mixed MSW"].iloc[0]
WASTE_FACTOR = float(waste_row["LandfilledB"])

results["Scope 3 - Waste"] = (
    activity["Waste (short tons)"] * WASTE_FACTOR
)

# =====================================================
# SCOPE 3 — EMPLOYEE COMMUTING
# =====================================================

commute_row = table10[table10["Vehicle Type"] == "Passenger Car A"].iloc[0]

COMMUTE_CO2 = float(commute_row["CO2 Factor (kg / unit)"])
COMMUTE_CH4 = float(commute_row["CH4 Factor (g / unit)"])
COMMUTE_N2O = float(commute_row["N2O Factor (g / unit)"])

commute_co2 = activity["Employee Commuting (vehicle miles)"] * COMMUTE_CO2
commute_ch4 = (activity["Employee Commuting (vehicle miles)"] * COMMUTE_CH4) / 1000
commute_n2o = (activity["Employee Commuting (vehicle miles)"] * COMMUTE_N2O) / 1000

commute_total = commute_co2 + (commute_ch4 * GWP_CH4) + (commute_n2o * GWP_N2O)
results["Scope 3 - Employee Commuting"] = commute_total / 1000

# =====================================================
# SCOPE 3 — BUSINESS AIR TRAVEL (Medium Haul)
# =====================================================

air_row = table10[
    table10["Vehicle Type"].str.contains("Medium Haul")
].iloc[0]

AIR_CO2 = float(air_row["CO2 Factor (kg / unit)"])
AIR_CH4 = float(air_row["CH4 Factor (g / unit)"])
AIR_N2O = float(air_row["N2O Factor (g / unit)"])

air_co2 = activity["Business Air Travel (passenger miles)"] * AIR_CO2
air_ch4 = (activity["Business Air Travel (passenger miles)"] * AIR_CH4) / 1000
air_n2o = (activity["Business Air Travel (passenger miles)"] * AIR_N2O) / 1000

air_total = air_co2 + (air_ch4 * GWP_CH4) + (air_n2o * GWP_N2O)
results["Scope 3 - Business Travel"] = air_total / 1000

# =====================================================
# FINAL SUMMARY TABLE
# =====================================================

df = pd.DataFrame.from_dict(results, orient="index", columns=["Metric Tons CO2e"])
df.loc["TOTAL CAMPUS EMISSIONS"] = df.sum()

# Add percent contribution column
df["Percent of Total"] = (
    df["Metric Tons CO2e"] /
    df.loc["TOTAL CAMPUS EMISSIONS", "Metric Tons CO2e"]
) * 100

print("\n2023 Modeled Campus Greenhouse Gas Inventory\n")
print(df)

# =====================================================
# BAR CHART VISUALIZATION
# =====================================================

plot_df = df.drop("TOTAL CAMPUS EMISSIONS")

plt.figure()
plot_df["Metric Tons CO2e"].plot(kind="bar")
plt.ylabel("Metric Tons CO2e")
plt.title("2023 Modeled Campus GHG Emissions by Source")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("figures/ghg_emissions_2023.png", dpi=300, bbox_inches="tight")



# =====================================================
# SCOPE AGGREGATION (ROBUST VERSION)
# =====================================================

analysis_df = df.drop("TOTAL CAMPUS EMISSIONS").copy()

# Convert index to string explicitly
analysis_df["Source"] = analysis_df.index.astype(str)

# Extract Scope using split instead of regex
analysis_df["Scope"] = analysis_df["Source"].str.split(" - ").str[0]

# Group by Scope
scope_summary = (
    analysis_df
    .groupby("Scope")["Metric Tons CO2e"]
    .sum()
    .reset_index()
)

print("\nEmissions by Scope\n")
print(scope_summary)

# =====================================================
# SCOPE BAR CHART (AUTO GENERATED FROM DATAFRAME)
# =====================================================

plt.figure()
plt.bar(scope_summary["Scope"], scope_summary["Metric Tons CO2e"])

plt.ylabel("Metric Tons CO2e")
plt.title("2023 Modeled Emissions by GHG Scope")
plt.tight_layout()

plt.savefig("figures/ghg_by_scope.png", dpi=300, bbox_inches="tight")
plt.close()

# =====================================================
# PIE CHART (OPTIONAL, CLEANER FOR REPORTS)
# =====================================================

plt.figure()
plt.pie(
    scope_summary["Metric Tons CO2e"],
    labels=scope_summary["Scope"],
    autopct="%1.1f%%"
)

plt.title("Share of Emissions by Scope (2023)")
plt.tight_layout()

plt.savefig("figures/ghg_scope_pie.png", dpi=300, bbox_inches="tight")
plt.close()