from __future__ import print_function, division    # (at top of module)
import sys
import logging

import numpy as np

logger = logging.getLogger("LevelGenerator")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class QuantitySampler(object):
    """Performs quantity sampling of roof top objects
    Uses a provided Pandas DataFrame where each row is a building observation and 
    a column is a rooftop object type. The cell contains the quantity observed.
    
    """

    def __init__(self, df, fit='histogram'):
        """Pass in a dataframe and specify if you want sampling to be from a histogram or 
        a kernel density estimator (kde).
        
        Arguments:
            df {DataFrame} -- DataFrame of Data
        
        Keyword Arguments:
            fit {str} -- How to sample from data. Histogram is just a weighted random choice (default: {'histogram'})
        """

        self.df = df
        self.fit = fit

        if fit == 'histogram':
            self.set_up_histogram()
        else:
            raise NotImplementedError("Have not implemented kde yet")

    def sample(self, key, size=1):
        quantity = [0] * size
        if self.fit == 'histogram':
            kwargs = self.histogram_meta[key].copy()
            kwargs.update(size=size)
            quantity = self.histogram_sampling(**kwargs)
        
        return quantity if size > 1 else quantity[0]

    def set_up_histogram(self):
        items = self.df.columns
        histogram_meta = {}
        # Iterate through each column in dataframe
        for item in items:
            x = self.df[item].values
            quantities, counts = np.unique(x, return_counts=True)
            histogram_meta[item] = dict(quantities=quantities, probabilities=counts/x.shape[0])
        self.histogram_meta = histogram_meta
    
    def histogram_sampling(self, quantities, probabilities, size=1):
        return np.random.choice(quantities, size=size, p=probabilities)



