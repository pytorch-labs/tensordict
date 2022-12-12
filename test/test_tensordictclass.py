from __future__ import annotations

import argparse
import dataclasses
import re
from typing import Any

import pytest
import torch

from tensordict import LazyStackedTensorDict, TensorDict
from tensordict.prototype import tensordictclass
from tensordict.tensordict import _PermutedTensorDict, _ViewedTensorDict, TensorDictBase
from torch import Tensor


@tensordictclass
class MyData:
    X: torch.Tensor
    y: torch.Tensor

    def stuff(self):
        return self.X + self.y


def test_dataclass():

    data = MyData(
        X=torch.ones(3, 4, 5),
        y=torch.zeros(3, 4, 5, dtype=torch.bool),
        batch_size=[3, 4],
    )
    assert dataclasses.is_dataclass(data)


def test_type():

    data = MyData(
        X=torch.ones(3, 4, 5),
        y=torch.zeros(3, 4, 5, dtype=torch.bool),
        batch_size=[3, 4],
    )
    assert isinstance(data, MyData)


def test_attributes():

    X = torch.ones(3, 4, 5)
    y = torch.zeros(3, 4, 5, dtype=torch.bool)
    batch_size = [3, 4]
    tensordict = TensorDict(
        {
            "X": X,
            "y": y,
        },
        batch_size=[3, 4],
    )

    data = MyData(X=X, y=y, batch_size=batch_size)

    equality_tensordict = data.tensordict == tensordict

    assert torch.equal(data.X, X)
    assert torch.equal(data.y, y)
    assert data.batch_size == batch_size
    assert equality_tensordict.all()
    assert equality_tensordict.batch_size == torch.Size(batch_size)


def test_stack():
    X = torch.ones(3, 4, 5)
    y = torch.zeros(3, 4, 5, dtype=torch.bool)
    batch_size = [3, 4]
    data1 = MyData(X=X, y=y, batch_size=batch_size)
    data2 = MyData(X=X, y=y, batch_size=batch_size)
    stacked_tdc = torch.stack([data1, data2], 0)
    assert stacked_tdc.X.shape == torch.Size([2, 3, 4, 5])
    assert (stacked_tdc.X == 1).all()
    assert isinstance(stacked_tdc.tensordict, LazyStackedTensorDict)


def test_cat():
    X = torch.ones(3, 4, 5)
    y = torch.zeros(3, 4, 5, dtype=torch.bool)
    batch_size = [3, 4]
    data1 = MyData(X=X, y=y, batch_size=batch_size)
    data2 = MyData(X=X, y=y, batch_size=batch_size)
    stacked_tdc = torch.cat([data1, data2], 0)
    assert stacked_tdc.X.shape == torch.Size([6, 4, 5])
    assert (stacked_tdc.X == 1).all()
    assert isinstance(stacked_tdc.tensordict, TensorDict)


def test_reshape():
    X = torch.ones(3, 4, 5)
    y = torch.zeros(3, 4, 5, dtype=torch.bool)
    batch_size = [3, 4]
    data = MyData(X=X, y=y, batch_size=batch_size)
    stacked_tdc = data.reshape(-1)
    assert stacked_tdc.X.shape == torch.Size([12, 5])
    assert (stacked_tdc.X == 1).all()
    assert isinstance(stacked_tdc.tensordict, TensorDict)


def test_view():
    X = torch.ones(3, 4, 5)
    y = torch.zeros(3, 4, 5, dtype=torch.bool)
    batch_size = [3, 4]
    data = MyData(X=X, y=y, batch_size=batch_size)
    stacked_tdc = data.view(-1)
    assert stacked_tdc.X.shape == torch.Size([12, 5])
    assert (stacked_tdc.X == 1).all()
    assert isinstance(stacked_tdc.tensordict, _ViewedTensorDict)


def test_permute():
    X = torch.ones(3, 4, 5)
    y = torch.zeros(3, 4, 5, dtype=torch.bool)
    batch_size = [3, 4]
    data = MyData(X=X, y=y, batch_size=batch_size)
    stacked_tdc = data.permute(1, 0)
    assert stacked_tdc.X.shape == torch.Size([4, 3, 5])
    assert (stacked_tdc.X == 1).all()
    assert isinstance(stacked_tdc.tensordict, _PermutedTensorDict)


def test_nested():
    @tensordictclass
    class MyDataNested:
        X: torch.Tensor
        y: MyDataNested = None

    X = torch.ones(3, 4, 5)
    batch_size = [3, 4]
    data_nest = MyDataNested(X=X, batch_size=batch_size)
    data = MyDataNested(X=X, y=data_nest, batch_size=batch_size)
    assert isinstance(data.y, MyDataNested), type(data.y)


