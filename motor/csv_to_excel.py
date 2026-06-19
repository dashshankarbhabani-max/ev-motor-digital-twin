import pandas as pd
from pathlib import Path

motor_folder = Path(r"C:\Users\dashs\OneDrive\Desktop\project ev motor\motor")
csv_file = motor_folder / "motor_dataset_100k.csv"
excel_file = motor_folder / "motor_dataset_100k.xlsx"

df = pd.read_csv(csv_file)
df.to_excel(excel_file, index=False)

print(f"Excel file saved at: {excel_file}")