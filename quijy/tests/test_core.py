from itertools import combinations
import scipy.sparse as sp
import numpy as np
from numpy.testing import assert_allclose, assert_almost_equal
from quijy.gen import bell_state
from quijy.rand import rand_rho, rand_matrix
from quijy.core import (quijify, qjf, isket, isbra, isop, isherm,
                        trace, sparse_trace, tr, nmlz, ptr, chop,
                        eye, kron, kron_dense, kronpow, eyepad)


# Quijify
def test_quijify_vector_create():
    x = [1, 2, 3j]
    p = quijify(x, qtype='ket')
    assert(type(p) == np.matrix)
    assert(p.dtype == np.complex)
    assert(p.shape == (3, 1))
    p = quijify(x, qtype='bra')
    assert(p.shape == (1, 3))
    assert_almost_equal(p[0, 2], -3.0j)


def test_quijify_dop_create():
    x = np.random.randn(3, 3)
    p = quijify(x, qtype='dop')
    assert(type(p) == np.matrix)
    assert(p.dtype == np.complex)
    assert(p.shape == (3, 3))


def test_quijify_convert_vector_to_dop():
    x = [1, 2, 3j]
    p = quijify(x, qtype='r')
    assert_allclose(p, np.matrix([[1.+0.j,  2.+0.j,  0.-3.j],
                                  [2.+0.j,  4.+0.j,  0.-6.j],
                                  [0.+3.j,  0.+6.j,  9.+0.j]]))


def test_quijify_chopped():
    x = [9e-16, 1]
    p = quijify(x, 'k', chopped=False)
    assert(p[0, 0] != 0.0)
    p = quijify(x, 'k', chopped=True)
    assert(p[0, 0] == 0.0)


def test_quijify_normalized():
    x = [3j, 4j]
    p = quijify(x, 'k', normalized=False)
    assert_almost_equal(tr(p.H @ p), 25.)
    p = quijify(x, 'k', normalized=True)
    assert_almost_equal(tr(p.H @ p), 1.)
    p = quijify(x, 'dop', normalized=True)
    assert_almost_equal(tr(p), 1.)


def test_quijify_sparse_create():
    x = [[1, 0], [3, 0]]
    p = quijify(x, 'dop', sparse=False)
    assert(type(p) == np.matrix)
    p = quijify(x, 'dop', sparse=True)
    assert(type(p) == sp.csr_matrix)
    assert(p.dtype == np.complex)
    assert(p.nnz == 2)


def test_quijify_sparse_convert_to_dop():
    x = [1, 0, 9e-16, 0, 3j]
    p = quijify(x, 'ket', sparse=True)
    q = quijify(p, 'dop', sparse=True)
    assert(q.shape == (5, 5))
    assert(q.nnz == 9)
    assert_almost_equal(q[4, 4], 9.)
    q = quijify(p, 'dop', sparse=True, normalized=True)
    assert_almost_equal(tr(q), 1.)


# Shape checks
def test_ket():
    x = qjf([[1], [0]])
    assert(isket(x))
    assert(not isbra(x))
    assert(not isop(x))


def test_bra():
    x = qjf([[1, 0]])
    assert(not isket(x))
    assert(isbra(x))
    assert(not isop(x))


def test_op():
    x = qjf([[1, 0]])
    assert(not isket(x))
    assert(isbra(x))
    assert(not isop(x))


def test_isherm():
    a = qjf([[1.0, 2.0 + 3.0j],
             [2.0 - 3.0j, 1.0]])
    assert(isherm(a))
    a = qjf([[1.0, 2.0 - 3.0j],
             [2.0 - 3.0j, 1.0]])
    assert(not isherm(a))


def test_isherm_sparse():
    a = qjf([[1.0, 2.0 + 3.0j],
             [2.0 - 3.0j, 1.0]], sparse=True)
    assert(isherm(a))
    a = qjf([[1.0, 2.0 - 3.0j],
             [2.0 - 3.0j, 1.0]], sparse=True)
    assert(not isherm(a))


# Trace tests
def test_trace():
    a = qjf([[2, 1], [4, 5]])
    assert(a.tr.__code__.co_code == trace.__code__.co_code)
    assert(tr(a) == 7)


def test_sparse_trace():
    a = qjf([[2, 1], [4, 5]], sparse=True)
    assert(a.tr.__code__.co_code == sparse_trace.__code__.co_code)
    assert(tr(a) == 7)


