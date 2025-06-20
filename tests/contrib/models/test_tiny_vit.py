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

import sys

import pytest
import torch

from kornia.contrib.models.tiny_vit import TinyViT
from kornia.core import Tensor

from testing.base import BaseTester


class TestTinyViT(BaseTester):
    @pytest.mark.parametrize("img_size", [224, 256])
    def test_smoke(self, device, dtype, img_size):
        model = TinyViT(img_size=img_size).to(device=device, dtype=dtype)
        data = torch.randn(1, 3, img_size, img_size, device=device, dtype=dtype)

        out = model(data)
        assert isinstance(out, Tensor)

    @pytest.mark.slow
    @pytest.mark.parametrize("num_classes", [10, 100])
    @pytest.mark.parametrize("batch_size", [1, 3])
    def test_cardinality(self, device, dtype, batch_size, num_classes):
        model = TinyViT(num_classes=num_classes).to(device=device, dtype=dtype)
        data = torch.rand(batch_size, 3, model.img_size, model.img_size, device=device, dtype=dtype)

        out = model(data)
        assert out.shape == (batch_size, num_classes)

    @pytest.mark.skip("not implemented")
    def test_exception(self): ...

    @pytest.mark.skip("not implemented")
    def test_gradcheck(self): ...

    @pytest.mark.skip("not implemented")
    def test_module(self): ...

    # @pytest.mark.skipif(sys.version_info.major == 3 and sys.version_info.minor == 8, reason="not working for py3.8")
    @pytest.mark.skip(reason="SDAA not support backend='inductor'")
    def test_dynamo(self, device, dtype, torch_optimizer):
        op = TinyViT().to(device=device, dtype=dtype)
        img = torch.rand(1, 3, op.img_size, op.img_size, device=device, dtype=dtype)

        op_optimized = torch_optimizer(op)
        self.assert_close(op(img), op_optimized(img))

    @pytest.mark.slow
    @pytest.mark.parametrize("pretrained", [False, True])
    @pytest.mark.parametrize("variant", ["5m", "11m", "21m"])
    def test_from_config(self, variant, pretrained):
        model = TinyViT.from_config(variant, pretrained=pretrained)
        assert isinstance(model, TinyViT)

    @pytest.mark.slow
    @pytest.mark.parametrize("num_classes", [1000, 8])
    @pytest.mark.parametrize("img_size", [224, 256])
    def test_pretrained(self, img_size, num_classes):
        model = TinyViT.from_config("5m", img_size=img_size, num_classes=num_classes, pretrained=True)
        assert isinstance(model, TinyViT)

    @pytest.mark.slow
    def test_mobile_sam_backbone(self, device, dtype):
        img_size = 1024
        batch_size = 1
        model = TinyViT.from_config("5m", img_size=img_size, mobile_sam=True).to(device=device, dtype=dtype)
        data = torch.randn(batch_size, 3, img_size, img_size, device=device, dtype=dtype)

        out = model(data)
        assert out.shape == (batch_size, 256, img_size // 16, img_size // 16)
