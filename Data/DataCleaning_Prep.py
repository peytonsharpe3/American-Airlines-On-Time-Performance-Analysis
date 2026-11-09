import pandas as pd
import numpy as np
from pathlib import Path
from zipfile import ZipFile

# Project directory
folder = Path(
    "/Users/peytonsharpe/Documents/"
    "American-Airlines-On-Time-Performance-Analysis/"
    "Data/Jan_T_ONTIME_REPORTING.csv"
)

# Output file
output_file = folder / "AA_CLT_2025.csv"

# Variables needed for the project
columns = [
    "Year", "Month", "DayOfWeek", "FlightDate",
    "Reporting_Airline", "Flight_Number_Reporting_Airline",
    "Origin", "Dest",
    "CRSDepTime", "DepTime", "DepTimeBlk",
    "CRSArrTime", "ArrTime",
    "DepDelay", "DepDel15", "ArrDelay", "ArrDel15",
    "Cancelled", "CancellationCode", "Diverted",
    "TaxiOut", "TaxiIn", "Distance", "AirTime",
    "CarrierDelay", "WeatherDelay", "NASDelay",
    "SecurityDelay", "LateAircraftDelay"
]

# Find CSV and ZIP files
files = sorted(
    f for f in folder.iterdir()
    if f.suffix.lower() in [".csv", ".zip"]
    and f.name != output_file.name
)

# Avoid processing both ZIP and extracted CSV versions
zip_stems = {
    f.stem for f in files
    if f.suffix.lower() == ".zip"
}

files = [
    f for f in files
    if f.suffix.lower() == ".zip"
    or f.stem not in zip_stems
]

frames = []

for file in files:
    print(f"Processing: {file.name}")

    if file.suffix.lower() == ".zip":
        with ZipFile(file) as archive:
            csv_name = next(
                (
                    name for name in archive.namelist()
                    if name.lower().endswith(".csv")
                ),
                None
            )

            if csv_name is None:
                continue

            with archive.open(csv_name) as source:
                monthly = pd.read_csv(
                    source,
                    usecols=lambda c: c in columns,
                    low_memory=False
                )
    else:
        monthly = pd.read_csv(
            file,
            usecols=lambda c: c in columns,
            low_memory=False
        )

    # Verify required columns
    required = ["Year", "Reporting_Airline", "Origin", "Dest"]

    missing = [
        col for col in required
        if col not in monthly.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns in {file.name}: {missing}"
        )

    # Filter for American Airlines, 2025, and CLT
    monthly = monthly[
        (monthly["Year"] == 2025) &
        (monthly["Reporting_Airline"] == "AA") &
        (
            (monthly["Origin"] == "CLT") |
            (monthly["Dest"] == "CLT")
        )
    ].copy()

    frames.append(monthly)

if not frames:
    raise ValueError("No valid BTS data files were found.")

# Combine filtered data
df = pd.concat(frames, ignore_index=True)

if df.empty:
    raise ValueError("No flights matched the selected filters.")

# Create direction variable
df["Direction"] = np.where(
    df["Origin"] == "CLT",
    "Departing CLT",
    "Arriving CLT"
)

# Create route variable
df["Route"] = df["Origin"] + "-" + df["Dest"]

# Extract scheduled departure hour
df["DepartureHour"] = (
    pd.to_numeric(df["CRSDepTime"], errors="coerce") // 100
)

# Handle midnight represented as 2400
df.loc[df["DepartureHour"] == 24, "DepartureHour"] = 0

# Create departure time periods
df["DeparturePeriod"] = pd.cut(
    df["DepartureHour"],
    bins=[-1, 5, 11, 17, 23],
    labels=[
        "Overnight",
        "Morning",
        "Afternoon",
        "Evening"
    ]
)

# Convert dates
df["FlightDate"] = pd.to_datetime(df["FlightDate"])

# Save filtered dataset
df.to_csv(output_file, index=False)

# Summary
print("\nDATASET SUMMARY")
print("-------------------------------")
print("Total flights:", len(df))
print("Unique routes:", df["Route"].nunique())

print("\nFlights by direction:")
print(df["Direction"].value_counts())

print("\nFlights by month:")
print(df.groupby("Month").size())

print("\nCancellation rate:")
print(f"{df['Cancelled'].mean() * 100:.2f}%")

print("\nDataset saved to:")
print(output_file)