# Test Normalize
def test_normalize():
    a = qjf([1, 1], 'ket')
    b = nmlz(a)
    assert_almost_equal(tr(b.H @ b), 1.0)
    a = qjf([1, 1], 'bra')
    b = nmlz(a)
    assert_almost_equal(tr(b @ b.H), 1.0)
    a = qjf([1, 1], 'dop')
    b = nmlz(a)
    assert_almost_equal(tr(b), 1.0)


def test_normalize_inplace():
    a = qjf([1, 1], 'ket')
    a.nmlz(inplace=True)
    assert_almost_equal(tr(a.H @ a), 1.0)
    a = qjf([1, 1], 'bra')
    a.nmlz(inplace=True)
    assert_almost_equal(tr(a @ a.H), 1.0)
    a = qjf([1, 1], 'dop')
    a.nmlz(inplace=True)
    assert_almost_equal(tr(a), 1.0)


# Kron functions
def test_kron_dense():
    a = rand_matrix(3)
    b = rand_matrix(3)
    c = kron_dense(a, b)
    npc = np.kron(a, b)
    assert_allclose(c, npc)


def test_kron_multi_args():
    a = rand_matrix(3)
    b = rand_matrix(3)
    c = rand_matrix(3)
    assert(kron() == 1)
    assert_allclose(kron(a), a)
    assert_allclose(kron(a, b, c),
                    np.kron(np.kron(a, b), c))


def test_kron_mixed_types():
    # TODO: scalar
    a = qjf([1, 2, 3, 4], 'ket')
    b = qjf([0, 1, 0, 2], 'ket', sparse=True)
    # c = -1.0j
    assert_allclose(kron(a, b).A,
                    (sp.kron(a, b, 'csr')).A)
    assert_allclose(kron(b, b).A,
                    (sp.kron(b, b, 'csr')).A)
    # assert_allclose(kron(a, c), a * c)
    # kron(b, c)
    # kron(b, c)


def test_kronpow():
    a = rand_matrix(2)
    b = a & a & a
    c = kronpow(a, 3)
    assert_allclose(b, c)


# TODO: test eye
# TODO: Test coords_map
# 1d
# 2d
# 3d
# cyclic
# trim
# error


# Test eyepad
def test_eyepad_basic():
    a = rand_matrix(2)
    i = eye(2)
    dims = [2, 2, 2]
    b = eyepad([a], dims, [0])
    assert_allclose(b, a & i & i)
    b = eyepad([a], dims, [1])
    assert_allclose(b, i & a & i)
    b = eyepad([a], dims, [2])
    assert_allclose(b, i & i & a)
    b = eyepad([a], dims, [0, 2])
    assert_allclose(b, a & i & a)
    b = eyepad([a], dims, [0, 1, 2])
    assert_allclose(b, a & a & a)


def test_eyepad_mid_multi():
    a = [rand_matrix(2) for i in range(3)]
    i = eye(2)
    dims = [2, 2, 2, 2, 2, 2]
    inds = [1, 2, 4]
    b = eyepad(a, dims, inds)
    assert_allclose(b, i & a[0] & a[1] & i & a[2] & i)


def test_eyepad_mid_multi_reverse():
    a = [rand_matrix(2) for i in range(3)]
    i = eye(2)
    dims = [2, 2, 2, 2, 2, 2]
    inds = [5, 4, 1]
    b = eyepad(a, dims, inds)
    assert_allclose(b, i & a[2] & i & i & a[1] & a[0])


def test_eyepad_auto():
    a = rand_matrix(2)
    i = eye(2)
    b = eyepad([a], (2, -1, 2), [1])
    assert_allclose(b, i & a & i)


def test_eyepad_ndarrays():
    a = rand_matrix(2)
    i = eye(2)
    b = eyepad([a], np.array([2, 2, 2]), [0, 2])
    assert_allclose(b, a & i & a)
    b = eyepad([a], [2, 2, 2], np.array([0, 2]))
    assert_allclose(b, a & i & a)


def test_eyepad_overlap():
    a = [rand_matrix(4) for i in range(2)]
    dims1 = [2, 2, 2, 2, 2, 2]
    dims2 = [2, 4, 4, 2]
    b = eyepad(a, dims1, [1, 2, 3, 4])
    c = eyepad(a, dims2, [1, 2])
    assert_allclose(c, b)

    dims2 = [4, 2, 2, 4]
    b = eyepad(a, dims1, [0, 1, 4, 5])
    c = eyepad(a, dims2, [0, 3])
    assert_allclose(c, b)


