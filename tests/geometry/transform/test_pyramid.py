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

import kornia

from testing.base import BaseTester


class TestPyrUp(BaseTester):
    def test_shape(self, device, dtype):
        inp = torch.zeros(1, 2, 4, 4, device=device, dtype=dtype)
        pyr = kornia.geometry.PyrUp()
        assert pyr(inp).shape == (1, 2, 8, 8)

    def test_shape_batch(self, device, dtype):
        inp = torch.zeros(2, 2, 4, 4, device=device, dtype=dtype)
        pyr = kornia.geometry.PyrUp()
        assert pyr(inp).shape == (2, 2, 8, 8)

    def test_gradcheck(self, device):
        img = torch.rand(1, 2, 5, 4, device=device, dtype=torch.float64)
        self.gradcheck(kornia.geometry.pyrup, (img,), nondet_tol=1e-8)


class TestPyrDown(BaseTester):
    def test_shape(self, device, dtype):
        inp = torch.zeros(1, 2, 4, 4, device=device, dtype=dtype)
        pyr = kornia.geometry.PyrDown()
        assert pyr(inp).shape == (1, 2, 2, 2)

    def test_shape_custom_factor(self, device, dtype):
        inp = torch.zeros(1, 2, 9, 9, device=device, dtype=dtype)
        pyr = kornia.geometry.PyrDown(factor=3.0)
        assert pyr(inp).shape == (1, 2, 3, 3)

    def test_shape_batch(self, device, dtype):
        inp = torch.zeros(2, 2, 4, 4, device=device, dtype=dtype)
        pyr = kornia.geometry.PyrDown()
        assert pyr(inp).shape == (2, 2, 2, 2)

    def test_symmetry_preserving(self, device, dtype):
        inp = torch.zeros(1, 1, 6, 6, device=device, dtype=dtype)
        inp[:, :, 2:4, 2:4] = 1.0
        pyr_out = kornia.geometry.PyrDown()(inp).squeeze()
        self.assert_close(pyr_out, pyr_out.flip(0))
        self.assert_close(pyr_out, pyr_out.flip(1))

    def test_gradcheck(self, device):
        img = torch.rand(1, 2, 5, 4, device=device, dtype=torch.float64)
        self.gradcheck(kornia.geometry.pyrdown, (img,), nondet_tol=1e-8)


