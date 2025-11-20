import numpy as np
import pandas as pd

data = np.load("Combo_11_6.npz")

data_arr = data["data_arr"]
rounded = np.round(data_arr, 4)

pd.DataFrame(rounded).to_csv("rounded_data.csv", index=True, header=False)