@pytest.mark.parametrize("any_to_td", [True, False])
def test_nested_heterogeneous(any_to_td):
    @tensordictclass
    class MyDataNest:
        X: torch.Tensor

    @tensordictclass
    class MyDataParent:
        W: Any
        X: Tensor
        z: TensorDictBase
        y: MyDataNest

    batch_size = [3, 4]
    if any_to_td:
        W = TensorDict({}, batch_size)
    else:
        W = torch.zeros(*batch_size, 1)
    X = torch.ones(3, 4, 5)
    data_nest = MyDataNest(X=X, batch_size=batch_size)
    td = TensorDict({}, batch_size)
    data = MyDataParent(X=X, y=data_nest, z=td, W=W, batch_size=batch_size)
    assert isinstance(data.y, MyDataNest)
    assert isinstance(data.y.X, Tensor)
    assert isinstance(data.X, Tensor)
    if not any_to_td:
        assert isinstance(data.W, Tensor)
    else:
        assert isinstance(data.W, TensorDict)
    assert isinstance(data, MyDataParent)
    assert isinstance(data.z, TensorDict)
    assert isinstance(data.tensordict["y"], TensorDict)


@pytest.mark.parametrize("any_to_td", [True, False])
def test_setattr(any_to_td):
    @tensordictclass
    class MyDataNest:
        X: torch.Tensor

    @tensordictclass
    class MyDataParent:
        W: Any
        X: Tensor
        z: TensorDictBase
        y: MyDataNest

    batch_size = [3, 4]
    if any_to_td:
        W = TensorDict({}, batch_size)
    else:
        W = torch.zeros(*batch_size, 1)
    X = torch.ones(3, 4, 5)
    X_clone = X.clone()
    td = TensorDict({}, batch_size)
    td_clone = td.clone()
    data_nest = MyDataNest(X=X, batch_size=batch_size)
    data = MyDataParent(X=X, y=data_nest, z=td, W=W, batch_size=batch_size)
    data_nest_clone = data_nest.clone()
    assert type(data_nest_clone) is type(data_nest)
    data.y = data_nest_clone
    assert data.tensordict["y"] is not data_nest.tensordict
    assert data.tensordict["y"] is data_nest_clone.tensordict, (
        type(data.tensordict["y"]),
        type(data_nest.tensordict),
    )
    data.X = X_clone
    assert data.tensordict["X"] is X_clone
    data.z = td_clone
    assert data.tensordict["z"] is td_clone
    # check that you can't mess up the batch_size
    with pytest.raises(
        RuntimeError, match=re.escape("the tensor smth has shape torch.Size([1]) which")
    ):
        data.z = TensorDict({"smth": torch.zeros(1)}, [])
    # check that you can't write any attribute
    with pytest.raises(AttributeError, match=re.escape("Cannot set the attribute")):
        data.newattr = TensorDict({"smth": torch.zeros(1)}, [])


def test_default():
    @tensordictclass
    class MyData:
        X: torch.Tensor = None  # TODO: do we want to allow any default, say an integer?
        y: torch.Tensor = torch.ones(3, 4, 5)

    data = MyData(batch_size=[3, 4])
    assert data.__dict__["y"] is None
    assert (data.y == 1).all()
    assert data.X is None
    data.X = torch.zeros(3, 4, 1)
    assert (data.X == 0).all()

    MyData(batch_size=[3])
    MyData(batch_size=[])
    with pytest.raises(RuntimeError, match="batch_size are incongruent"):
        MyData(batch_size=[4])


def test_defaultfactory():
    @tensordictclass
    class MyData:
        X: torch.Tensor = None  # TODO: do we want to allow any default, say an integer?
        y: torch.Tensor = dataclasses.field(default_factory=torch.ones(3, 4, 5))

    data = MyData(batch_size=[3, 4])
    assert data.__dict__["y"] is None
    assert (data.y == 1).all()
    assert data.X is None
    data.X = torch.zeros(3, 4, 1)
    assert (data.X == 0).all()

    MyData(batch_size=[3])
    MyData(batch_size=[])
    with pytest.raises(RuntimeError, match="batch_size are incongruent"):
        MyData(batch_size=[4])


def test_kjt():
    try:
        from torchrec import KeyedJaggedTensor
    except ImportError:
        pytest.skip("TorchRec not installed.")

    def _get_kjt():
        values = torch.Tensor([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0])
        weights = torch.Tensor([1.0, 0.5, 1.5, 1.0, 0.5, 1.0, 1.0, 1.5, 1.0, 1.0, 1.0])
        keys = ["index_0", "index_1", "index_2"]
        offsets = torch.IntTensor([0, 2, 2, 3, 4, 5, 8, 9, 10, 11])

        jag_tensor = KeyedJaggedTensor(
            values=values,
            keys=keys,
            offsets=offsets,
            weights=weights,
        )
        return jag_tensor

    kjt = _get_kjt()

    @tensordictclass
    class MyData:
        X: torch.Tensor
        y: KeyedJaggedTensor

    data = MyData(X=torch.zeros(3, 1), y=kjt, batch_size=[3])
    subdata = data[:2]
    assert (
        subdata.y["index_0"].to_padded_dense() == torch.tensor([[1.0, 2.0], [0.0, 0.0]])
    ).all()

    subdata = data[[0, 2]]
    assert (
        subdata.y["index_0"].to_padded_dense() == torch.tensor([[1.0, 2.0], [3.0, 0.0]])
    ).all()


if __name__ == "__main__":
    args, unknown = argparse.ArgumentParser().parse_known_args()
    pytest.main([__file__, "--capture", "no", "--exitfirst"] + unknown)
