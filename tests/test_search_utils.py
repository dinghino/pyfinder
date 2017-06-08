"""
Testing module for search.utils. Even utils need some testing!
"""
from search import utils
import pytest


class TestUtils:
    def string_walker(self, string, size, func):
        """Utility function for walker utilities such as splitter and slider"""
        expected = []
        for partial in func(string, size):
            if 0 < size <= len(string):
                # if size is between 0 and the string length the partial length
                # should be what we expected, from 1 to size
                assert len(partial) <= size
            elif size == -1 or size > len(string):
                # partial string should be the whole string if size is -1
                assert len(partial) == len(string)

            assert partial in string
            expected.append(partial)

        return expected

    def test_normalize(self):
        v = utils.normalize([5, 4, 3, 2.5, 1, 7])
        assert pytest.approx(sum(v)) == 1

    def test_scale_to_one(self):
        values = [6, 4, 3, 2, 8, 9, 4]
        v = utils.scale_to_one(values)
        assert max(v) == 1.0
        assert min(v) > 0
        assert sum(v) == pytest.approx(4)

    def test_weighted_average(self):
        s1, w1 = (1, 2, 3), (3, 2, 1)
        r1 = utils.weighted_average(s1, w1)
        assert r1 == pytest.approx(1.7, abs=1e-1)

        s2, w2 = (1, 2, 3), (1, 2, 3)
        r2 = utils.weighted_average(s2, w2)
        assert r2 == pytest.approx(2.3, abs=1e-1)

    def test_tokenize(self):
        v = utils.tokenize('This is a string, and should be tokenized! 123')
        assert v == ['this', 'string', 'should', 'tokenized']

    def test_splitter(self):
        string = "hello there, it's a sunny day!"

        def assert_equal(seq, phrase=string):
            assert phrase == ''.join(seq)

        seq = self.string_walker(string, len(string) + 3, utils.splitter)
        assert_equal(seq)
        seq = self.string_walker(string, 3, utils.splitter)
        assert_equal(seq)
        seq = self.string_walker(string, 6, utils.splitter)
        assert_equal(seq)
        seq = self.string_walker(string, -1, utils.splitter)
        assert_equal(seq)
        seq = self.string_walker('', 5, utils.splitter)
        assert_equal(seq, '')

    def test_slider(self):
        string = "hello there, it's a cloudy day!"

        def assert_equal(seq, phrase=string):
            # Take the first character of each string in our sequence but the
            # last one, that will be added as is, since our slider function
            # walks the string index by index.
            comp = [w[0] for w in seq[:-1]]
            comp.extend(seq[-1])
            assert phrase == ''.join(comp)

        seq = self.string_walker(string, len(string) + 3, utils.shifter)
        assert_equal(seq)
        seq = self.string_walker(string, 3, utils.shifter)
        assert_equal(seq)
        seq = self.string_walker(string, 6, utils.shifter)
        assert_equal(seq)
        seq = self.string_walker(string, -1, utils.shifter)
        assert_equal(seq)
        seq = self.string_walker('', 5, utils.shifter)
        assert_equal(seq, '')
