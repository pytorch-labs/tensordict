import os
import torch
import pytest

from _utils_internal import get_available_devices
from tensordict import TensorMap


@pytest.mark.parametrize("device", get_available_devices())
def test_tensormap_simple_set_tensor(device):
    m = TensorMap()
    x = torch.ones(3)
    m['a'] = x
    assert m['a'] is x

    m['a'] = torch.zeros(3)
    assert (m['a'] == 0).all()

    m['b'] = m['a']
    assert m['b'] is m['a']


@pytest.mark.skip(reason="TensorMap ref not working for now") # parametrize("device", get_available_devices())
def test_tensormap_simple_set_map(device):
    m1 = TensorMap()
    m2 = TensorMap()

    m1['a'] = m2
    assert m1['a'] is m2  # Failing - Need to fix!


@pytest.mark.parametrize("device", get_available_devices())
def test_tensormap_nested_set(device):
    m1 = TensorMap()
    m2 = TensorMap()
    x = torch.rand(3)
    y = torch.rand(3)

    m1['a'] = torch.ones(3)
    m1['b'] = m2
    m2['c'] = x

    assert x is m1['b']['c']
    assert m1['b']['c'] is m1['b', 'c']
    assert m1['b', 'c'] is m2['c']

    m1['b', 'c'] = y
    assert m1['b']['c'] is y
    assert m1['b', 'c'] is y
    assert m2['c'] is y


@pytest.mark.parametrize("device", get_available_devices())
def test_tensormap_nested_overrite(device):
    m1 = TensorMap()

    m1['a'] = torch.ones(3)
    assert (m1['a'] == 1).all()
    m1['a', 'b', 'c'] = torch.ones(3)
    assert type(m1['a']) is TensorMap
    assert type(m1['a', 'b']) is TensorMap
    assert m1['a', 'b', 'c'] is m1['a', 'b']['c']
    assert (m1['a', 'b', 'c'] == 1).all()

    m2 = TensorMap()
    m2['x'] = m1['a', 'b']
    assert m2['x', 'c'] is m1['a', 'b', 'c']


@pytest.mark.parametrize("device", get_available_devices())
def test_tensormap_get_keys(device):
    m = TensorMap()
    m['a'] = torch.ones(3)
    m['b'] = torch.zeros(3)

    expected_keys = {'a', 'b'}
    assert len(expected_keys.difference(m.keys())) == 0

    m['c', 'd'] = torch.ones(3)
    m['a', 'x', 'y'] = torch.zeros(3)
    expected_nested_keys = {('a', 'x', 'y'), 'b', ('c', 'd')}
    assert len(expected_nested_keys.difference(m.keys(True))) == 0
    expected_keys = {'a', 'b', 'c'}
    assert len(expected_keys.difference(m.keys())) == 0

    m['a', 'z'] = torch.rand(3)
    expected_nested_keys = {('a', 'z'), ('a', 'x', 'y'), 'b', ('c', 'd')}
    assert len(expected_nested_keys.difference(m.keys(True))) == 0
    expected_keys = {'a', 'b', 'c'}
    assert len(expected_keys.difference(m.keys())) == 0

    m['c', 'd'] = m['a']
    expected_nested_keys = {('a', 'z'), ('a', 'x', 'y'), 'b', ('c', 'd', 'z')}
    assert len(expected_nested_keys.difference(m.keys(True))) == 0
    expected_keys = {'a', 'b', 'c'}
    assert len(expected_keys.difference(m.keys())) == 0

    m['c'] = torch.ones(3)
    expected_nested_keys = {('a', 'z'), ('a', 'x', 'y'), 'b', 'c'}
    assert len(expected_nested_keys.difference(m.keys(True))) == 0
    expected_keys = {'a', 'b', 'c'}
    assert len(expected_keys.difference(m.keys())) == 0


@pytest.mark.parametrize("device", get_available_devices())
def test_tensormap_get_keys_leaves_only(device):
    m = TensorMap()
    m['a'] = torch.ones(3)
    m['b'] = torch.zeros(3)

    expected_keys = {'a', 'b'}
    assert len(expected_keys.difference(m.keys(False, True))) == 0

    m['c', 'd'] = torch.ones(3)
    m['a', 'x', 'y'] = torch.zeros(3)
    expected_keys = {('a', 'x', 'y'), 'b', ('c', 'd')}
    assert len(expected_keys.difference(m.keys(True, True))) == 0
    expected_keys = {'b'}
    assert len(expected_keys.difference(m.keys(False, True))) == 0

    m['a', 'z'] = torch.rand(3)
    expected_keys = {('a', 'z'), ('a', 'x', 'y'), 'b', ('c', 'd')}
    assert len(expected_keys.difference(m.keys(True, True))) == 0
    expected_keys = {'b'}
    assert len(expected_keys.difference(m.keys(False, True))) == 0

    m['c', 'd'] = m['a']
    expected_keys = {('a', 'z'), ('a', 'x', 'y'), 'b', ('c', 'd', 'z')}
    assert len(expected_keys.difference(m.keys(True, True))) == 0
    expected_keys = {'b'}
    assert len(expected_keys.difference(m.keys(False, True))) == 0

    m['c'] = torch.ones(3)
    expected_keys = {('a', 'z'), ('a', 'x', 'y'), 'b', 'c'}
    assert len(expected_keys.difference(m.keys(True, True))) == 0
    expected_keys = {'b', 'c'}
    assert len(expected_keys.difference(m.keys(False, True))) == 0



@pytest.mark.skip(reason="in keyword doesn't work with all cases") # .parametrize("device", get_available_devices())
def test_tensormap_in_keys(device):
    m = TensorMap()
    m['a', 'b', 'c'] = torch.zeros(3)
    m['d'] = torch.zeros(3)

    keys = m.keys()
    assert 'd' in keys
    assert ('a', 'b', 'c') in keys

    assert ('a', 'b') in keys  # This breaks too. Need to overwrite 'in' keyword ?
    assert ('a', ) in keys