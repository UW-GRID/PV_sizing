import pandas as pd

print('Input path to load profile')
filename = input("> ")

raw_input = pd.read_csv(filename, header=None, skiprows = 12, nrows=1)
raw_input = raw_input.dropna(axis='columns')
raw_input = raw_input.drop([6, 7, 57], axis='columns')
hourly_load = []

for i in raw_input.iloc[0]:
    hourly_load.append(i)
