import pandas as pd 
import os 


DATA_DIR = os.path.join('src', '_data', 'dummy_linechart.csv')

dummy_linechart = pd.read_csv(DATA_DIR)

if __name__ == '__main__':

    dummy_linechart['date'] = pd.to_datetime(dummy_linechart['date'])
    dummy_linechart.to_csv(DATA_DIR, index=False)

    print(dummy_linechart['date'].dtype)