# -*- coding: utf-8 -*-
"""
Created on Wed Sep  6 17:08:57 2023

@author: Gilberto
"""

import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import os


class SOFRDataExtractor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data_1m = pd.read_excel(self.filepath, sheet_name="1M_Term_SOFR", skiprows=2)
        self.data_3m = pd.read_excel(self.filepath, sheet_name="3M_Term_SOFR", skiprows=2)
        
    def interpolate_curve(self, df):
        start_date = df.iloc[0, 0]
        x = (df.iloc[:, 0] - start_date).dt.total_seconds() / (30.44 * 24 * 60 * 60)  # Convert timedelta to float months assuming avg month length
        y = df.iloc[:, 1]
        f = interp1d(x, y, kind="linear", fill_value="extrapolate")
        return f
    
    def plot_curve(self, f, label):
        x_new = np.linspace(0, 120, 500)  # plotting for 120 months
        y_new = f(x_new)
     
        plt.plot(x_new, y_new, label=label)
        
    def plot_forward_curves(self):
        f_1m = self.interpolate_curve(self.data_1m)
        f_3m = self.interpolate_curve(self.data_3m)
        
        self.plot_curve(f_1m, "1M Term SOFR")
        self.plot_curve(f_3m, "3M Term SOFR")
        
        plt.xlabel("Months since start")
        plt.ylabel("Market Expectation")
        plt.title("Forward Curves")
        plt.legend()
        plt.show()