class TestScalePyramid(BaseTester):
    def test_shape_tuple(self, device, dtype):
        inp = torch.zeros(3, 2, 41, 41, device=device, dtype=dtype)
        SP = kornia.geometry.ScalePyramid(n_levels=1, min_size=30)
        out = SP(inp)
        assert len(out) == 3
        assert len(out[0]) == 1
        assert len(out[1]) == 1
        assert len(out[2]) == 1

    def test_shape_batch(self, device, dtype):
        inp = torch.zeros(3, 2, 31, 31, device=device, dtype=dtype)
        SP = kornia.geometry.ScalePyramid(n_levels=1)
        sp, _, _ = SP(inp)
        assert sp[0].shape == (3, 2, 3 + 1, 31, 31)

    def test_shape_batch_double(self, device, dtype):
        inp = torch.zeros(3, 2, 31, 31, device=device, dtype=dtype)
        SP = kornia.geometry.ScalePyramid(n_levels=1, double_image=True)
        sp, _, _ = SP(inp)
        assert sp[0].shape == (3, 2, 1 + 3, 62, 62)

    def test_n_levels_shape(self, device, dtype):
        inp = torch.zeros(1, 1, 32, 32, device=device, dtype=dtype)
        SP = kornia.geometry.ScalePyramid(n_levels=3)
        sp, _, _ = SP(inp)
        assert sp[0].shape == (1, 1, 3 + 3, 32, 32)

    def test_blur_order(self, device, dtype):
        inp = torch.rand(1, 1, 31, 31, device=device, dtype=dtype)
        SP = kornia.geometry.ScalePyramid(n_levels=3)
        sp, _, _ = SP(inp)
        for _, pyr_level in enumerate(sp):
            for _, img in enumerate(pyr_level):
                img = img.squeeze().view(3, -1)
                max_per_blur_level_val, _ = img.max(dim=1)
                assert torch.argmax(max_per_blur_level_val).item() == 0

    def test_symmetry_preserving(self, device, dtype):
        PS = 16
        R = 2
        inp = torch.zeros(1, 1, PS, PS, device=device, dtype=dtype)
        inp[..., PS // 2 - R : PS // 2 + R, PS // 2 - R : PS // 2 + R] = 1.0
        SP = kornia.geometry.ScalePyramid(n_levels=3)
        sp, _, _ = SP(inp)
        for _, pyr_level in enumerate(sp):
            for _, img in enumerate(pyr_level):
                img = img.squeeze()
                self.assert_close(img, img.flip(1))
                self.assert_close(img, img.flip(2))

    def test_gradcheck(self, device):
        img = torch.rand(1, 2, 7, 9, device=device, dtype=torch.float64)
        from kornia.geometry import ScalePyramid as SP

        def sp_tuple(img):
            sp, _, _ = SP()(img)
            return tuple(sp)

        self.gradcheck(sp_tuple, (img,), nondet_tol=1e-4)


class TestBuildPyramid(BaseTester):
    def test_smoke(self, device, dtype):
        sample = torch.ones(1, 2, 4, 5, device=device, dtype=dtype)
        pyramid = kornia.geometry.transform.build_pyramid(sample, max_level=1)
        assert len(pyramid) == 1
        assert pyramid[0].shape == (1, 2, 4, 5)

    @pytest.mark.parametrize("batch_size", (1, 2, 3))
    @pytest.mark.parametrize("channels", (1, 3))
    @pytest.mark.parametrize("max_level", (2, 3, 4))
    def test_num_levels(self, batch_size, channels, max_level, device, dtype):
        height, width = 16, 20
        sample = torch.rand(batch_size, channels, height, width, device=device, dtype=dtype)
        pyramid = kornia.geometry.transform.build_pyramid(sample, max_level)
        assert len(pyramid) == max_level
        for i in range(1, max_level):
            img = pyramid[i]
            denom = 2**i
            expected_shape = (batch_size, channels, height // denom, width // denom)
            assert img.shape == expected_shape

    def test_gradcheck(self, device):
        max_level = 1
        batch_size, channels, height, width = 1, 2, 7, 9
        img = torch.rand(batch_size, channels, height, width, device=device, dtype=torch.float64)
        self.gradcheck(kornia.geometry.transform.build_pyramid, (img, max_level))


class TestBuildLaplacianPyramid(BaseTester):
    def test_smoke(self, device, dtype):
        sample = torch.ones(1, 2, 4, 5, device=device, dtype=dtype)
        pyramid = kornia.geometry.transform.build_laplacian_pyramid(sample, max_level=1)
        assert len(pyramid) == 1
        assert pyramid[0].shape == (1, 2, 4, 5)

    @pytest.mark.parametrize("batch_size", (1, 2, 3))
    @pytest.mark.parametrize("channels", (1, 3))
    @pytest.mark.parametrize("max_level", (2, 3, 4))
    def test_num_levels(self, batch_size, channels, max_level, device, dtype):
        height, width = 16, 32
        sample = torch.rand(batch_size, channels, height, width, device=device, dtype=dtype)
        pyramid = kornia.geometry.transform.build_laplacian_pyramid(sample, max_level)
        assert len(pyramid) == max_level
        for i in range(1, max_level):
            img = pyramid[i]
            denom = 2**i
            expected_shape = (batch_size, channels, height // denom, width // denom)
            assert img.shape == expected_shape

    def test_gradcheck(self, device):
        max_level = 1
        batch_size, channels, height, width = 1, 2, 7, 9
        img = torch.rand(batch_size, channels, height, width, device=device, dtype=torch.float64)
        self.gradcheck(kornia.geometry.transform.build_laplacian_pyramid, (img, max_level), nondet_tol=1e-8)


class TestUpscaleDouble(BaseTester):
    @pytest.mark.parametrize("shape", ((5, 5), (2, 5, 5), (1, 2, 5, 5)))
    def test_smoke(self, shape, device, dtype):
        x = self.prepare_data(shape, device, dtype)
        assert kornia.geometry.transform.upscale_double(x) is not None

    def test_exception(self):
        with pytest.raises(TypeError):
            kornia.geometry.transform.upscale_double(None)

    @pytest.mark.parametrize("shape", ((5, 5), (2, 5, 5), (1, 2, 5, 5)))
    def test_cardinality(self, shape, device, dtype):
        x = self.prepare_data(shape, device, dtype)
        actual = kornia.geometry.transform.upscale_double(x)

        h, w = shape[-2:]
        expected = (*shape[:-2], h * 2, w * 2)

        assert tuple(actual.shape) == expected

    @pytest.mark.skip(reason="SDAA not support backend='inductor'")
    def test_dynamo(self, device, dtype, torch_optimizer):
        img = self.prepare_data((1, 2, 5, 5), device, dtype)
        op = kornia.geometry.transform.upscale_double
        op_optimized = torch_optimizer(op)
        self.assert_close(op(img), op_optimized(img))

    @pytest.mark.grad()
    def test_gradcheck(self, device):
        x = self.prepare_data((1, 2, 5, 5), device)
        self.gradcheck(kornia.geometry.transform.upscale_double, (x,), rtol=5e-2)

    @pytest.mark.parametrize("shape", ((5, 5), (2, 5, 5), (1, 2, 5, 5)))
    def test_upscale_double_and_back(self, shape, device, dtype):
        x = self.prepare_data(shape, device, dtype)
        upscaled = kornia.geometry.transform.upscale_double(x)

        expected = torch.tensor(
            [
                [
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
                    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
                    [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5],
                    [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                    [2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
                    [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0],
                    [3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5],
                    [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0],
                    [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0],
                ],
                [
                    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0],
                    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0],
                    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0],
                    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0],
                    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0],
                    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0],
                    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0],
                    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0],
                    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0],
                    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0],
                ],
            ],
            device=device,
            dtype=dtype,
        )

        if len(shape) == 2:
            expected = expected[0]
        elif len(shape) == 4:
            expected = expected[None]

        self.assert_close(upscaled, expected)

        downscaled_back = upscaled[..., ::2, ::2]
        self.assert_close(x, downscaled_back)

    @staticmethod
    def prepare_data(shape, device, dtype=torch.float32):
        xm = torch.tensor(
            [[0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3], [4, 4, 4, 4, 4]],
            device=device,
            dtype=dtype,
        )
        ym = torch.tensor(
            [[0, 1, 2, 3, 4], [0, 1, 2, 3, 4], [0, 1, 2, 3, 4], [0, 1, 2, 3, 4], [0, 1, 2, 3, 4]],
            device=device,
            dtype=dtype,
        )

        x = torch.zeros(shape, device=device, dtype=dtype)
        if len(shape) == 2:
            x = xm
        else:
            x[..., 0, :, :] = xm
            x[..., 1, :, :] = ym

        return x
