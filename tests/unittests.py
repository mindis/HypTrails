from __future__ import division

__author__ = 'psinger'

import unittest
from scipy.sparse import rand, lil_matrix, csr_matrix, vstack
from sklearn.preprocessing import normalize
from hyptrails.trial_roulette import *
from pathtools.markovchain import MarkovChain
import os

class TestFunctions(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.states = 100

    def setUp(self):
        self.matrix = rand(self.states,self.states, density=0.1, format='csr')

    def test_distr_chips(self):
        ret = distr_chips(self.matrix, self.states*self.states)

        self.assertEqual(ret.sum(), self.states*self.states)

    def test_distr_chips_row_manual(self):
        tmp = lil_matrix(self.matrix.shape)
        for i in xrange(self.states):
            tmp[i,:] = distr_chips(self.matrix[i,:], self.states)

        self.assertEqual(tmp.sum(), self.states*self.states)

    def test_distr_chips_row(self):
        ret = distr_chips_row(self.matrix, self.states)
        self.assertEqual(ret.sum(), self.states*self.states)

    def test_distr_chips_reals(self):
        ret = distr_chips(self.matrix, self.states*self.states, mode="reals")

        self.assertAlmostEqual(ret.sum(), self.states*self.states)

    def test_distr_chips_row_reals(self):
        ret = distr_chips_row(self.matrix, self.states, mode="reals")
        self.assertAlmostEqual(ret.sum(), self.states*self.states)

    def test_distr_chips_row_vs_full(self):
        tmp = normalize(self.matrix, norm='l1')

        ret1 = distr_chips(tmp, self.states*self.states, matrix_sum_final = self.states)

        ret2 = lil_matrix(self.matrix.shape)

        for i in xrange(self.states):
            ret2[i,:] = distr_chips(tmp[i,:], self.states)

        np.testing.assert_array_almost_equal(ret1.toarray(), ret2.toarray(), decimal=0)

    def test_distr_chips_zeros(self):
        m = self.matrix
        m[:] = 0.
        m.eliminate_zeros()
        ret = distr_chips(m, self.states*self.states*2)
        self.assertEqual(ret.sum(), self.states*self.states*2)

    def test_distr_chips_smaller_zeros(self):
        m = self.matrix
        m[:] = 0.
        m.eliminate_zeros()
        ret = distr_chips(m, 90*90)
        self.assertEqual(ret.sum(), 90*90)

    def test_distr_chips_reals_zeros(self):
        m = self.matrix
        m[:] = 0.
        m.eliminate_zeros()
        ret = distr_chips(m, self.states*self.states, mode="reals")

        self.assertEqual(ret.sum(), self.states*self.states)

    def test_distr_chips_row_zeros(self):
        m = self.matrix
        m[0,:] = 0.
        m.eliminate_zeros()
        ret = distr_chips_row(m, self.states)
        self.assertEqual(ret.sum(), self.states*self.states)

    def test_distr_chips_row_reals_zeros(self):
        m = self.matrix
        m[0,:] = 0.
        m[99,:] = 0.
        m.eliminate_zeros()
        ret = distr_chips_row(m, self.states, mode="reals")
        self.assertAlmostEqual(ret.sum(), self.states*self.states)

    def test_distr_chips_row_reals_all_zeros(self):
        m = self.matrix
        m[:] = 0.
        m.eliminate_zeros()
        ret = distr_chips_row(m, self.states, mode="reals")

        self.assertEqual(ret.sum(), self.states*self.states)

    def test_distr_chips_row_reals_zeros_ignore(self):
        m = self.matrix
        m[0,:] = 0.
        m.eliminate_zeros()
        ret = distr_chips_row(m, self.states, dist_zero_rows=False, mode="reals")

        self.assertEqual(ret.sum(), self.states*self.states - self.states)

    def test_distr_chips_row_zeros_ignore(self):
        m = self.matrix
        m[0,:] = 0.
        m.eliminate_zeros()
        ret = distr_chips_row(m, self.states, dist_zero_rows=False)

        self.assertEqual(ret.sum(), self.states*self.states - self.states)

    def test_distr_chips_row_strange_chips(self):
        tmp = lil_matrix(self.matrix.shape)
        for i in xrange(self.states):
            tmp[i,:] = distr_chips(self.matrix[i,:], self.states+53)

        self.assertEqual(tmp.sum(), (self.states)*(self.states)+ self.states*53)

    def test_distr_chips_row_reals_strange_chips(self):
        ret = distr_chips_row(self.matrix, self.states+53, mode="reals")

        self.assertAlmostEqual(ret.sum(), (self.states)*(self.states)+ self.states*53)

    def test_distr_chips_norm(self):
        ret1 = distr_chips(self.matrix, self.states*self.states)
        tmp = self.matrix / self.matrix.sum()
        ret2 = distr_chips(tmp, self.states*self.states, norm=False)

        np.testing.assert_array_equal(ret1.toarray(), ret2.toarray())

    def test_distr_chips_row_norm(self):
        ret1 = distr_chips_row(self.matrix, self.states)
        tmp = normalize(self.matrix, norm='l1')
        ret2 = distr_chips_row(tmp, self.states, norm=False)

        np.testing.assert_array_equal(ret1.toarray(), ret2.toarray())

    def test_distr_chips_hdf5(self):
        filters = tb.Filters(complevel=5, complib='blosc')
        atom = tb.Atom.from_dtype(self.matrix.dtype)
        f = tb.open_file("test.hdf5", 'w')
        out = f.create_carray(f.root, 'data', atom, shape=self.matrix.shape, filters=filters)
        out[:] = self.matrix.toarray()
        f.close()

        ret1 = distr_chips(self.matrix, self.states*self.states)
        distr_chips_hdf5("test.hdf5", self.states*self.states, self.matrix.sum(), "out.hdf5")

        h5 = tb.open_file("out.hdf5", 'r')

        ret2 = csr_matrix((h5.root.data[:], h5.root.indices[:], h5.root.indptr[:]), shape=self.matrix.shape, dtype=np.float64)

        np.testing.assert_array_equal(ret1.toarray(), ret2.toarray())

        h5.close()
        os.remove("test.hdf5")
        os.remove("out.hdf5")

    def test_distr_chips_hdf5_sparse(self):
        hdf5_save(self.matrix,"test.hdf5")

        ret1 = distr_chips(self.matrix, self.states*self.states)
        distr_chips_hdf5_sparse("test.hdf5", self.states*self.states, self.matrix.sum(), "out.hdf5")

        h5 = tb.open_file("out.hdf5", 'r')

        ret2 = csr_matrix((h5.root.data[:], h5.root.indices[:], h5.root.indptr[:]), shape=self.matrix.shape, dtype=np.float64)

        self.assertEqual(h5.root.data[:].sum(), self.states*self.states)
        np.testing.assert_array_equal(ret1.toarray(), ret2.toarray())

        h5.close()
        os.remove("test.hdf5")
        os.remove("out.hdf5")

    def test_evidence_hdf5(self):
        trails = []
        with open("../data/test_case_4") as f:
            for line in f:
                if line.strip() == "":
                    continue
                line = line.strip().split(" ")
                trails.append(np.array(line))

        states = set()
        for row in trails:
            col = list(row)
            for c in col:
                states.add(c)

        #build the vocabulary for matrix A
        vocab = dict(((t, i) for i, t in enumerate(states)))

        A = lil_matrix((5,5))
        A[vocab["1"],vocab["2"]] = 0.6
        A[vocab["1"],vocab["1"]] = 0.4
        A[vocab["3"],vocab["5"]] = 0.4

        A = A.tocsr()

        hdf5_save(A,"test.hdf5")

        ret1 = distr_chips(A, 25)
        distr_chips_hdf5_sparse("test.hdf5", 25, A.sum(), "out.hdf5")

        h5 = tb.open_file("out.hdf5", 'r')

        ret2 = h5.root

        markov = MarkovChain(use_prior=True, reset = True, prior=1., specific_prior=ret1,
                                    specific_prior_vocab = vocab, modus="bayes")
        markov.prepare_data(trails)
        markov.fit(trails)

        evi1 = markov.bayesian_evidence()

        markov = MarkovChain(use_prior=True, reset = True, prior=1., specific_prior=ret2,
                                    specific_prior_vocab = vocab, modus="bayes")
        markov.prepare_data(trails)
        markov.fit(trails)

        evi2 = markov.bayesian_evidence()

        self.assertEqual(evi1, evi2)

        h5.close()
        os.remove("test.hdf5")
        os.remove("out.hdf5")

    def test_evidence_single_row(self):
        trails = []
        with open("../data/test_case_4") as f:
            for line in f:
                if line.strip() == "":
                    continue
                line = line.strip().split(" ")
                trails.append(np.array(line))

        states = set()
        for row in trails:
            col = list(row)
            for c in col:
                states.add(c)

        #build the vocabulary for matrix A
        vocab = dict(((t, i) for i, t in enumerate(states)))

        A = lil_matrix((5,5))
        A[:,0] = 1.
        A = A.tocsr()

        ret1 = distr_chips(A, 25)

        markov = MarkovChain(use_prior=True, reset = True, prior=1., specific_prior=ret1,
                                    specific_prior_vocab = vocab, modus="bayes")
        markov.prepare_data(trails)
        markov.fit(trails)

        evi1 = markov.bayesian_evidence()

        A = lil_matrix((1,5))
        A[0,0] = 1.
        A = A.tocsr()

        ret2 = distr_chips(A, 5)

        markov = MarkovChain(use_prior=True, reset = True, prior=1., specific_prior=ret2,
                                    specific_prior_vocab = vocab, modus="bayes")
        markov.prepare_data(trails)
        markov.fit(trails)

        evi2 = markov.bayesian_evidence()

        self.assertEqual(evi1, evi2)

    def test_evidence_uniform(self):
        trails = []
        with open("../data/test_case_4") as f:
            for line in f:
                if line.strip() == "":
                    continue
                line = line.strip().split(" ")
                trails.append(np.array(line))

        states = set()
        for row in trails:
            col = list(row)
            for c in col:
                states.add(c)

        #build the vocabulary for matrix A
        vocab = dict(((t, i) for i, t in enumerate(states)))

        A = lil_matrix((5,5))
        A[:] = 1.
        A = A.tocsr()

        ret1 = distr_chips(A, 25)

        markov = MarkovChain(use_prior=True, prior=1., specific_prior=ret1,
                                    specific_prior_vocab = vocab, modus="bayes", reset=False)
        markov.prepare_data(trails)
        markov.fit(trails)

        evi1 = markov.bayesian_evidence()


        markov = MarkovChain(use_prior=True, prior=2., modus="bayes", state_count=5, reset=False)
        markov.prepare_data(trails)
        markov.fit(trails)

        evi2 = markov.bayesian_evidence()


        self.assertEqual(evi1, evi2)

    def test_evidence_uniform_row(self):
        trails = []
        with open("../data/test_case_4") as f:
            for line in f:
                if line.strip() == "":
                    continue
                line = line.strip().split(" ")
                trails.append(np.array(line))

        states = set()
        for row in trails:
            col = list(row)
            for c in col:
                states.add(c)

        #build the vocabulary for matrix A
        vocab = dict(((t, i) for i, t in enumerate(states)))

        A = lil_matrix((5,5))
        A[:] = 1.
        A = A.tocsr()

        ret1 = distr_chips_row(A, 5)

        markov = MarkovChain(use_prior=True, prior=1., specific_prior=ret1,
                                    specific_prior_vocab = vocab, modus="bayes", reset=False)
        markov.prepare_data(trails)
        markov.fit(trails)

        evi1 = markov.bayesian_evidence()


        markov = MarkovChain(use_prior=True, prior=2., modus="bayes", state_count=5, reset=False)
        markov.prepare_data(trails)
        markov.fit(trails)

        evi2 = markov.bayesian_evidence()


        self.assertEqual(evi1, evi2)

    def test_evidence_uniform_row_reals(self):
        trails = []
        with open("../data/test_case_4") as f:
            for line in f:
                if line.strip() == "":
                    continue
                line = line.strip().split(" ")
                trails.append(np.array(line))

        states = set()
        for row in trails:
            col = list(row)
            for c in col:
                states.add(c)

        #build the vocabulary for matrix A
        vocab = dict(((t, i) for i, t in enumerate(states)))

        A = lil_matrix((5,5))
        A[:] = 1.
        A = A.tocsr()

        ret1 = distr_chips_row(A, 5, mode="reals")

        markov = MarkovChain(use_prior=True, prior=1., specific_prior=ret1,
                                    specific_prior_vocab = vocab, modus="bayes", reset=False)
        markov.prepare_data(trails)
        markov.fit(trails)

        evi1 = markov.bayesian_evidence()


        markov = MarkovChain(use_prior=True, prior=2., modus="bayes", state_count=5, reset=False)
        markov.prepare_data(trails)
        markov.fit(trails)

        evi2 = markov.bayesian_evidence()


        self.assertEqual(evi1, evi2)

    def test_evidence_uniform_morestates(self):
        trails = []
        with open("../data/test_case_4") as f:
            for line in f:
                if line.strip() == "":
                    continue
                line = line.strip().split(" ")
                trails.append(np.array(line))

        states = set()
        for row in trails:
            col = list(row)
            for c in col:
                states.add(c)

        #build the vocabulary for matrix A
        vocab = dict(((t, i) for i, t in enumerate(states)))

        A = lil_matrix((6,6))
        A[:] = 1.
        A = A.tocsr()

        ret1 = distr_chips(A, 36)

        markov = MarkovChain(use_prior=True, prior=1., specific_prior=ret1,
                                    specific_prior_vocab = vocab, modus="bayes", state_count=6, reset=False)
        markov.prepare_data(trails)
        markov.fit(trails)

        evi1 = markov.bayesian_evidence()


        markov = MarkovChain(use_prior=True, prior=2., modus="bayes", state_count=6, reset=False)
        markov.prepare_data(trails)
        markov.fit(trails)

        evi2 = markov.bayesian_evidence()


        self.assertEqual(evi1, evi2)

    def test_evidence_random_row_reals(self):
        trails = []
        with open("../data/test_case_4") as f:
            for line in f:
                if line.strip() == "":
                    continue
                line = line.strip().split(" ")
                trails.append(np.array(line))

        states = set()
        for row in trails:
            col = list(row)
            for c in col:
                states.add(c)

        #build the vocabulary for matrix A
        vocab = dict(((t, i) for i, t in enumerate(states)))

        A = rand(5,5, density=0.5, format='csr')

        ret1 = distr_chips_row(A, 5, mode="integers")

        markov = MarkovChain(use_prior=True, prior=1., specific_prior=ret1,
                                    specific_prior_vocab = vocab, modus="bayes", reset=False)
        markov.prepare_data(trails)
        markov.fit(trails)

        evi1 = markov.bayesian_evidence()

        ret2 = distr_chips_row(A, 5, mode="reals")

        markov = MarkovChain(use_prior=True, prior=1., specific_prior=ret2,
                                    specific_prior_vocab = vocab, modus="bayes", reset=False)
        markov.prepare_data(trails)
        markov.fit(trails)

        evi2 = markov.bayesian_evidence()

        self.assertLess(abs(evi1-evi2),2)

if __name__ == '__main__':
    unittest.main()