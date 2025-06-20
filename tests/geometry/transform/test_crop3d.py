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
from kornia.utils._compat import torch_version

from testing.base import BaseTester


class TestCropAndResize3D(BaseTester):
    def test_crop(self, device, dtype):
        inp = torch.arange(0.0, 64.0, device=device, dtype=dtype).view(1, 1, 4, 4, 4)

        depth, height, width = 2, 2, 2
        expected = torch.tensor(
            [[[[[25.1667, 27.1667], [30.5000, 32.5000]], [[46.5000, 48.5000], [51.8333, 53.8333]]]]],
            device=device,
            dtype=dtype,
        )

        boxes = torch.tensor(
            [[[0, 0, 1], [3, 0, 1], [3, 2, 1], [0, 2, 1], [0, 0, 3], [3, 0, 3], [3, 2, 3], [0, 2, 3]]],
            device=device,
            dtype=dtype,
        )  # 1x8x3

        patches = kornia.geometry.transform.crop_and_resize3d(inp, boxes, (depth, height, width))
        self.assert_close(patches, expected)

    def test_crop_batch(self, device, dtype):
        inp = torch.cat(
            [
                torch.arange(0.0, 64.0, device=device, dtype=dtype).view(1, 1, 4, 4, 4),
                torch.arange(0.0, 128.0, step=2, device=device, dtype=dtype).view(1, 1, 4, 4, 4),
            ],
            dim=0,
        )

        depth, height, width = 2, 2, 2
        expected = torch.tensor(
            [
                [[[[16.0000, 19.0000], [24.0000, 27.0000]], [[48.0000, 51.0000], [56.0000, 59.0000]]]],
                [[[[0.0000, 6.0000], [16.0000, 22.0000]], [[64.0000, 70.0000], [80.0000, 86.0000]]]],
            ],
            device=device,
            dtype=dtype,
        )

        boxes = torch.tensor(
            [
                [[0, 0, 1], [3, 0, 1], [3, 2, 1], [0, 2, 1], [0, 0, 3], [3, 0, 3], [3, 2, 3], [0, 2, 3]],
                [[0, 0, 0], [3, 0, 0], [3, 2, 0], [0, 2, 0], [0, 0, 2], [3, 0, 2], [3, 2, 2], [0, 2, 2]],
            ],
            device=device,
            dtype=dtype,
        )  # 2x8x3

        patches = kornia.geometry.transform.crop_and_resize3d(inp, boxes, (depth, height, width), align_corners=True)
        self.assert_close(patches, expected)

    def test_gradcheck(self, device):
        img = torch.arange(0.0, 64.0, device=device, dtype=torch.float64).view(1, 1, 4, 4, 4)

        boxes = torch.tensor(
            [[[0, 0, 1], [3, 0, 1], [3, 2, 1], [0, 2, 1], [0, 0, 3], [3, 0, 3], [3, 2, 3], [0, 2, 3]]],
            device=device,
            dtype=torch.float64,
        )  # 1x8x3

        self.gradcheck(kornia.geometry.transform.crop_and_resize3d, (img, boxes, (4, 3, 2)))

    @pytest.mark.skip(reason="SDAA not support backend='inductor'")
    def test_dynamo(self, device, dtype, torch_optimizer):
        # Define script
        op = kornia.geometry.transform.crop_and_resize3d
        op_script = torch_optimizer(op)

        img = torch.arange(0.0, 64.0, device=device, dtype=dtype).view(1, 1, 4, 4, 4)

        boxes = torch.tensor(
            [[[0, 0, 1], [3, 0, 1], [3, 2, 1], [0, 2, 1], [0, 0, 3], [3, 0, 3], [3, 2, 3], [0, 2, 3]]],
            device=device,
            dtype=dtype,
        )  # 1x8x3

        actual = op_script(img, boxes, (4, 3, 2))
        expected = op(img, boxes, (4, 3, 2))
        self.assert_close(actual, expected)


