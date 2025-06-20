# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright 2018 Kornia Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest
import torch

from kornia.filters import Laplacian, get_laplacian_kernel1d, get_laplacian_kernel2d, laplacian

from testing.base import BaseTester, assert_close


@pytest.mark.parametrize("window_size", [5, 11])
def test_get_laplacian_kernel1d(window_size, device, dtype):
    actual = get_laplacian_kernel1d(window_size, device=device, dtype=dtype)
    expected = torch.zeros(1, device=device, dtype=dtype)

    assert actual.shape == (window_size,)
    assert_close(actual.sum(), expected.sum())


@pytest.mark.parametrize("window_size", [5, 11, (3, 3)])
def test_get_laplacian_kernel2d(window_size, device, dtype):
    actual = get_laplacian_kernel2d(window_size, device=device, dtype=dtype)
    expected = torch.zeros(1, device=device, dtype=dtype)
    expected_shape = window_size if isinstance(window_size, tuple) else (window_size, window_size)

    assert actual.shape == expected_shape
    assert_close(actual.sum(), expected.sum())


def test_get_laplacian_kernel1d_exact(device, dtype):
    actual = get_laplacian_kernel1d(5, device=device, dtype=dtype)
    expected = torch.tensor([1.0, 1.0, -4.0, 1.0, 1.0], device=device, dtype=dtype)
    assert_close(expected, actual)


def test_get_laplacian_kernel2d_exact(device, dtype):
    actual = get_laplacian_kernel2d(7, device=device, dtype=dtype)
    expected = torch.tensor(
        [
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, -48.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        ],
        device=device,
        dtype=dtype,
    )
    assert_close(expected, actual)


class TestLaplacian(BaseTester):
    @pytest.mark.parametrize("shape", [(1, 4, 8, 15), (2, 3, 11, 7)])
    @pytest.mark.parametrize("kernel_size", [5, (11, 7), (3, 3)])
    @pytest.mark.parametrize("normalized", [True, False])
    def test_smoke(self, shape, kernel_size, normalized, device, dtype):
        data = torch.rand(shape, device=device, dtype=dtype)
        actual = laplacian(data, kernel_size, "reflect", normalized)
        assert isinstance(actual, torch.Tensor)
        assert actual.shape == shape

    @pytest.mark.parametrize("shape", [(1, 4, 8, 15), (2, 3, 11, 7)])
    @pytest.mark.parametrize("kernel_size", [5, (11, 7), 3])
    def test_cardinality(self, shape, kernel_size, device, dtype):
        sample = torch.rand(shape, device=device, dtype=dtype)
        actual = laplacian(sample, kernel_size)
        assert actual.shape == shape

    @pytest.mark.skip(reason="Nothing to test.")
    def test_exception(self): ...

    def test_noncontiguous(self, device, dtype):
        batch_size = 3
        sample = torch.rand(3, 5, 5, device=device, dtype=dtype).expand(batch_size, -1, -1, -1)

        kernel_size = 3
        actual = laplacian(sample, kernel_size)
        assert actual.is_contiguous()

    def test_gradcheck(self, device):
        # test parameters
        batch_shape = (1, 2, 5, 7)
        kernel_size = 3

        # evaluate function gradient
        sample = torch.rand(batch_shape, device=device, dtype=torch.float64)
        self.gradcheck(laplacian, (sample, kernel_size))

    def test_module(self, device, dtype):
        params = [3]
        op = laplacian
        op_module = Laplacian(*params)

        img = torch.ones(1, 3, 5, 5, device=device, dtype=dtype)
        self.assert_close(op(img, *params), op_module(img))

    # @pytest.mark.parametrize("kernel_size", [5, (5, 7)])
    # @pytest.mark.parametrize("batch_size", [1, 2])
    @pytest.mark.skip(reason="SDAA not support backend='inductor'")
    def test_dynamo(self, batch_size, kernel_size, device, dtype, torch_optimizer):
        data = torch.ones(batch_size, 3, 10, 10, device=device, dtype=dtype)
        op = Laplacian(kernel_size)
        op_optimized = torch_optimizer(op)

        self.assert_close(op(data), op_optimized(data))
