import pandas as pd

gen = pd.read_csv("data/raw/Plant_1_Generation_Data.csv")
weather = pd.read_csv("data/raw/Plant_1_Weather_Sensor_Data.csv")

for name, df in [("Generation", gen), ("Weather", weather)]:
    print(f"\n===== {name} =====")
    print(df.shape)         # rows, columns
    print(df.dtypes)        # the data type of each column
    print(df.head())        # the first 5 rows
    print(df.isna().sum())  # count of missing values per column

print("\nInverters:", gen["SOURCE_KEY"].nunique())