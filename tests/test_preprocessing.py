from pandas.util.testing import assert_almost_equal, assert_index_equal
from fcsy.preprocessing import *


class TestTransform:
    def setup_method(self):
        df = pd.DataFrame([[0.1, 0.1, 0.1, 1],
                           [0.2, 0.1, 0.2, 100],
                           [0.3, 0.1, 0.3, 1000],
                           [0.4, 0.1, 0.4, 10000],
                           ], columns=['a', 'b', 'c', 'd'], index=[1, 2, 5, 8])
        self.df = df

    def test_zscore(self):
        expected = pd.DataFrame([[-1.341641, np.nan, -1.341641, -0.662218],
                                 [-0.447214, np.nan, -0.447214, -0.638587],
                                 [0.447214, np.nan,  0.447214, -0.423755],
                                 [1.341641, np.nan,  1.341641, 1.724560]],
                                columns=self.df.columns, index=self.df.index)
        assert_almost_equal(zscore(self.df), expected)

    def test_arcsinh(self):
        expected = pd.DataFrame([[0.019998666906609543, 0.019998666906609543, 0.019998666906609543, 0.198690],
                                 [0.039989341006027, 0.019998666906609543, 0.039989341006027, 3.689504],
                                 [0.059964058195333944, 0.019998666906609543, 0.059964058195333944, 5.991471],
                                 [0.07991491149449678, 0.019998666906609543, 0.07991491149449678, 8.294050]],
                                columns=self.df.columns, index=self.df.index)
        assert_almost_equal(arcsinh(self.df), expected)

    def test_randomize(self):
        assert_index_equal(randomize(self.df).index, self.df.index)
