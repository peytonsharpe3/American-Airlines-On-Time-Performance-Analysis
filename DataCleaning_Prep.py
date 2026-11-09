import pandas as pd
from pathlib import Path
import numpy as np

# File locations
data_folder = Path(__file__).resolve().parent / "Data"
raw_folder = next(
    p for p in data_folder.iterdir()
    if p.is_dir() and p.name.strip() == "Raw Data"
)
output = data_folder / "AA_CLT_2025.csv"

# Find all monthly CSV files
files = sorted(raw_folder.glob("*_T_ONTIME_REPORTING.csv"))

if not files:
    raise FileNotFoundError("No monthly CSV files found.")

first_chunk = True
total_flights = 0

# Read, filter, and combine monthly files
for file in files:
    print(f"Processing {file.name}")

    for chunk in pd.read_csv(file, chunksize=100000):

        # Filter for American Airlines and Charlotte in 2025
        filtered = chunk[
            (chunk["YEAR"] == 2025) &
            (chunk["OP_CARRIER"] == "AA") &
            ((chunk["ORIGIN"] == "CLT") |
             (chunk["DEST"] == "CLT"))
        ].copy()

        # Add flight direction
        filtered["DIRECTION"] = np.where(
            filtered["ORIGIN"] == "CLT",
            "Departing CLT",
            "Arriving CLT"
        )

        # Append filtered flights to one CSV
        filtered.to_csv(
            output,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False
        )

        first_chunk = False
        total_flights += len(filtered)

# Results
print("\nTotal flights:", total_flights)
print("Months processed:", len(files))
print("Saved to:", output)