class TestCenterCrop3D(BaseTester):
    @pytest.mark.parametrize("crop_size", [(3, 5, 7), (5, 3, 7), (7, 3, 5)])
    def test_center_crop_357(self, crop_size, device, dtype):
        inp = torch.arange(0.0, 343.0, device=device, dtype=dtype).view(1, 1, 7, 7, 7)
        expected = inp[
            :,
            :,
            (inp.size(2) // 2 - crop_size[0] // 2) : (inp.size(2) // 2 + crop_size[0] // 2 + 1),
            (inp.size(3) // 2 - crop_size[1] // 2) : (inp.size(3) // 2 + crop_size[1] // 2 + 1),
            (inp.size(4) // 2 - crop_size[2] // 2) : (inp.size(4) // 2 + crop_size[2] // 2 + 1),
        ]
        out_crop = kornia.geometry.transform.center_crop3d(inp, crop_size, align_corners=True)
        self.assert_close(out_crop, expected, rtol=1e-4, atol=1e-4)

    @pytest.mark.parametrize("crop_size", [(3, 5, 7), (5, 3, 7), (7, 3, 5)])
    def test_center_crop_357_batch(self, crop_size, device, dtype):
        inp = torch.cat(
            [
                torch.arange(0.0, 343.0, device=device, dtype=dtype).view(1, 1, 7, 7, 7),
                torch.arange(343.0, 686.0, device=device, dtype=dtype).view(1, 1, 7, 7, 7),
            ]
        )
        expected = inp[
            :,
            :,
            (inp.size(2) // 2 - crop_size[0] // 2) : (inp.size(2) // 2 + crop_size[0] // 2 + 1),
            (inp.size(3) // 2 - crop_size[1] // 2) : (inp.size(3) // 2 + crop_size[1] // 2 + 1),
            (inp.size(4) // 2 - crop_size[2] // 2) : (inp.size(4) // 2 + crop_size[2] // 2 + 1),
        ]
        out_crop = kornia.geometry.transform.center_crop3d(inp, crop_size, align_corners=True)
        self.assert_close(out_crop, expected, rtol=1e-4, atol=1e-4)

    def test_gradcheck(self, device):
        img = torch.arange(0.0, 343.0, device=device, dtype=torch.float64).view(1, 1, 7, 7, 7)

        self.gradcheck(kornia.geometry.transform.center_crop3d, (img, (3, 5, 7)))

    # @pytest.mark.skipif(
    #     torch_version() == "2.1.0",
    #     reason=(
    #         "https://github.com/pytorch/pytorch/issues/110680"
    #         " -  unsupported operand type(s) for @: 'FakeTensor' and 'FakeTensor' on `normalize_homography3d`"
    #     ),
    # )
    @pytest.mark.skip(reason="SDAA not support backend='inductor'")
    def test_dynamo(self, device, dtype, torch_optimizer):
        # Define script
        op = kornia.geometry.transform.center_crop3d
        op_script = torch_optimizer(op)
        img = torch.ones(4, 3, 5, 6, 7, device=device, dtype=dtype)

        actual = op_script(img, (4, 3, 2))
        expected = kornia.geometry.transform.center_crop3d(img, (4, 3, 2))
        self.assert_close(actual, expected, rtol=1e-4, atol=1e-4)


class TestCropByBoxes3D(BaseTester):
    def test_crop_by_boxes_no_resizing(self, device, dtype):
        inp = torch.arange(0.0, 343.0, device=device, dtype=dtype).view(1, 1, 7, 7, 7)
        src_box = torch.tensor(
            [
                [
                    [1.0, 1.0, 1.0],
                    [3.0, 1.0, 1.0],
                    [3.0, 3.0, 1.0],
                    [1.0, 3.0, 1.0],
                    [1.0, 1.0, 2.0],
                    [3.0, 1.0, 2.0],
                    [3.0, 3.0, 2.0],
                    [1.0, 3.0, 2.0],
                ]
            ],
            device=device,
            dtype=dtype,
        )  # 1x8x3
        dst_box = torch.tensor(
            [
                [
                    [0.0, 0.0, 0.0],
                    [2.0, 0.0, 0.0],
                    [2.0, 2.0, 0.0],
                    [0.0, 2.0, 0.0],
                    [0.0, 0.0, 1.0],
                    [2.0, 0.0, 1.0],
                    [2.0, 2.0, 1.0],
                    [0.0, 2.0, 1.0],
                ]
            ],
            device=device,
            dtype=dtype,
        )  # 1x8x3

        expected = inp[:, :, 1:3, 1:4, 1:4]

        patches = kornia.geometry.transform.crop_by_boxes3d(inp, src_box, dst_box, align_corners=True)
        self.assert_close(patches, expected, rtol=1e-4, atol=1e-4)

    def test_crop_by_boxes_resizing(self, device, dtype):
        inp = torch.arange(0.0, 343.0, device=device, dtype=dtype).view(1, 1, 7, 7, 7)
        src_box = torch.tensor(
            [
                [
                    [1.0, 1.0, 1.0],
                    [3.0, 1.0, 1.0],
                    [3.0, 3.0, 1.0],
                    [1.0, 3.0, 1.0],
                    [1.0, 1.0, 2.0],
                    [3.0, 1.0, 2.0],
                    [3.0, 3.0, 2.0],
                    [1.0, 3.0, 2.0],
                ]
            ],
            device=device,
            dtype=dtype,
        )  # 1x8x3
        dst_box = torch.tensor(
            [
                [
                    [0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [1.0, 1.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                    [1.0, 0.0, 1.0],
                    [1.0, 1.0, 1.0],
                    [0.0, 1.0, 1.0],
                ]
            ],
            device=device,
            dtype=dtype,
        )  # 1x8x3

        expected = torch.tensor(
            [[[[[57.0000, 59.0000], [71.0000, 73.0000]], [[106.0000, 108.0000], [120.0000, 122.0000]]]]],
            device=device,
            dtype=dtype,
        )

        patches = kornia.geometry.transform.crop_by_boxes3d(inp, src_box, dst_box, align_corners=True)
        self.assert_close(patches, expected, rtol=1e-4, atol=1e-4)

    @pytest.mark.skip(reason="SDAA not support backend='inductor'")
    def test_dynamo(self, device, dtype, torch_optimizer):
        # Define script
        op = kornia.geometry.transform.crop_by_boxes3d
        op_script = torch_optimizer(op)
        # Define input
        inp = torch.randn((1, 1, 7, 7, 7), device=device, dtype=dtype)
        src_box = torch.tensor(
            [
                [
                    [1.0, 1.0, 1.0],
                    [3.0, 1.0, 1.0],
                    [3.0, 3.0, 1.0],
                    [1.0, 3.0, 1.0],
                    [1.0, 1.0, 2.0],
                    [3.0, 1.0, 2.0],
                    [3.0, 3.0, 2.0],
                    [1.0, 3.0, 2.0],
                ]
            ],
            device=device,
            dtype=dtype,
        )  # 1x8x3
        dst_box = torch.tensor(
            [
                [
                    [0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [1.0, 1.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                    [1.0, 0.0, 1.0],
                    [1.0, 1.0, 1.0],
                    [0.0, 1.0, 1.0],
                ]
            ],
            device=device,
            dtype=dtype,
        )  # 1x8x3

        actual = op_script(inp, src_box, dst_box, align_corners=True)
        expected = op(inp, src_box, dst_box, align_corners=True)
        self.assert_close(actual, expected, rtol=1e-4, atol=1e-4)

    def test_gradcheck(self, device):
        dtype = torch.float64
        inp = torch.randn((1, 1, 7, 7, 7), device=device, dtype=dtype)
        src_box = torch.tensor(
            [
                [
                    [1.0, 1.0, 1.0],
                    [3.0, 1.0, 1.0],
                    [3.0, 3.0, 1.0],
                    [1.0, 3.0, 1.0],
                    [1.0, 1.0, 2.0],
                    [3.0, 1.0, 2.0],
                    [3.0, 3.0, 2.0],
                    [1.0, 3.0, 2.0],
                ]
            ],
            device=device,
            dtype=dtype,
        )  # 1x8x3
        dst_box = torch.tensor(
            [
                [
                    [0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [1.0, 1.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                    [1.0, 0.0, 1.0],
                    [1.0, 1.0, 1.0],
                    [0.0, 1.0, 1.0],
                ]
            ],
            device=device,
            dtype=dtype,
        )  # 1x8x3

        self.gradcheck(
            kornia.geometry.transform.crop_by_boxes3d, (inp, src_box, dst_box), requires_grad=(True, False, False)
        )