def test_eyepad_sparse():
    i = eye(2, sparse=True)
    a = qjf(rand_matrix(2), sparse=True)
    b = eyepad(a, [2, 2, 2], 1)
    assert(sp.issparse(b))
    assert_allclose(b.A, (i & a & i).A)
    a = rand_matrix(2)
    b = eyepad(a, [2, 2, 2], 1, sparse=True)
    assert(sp.issparse(b))
    assert_allclose(b.A, (i & a & i).A)


# TODO: test permute_subsystems

# Partial Trace checks
def test_partial_trace_early_return():
    a = qjf([0.5, 0.5, 0.5, 0.5], 'ket')
    b = ptr(a, [2, 2], [0, 1])
    assert_allclose(a @ a.H, b)
    a = qjf([0.5, 0.5, 0.5, 0.5], 'dop')
    b = ptr(a, [2, 2], [0, 1])
    assert_allclose(a, b)


def test_partial_trace_return_type():
    a = qjf([0, 2**-0.5, 2**-0.5, 0], 'ket')
    b = ptr(a, [2, 2], 1)
    assert(type(a) == np.matrix)
    a = qjf([0, 2**-0.5, 2**-0.5, 0], 'dop')
    b = ptr(a, [2, 2], 1)
    assert(type(a) == np.matrix)


def test_partial_trace_single_ket():
    dims = [2, 3, 4]
    a = np.random.randn(np.prod(dims), 1)
    for i, dim in enumerate(dims):
        b = ptr(a, dims, i)
        assert(b.shape[0] == dim)


def test_partial_trace_multi_ket():
    dims = [2, 3, 4]
    a = np.random.randn(np.prod(dims), 1)
    for i1, i2 in combinations([0, 1, 2], 2):
        b = ptr(a, dims, [i1, i2])
        assert(b.shape[1] == dims[i1] * dims[i2])


def test_partial_trace_dop_product_state():
    dims = [3, 2, 4, 2, 3]
    ps = [rand_rho(dim) for dim in dims]
    pt = kron(*ps)
    for i, dim in enumerate(dims):
        p = ptr(pt, dims, i)
        assert_allclose(p, ps[i])


def test_partial_trace_bell_states():
    for lab in ('psi-', 'psi+', 'phi-', 'phi+'):
        psi = bell_state(lab, qtype='dop')
        rhoa = ptr(psi, [2, 2], 0)
        assert_allclose(rhoa, eye(2)/2)


def test_partial_trace_supply_ndarray():
    a = rand_rho(2**3)
    dims = np.array([2, 2, 2])
    keep = np.array(1)
    b = ptr(a, dims, keep)
    assert(b.shape[0] == 2)


# Test chop
def test_chop_inplace():
    a = qjf([-1j, 0.1+0.2j])
    chop(a, tol=0.11, inplace=True)
    assert_allclose(a, qjf([-1j, 0.2j]))
    # Sparse
    a = qjf([-1j, 0.1+0.2j], sparse=True)
    chop(a, tol=0.11, inplace=True)
    b = qjf([-1j, 0.2j], sparse=True)
    assert((a != b).nnz == 0)


def test_chop_inplace_dop():
    a = qjf([1, 0.1], 'dop')
    chop(a, tol=0.11, inplace=True)
    assert_allclose(a, qjf([1, 0], 'dop'))
    a = qjf([1, 0.1], 'dop', sparse=True)
    chop(a, tol=0.11, inplace=True)
    b = qjf([1, 0.0], 'dop', sparse=True)
    assert((a != b).nnz == 0)


def test_chop_copy():
    a = qjf([-1j, 0.1+0.2j])
    b = chop(a, tol=0.11, inplace=False)
    assert_allclose(a, qjf([-1j, 0.1+0.2j]))
    assert_allclose(b, qjf([-1j, 0.2j]))
    # Sparse
    a = qjf([-1j, 0.1+0.2j], sparse=True)
    b = chop(a, tol=0.11, inplace=False)
    ao = qjf([-1j, 0.1+0.2j], sparse=True)
    bo = qjf([-1j, 0.2j], sparse=True)
    assert((a != ao).nnz == 0)
    assert((b != bo).nnz == 0)

# TODO: test rdmul/ldmul
# TODO: test infer_size
# TODO: test levi_civita