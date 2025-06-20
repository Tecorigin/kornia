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

from kornia.feature.integrated import LightGlueMatcher
from kornia.feature.laf import laf_from_center_scale_ori
from kornia.feature.matching import (
    DescriptorMatcher,
    DescriptorMatcherWithSteerer,
    GeometryAwareDescriptorMatcher,
    match_adalam,
    match_fginn,
    match_mnn,
    match_nn,
    match_smnn,
    match_snn,
)
from kornia.feature.steerers import DiscreteSteerer
from kornia.utils._compat import torch_version_le

from testing.base import BaseTester
from testing.casts import dict_to


class TestMatchNN(BaseTester):
    @pytest.mark.parametrize("num_desc1, num_desc2, dim", [(1, 4, 4), (2, 5, 128), (6, 2, 32)])
    def test_shape(self, num_desc1, num_desc2, dim, device):
        desc1 = torch.rand(num_desc1, dim, device=device)
        desc2 = torch.rand(num_desc2, dim, device=device)

        dists, idxs = match_nn(desc1, desc2)
        assert idxs.shape == (num_desc1, 2)
        assert dists.shape == (num_desc1, 1)

    def test_matching(self, device):
        desc1 = torch.tensor([[0, 0.0], [1, 1], [2, 2], [3, 3.0], [5, 5.0]], device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1], [0, 0.0]], device=device)

        dists, idxs = match_nn(desc1, desc2)
        expected_dists = torch.tensor([0, 0, 0.5, 0, 0], device=device).view(-1, 1)
        expected_idx = torch.tensor([[0, 4], [1, 3], [2, 2], [3, 1], [4, 0]], device=device)
        self.assert_close(dists, expected_dists)
        self.assert_close(idxs, expected_idx)

        dists1, idxs1 = match_nn(desc1, desc2)
        self.assert_close(dists1, expected_dists)
        self.assert_close(idxs1, expected_idx)

    def test_gradcheck(self, device):
        desc1 = torch.rand(5, 8, device=device, dtype=torch.float64)
        desc2 = torch.rand(7, 8, device=device, dtype=torch.float64)
        self.gradcheck(match_mnn, (desc1, desc2), nondet_tol=1e-4)


class TestMatchMNN(BaseTester):
    @pytest.mark.parametrize("num_desc1, num_desc2, dim", [(1, 4, 4), (2, 5, 128), (6, 2, 32)])
    def test_shape(self, num_desc1, num_desc2, dim, device):
        desc1 = torch.rand(num_desc1, dim, device=device)
        desc2 = torch.rand(num_desc2, dim, device=device)

        dists, idxs = match_mnn(desc1, desc2)
        assert idxs.shape[1] == 2
        assert dists.shape[1] == 1
        assert idxs.shape[0] == dists.shape[0]
        assert dists.shape[0] <= num_desc1

    def test_matching(self, device):
        desc1 = torch.tensor([[0, 0.0], [1, 1], [2, 2], [3, 3.0], [5, 5.0]], device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1], [0, 0.0]], device=device)

        dists, idxs = match_mnn(desc1, desc2)
        expected_dists = torch.tensor([0, 0, 0.5, 0, 0], device=device).view(-1, 1)
        expected_idx = torch.tensor([[0, 4], [1, 3], [2, 2], [3, 1], [4, 0]], device=device)
        self.assert_close(dists, expected_dists)
        self.assert_close(idxs, expected_idx)
        matcher = DescriptorMatcher("mnn").to(device)
        dists1, idxs1 = matcher(desc1, desc2)
        self.assert_close(dists1, expected_dists)
        self.assert_close(idxs1, expected_idx)

    def test_gradcheck(self, device):
        desc1 = torch.rand(5, 8, device=device, dtype=torch.float64)
        desc2 = torch.rand(7, 8, device=device, dtype=torch.float64)
        self.gradcheck(match_mnn, (desc1, desc2), nondet_tol=1e-4)


class TestMatchSNN(BaseTester):
    @pytest.mark.parametrize("num_desc1, num_desc2, dim", [(2, 4, 4), (2, 5, 128), (6, 2, 32)])
    def test_shape(self, num_desc1, num_desc2, dim, device):
        desc1 = torch.rand(num_desc1, dim, device=device)
        desc2 = torch.rand(num_desc2, dim, device=device)

        dists, idxs = match_snn(desc1, desc2)
        assert idxs.shape[1] == 2
        assert dists.shape[1] == 1
        assert idxs.shape[0] == dists.shape[0]
        assert dists.shape[0] <= num_desc1

    def test_nomatch(self, device):
        desc1 = torch.tensor([[0, 0.0], [1, 1], [2, 2], [3, 3.0], [5, 5.0]], device=device)
        desc2 = torch.tensor([[5, 5.0]], device=device)

        dists, idxs = match_snn(desc1, desc2, 0.8)
        assert len(dists) == 0
        assert len(idxs) == 0

    def test_matching1(self, device):
        desc1 = torch.tensor([[0, 0.0], [1, 1], [2, 2], [3, 3.0], [5, 5.0]], device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1], [0, 0.0]], device=device)

        dists, idxs = match_snn(desc1, desc2, 0.8)
        expected_dists = torch.tensor([0, 0, 0.35355339059327373, 0, 0], device=device).view(-1, 1)
        expected_idx = torch.tensor([[0, 4], [1, 3], [2, 2], [3, 1], [4, 0]], device=device)
        self.assert_close(dists, expected_dists)
        self.assert_close(idxs, expected_idx)
        matcher = DescriptorMatcher("snn", 0.8).to(device)
        dists1, idxs1 = matcher(desc1, desc2)
        self.assert_close(dists1, expected_dists)
        self.assert_close(idxs1, expected_idx)

    def test_matching2(self, device):
        desc1 = torch.tensor([[0, 0.0], [1, 1], [2, 2], [3, 3.0], [5, 5.0]], device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1], [0, 0.0]], device=device)

        dists, idxs = match_snn(desc1, desc2, 0.1)
        expected_dists = torch.tensor([0.0, 0, 0, 0], device=device).view(-1, 1)
        expected_idx = torch.tensor([[0, 4], [1, 3], [3, 1], [4, 0]], device=device)
        self.assert_close(dists, expected_dists)
        self.assert_close(idxs, expected_idx)
        matcher = DescriptorMatcher("snn", 0.1).to(device)
        dists1, idxs1 = matcher(desc1, desc2)
        self.assert_close(dists1, expected_dists)
        self.assert_close(idxs1, expected_idx)

    def test_gradcheck(self, device):
        desc1 = torch.rand(5, 8, device=device, dtype=torch.float64)
        desc2 = torch.rand(7, 8, device=device, dtype=torch.float64)
        self.gradcheck(match_snn, (desc1, desc2, 0.8), nondet_tol=1e-4)


class TestMatchSMNN(BaseTester):
    @pytest.mark.parametrize("num_desc1, num_desc2, dim", [(2, 4, 4), (2, 5, 128), (6, 2, 32)])
    def test_shape(self, num_desc1, num_desc2, dim, device):
        desc1 = torch.rand(num_desc1, dim, device=device)
        desc2 = torch.rand(num_desc2, dim, device=device)

        dists, idxs = match_smnn(desc1, desc2, 0.8)
        assert idxs.shape[1] == 2
        assert dists.shape[1] == 1
        assert idxs.shape[0] == dists.shape[0]
        assert dists.shape[0] <= num_desc1
        assert dists.shape[0] <= num_desc2

    def test_matching1(self, device):
        desc1 = torch.tensor([[0, 0.0], [1, 1], [2, 2], [3, 3.0], [5, 5.0]], device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1], [0, 0.0]], device=device)

        dists, idxs = match_smnn(desc1, desc2, 0.8)
        expected_dists = torch.tensor([0, 0, 0.5423, 0, 0], device=device).view(-1, 1)
        expected_idx = torch.tensor([[0, 4], [1, 3], [2, 2], [3, 1], [4, 0]], device=device)
        self.assert_close(dists, expected_dists)
        self.assert_close(idxs, expected_idx)
        matcher = DescriptorMatcher("smnn", 0.8).to(device)
        dists1, idxs1 = matcher(desc1, desc2)
        self.assert_close(dists1, expected_dists)
        self.assert_close(idxs1, expected_idx)

    def test_nomatch(self, device):
        desc1 = torch.tensor([[0, 0.0]], device=device)
        desc2 = torch.tensor([[5, 5.0]], device=device)

        dists, idxs = match_smnn(desc1, desc2, 0.8)
        assert len(dists) == 0
        assert len(idxs) == 0

    def test_matching2(self, device):
        desc1 = torch.tensor([[0, 0.0], [1, 1], [2, 2], [3, 3.0], [5, 5.0]], device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1], [0, 0.0]], device=device)

        dists, idxs = match_smnn(desc1, desc2, 0.1)
        expected_dists = torch.tensor([0.0, 0, 0, 0], device=device).view(-1, 1)
        expected_idx = torch.tensor([[0, 4], [1, 3], [3, 1], [4, 0]], device=device)
        self.assert_close(dists, expected_dists)
        self.assert_close(idxs, expected_idx)
        matcher = DescriptorMatcher("smnn", 0.1).to(device)
        dists1, idxs1 = matcher(desc1, desc2)
        self.assert_close(dists1, expected_dists)
        self.assert_close(idxs1, expected_idx)

    @pytest.mark.parametrize(
        "match_type, d1, d2",
        [
            ("nn", 0, 10),
            ("nn", 10, 0),
            ("nn", 0, 0),
            ("snn", 0, 10),
            ("snn", 10, 0),
            ("snn", 0, 0),
            ("mnn", 0, 10),
            ("mnn", 10, 0),
            ("mnn", 0, 0),
            ("smnn", 0, 10),
            ("smnn", 10, 0),
            ("smnn", 0, 0),
        ],
    )
    def test_empty_nocrash(self, match_type, d1, d2, device, dtype):
        desc1 = torch.empty(d1, 8, device=device, dtype=dtype)
        desc2 = torch.empty(d2, 8, device=device, dtype=dtype)
        matcher = DescriptorMatcher(match_type, 0.8).to(device)
        dists, idxs = matcher(desc1, desc2)
        assert dists is not None
        assert idxs is not None

    def test_gradcheck(self, device):
        desc1 = torch.rand(5, 8, device=device, dtype=torch.float64)
        desc2 = torch.rand(7, 8, device=device, dtype=torch.float64)
        matcher = DescriptorMatcher("smnn", 0.8).to(device)
        self.gradcheck(match_smnn, (desc1, desc2, 0.8), nondet_tol=1e-4)
        self.gradcheck(matcher, (desc1, desc2), nondet_tol=1e-4)

    @pytest.mark.jit()
    @pytest.mark.parametrize("match_type", ["nn", "snn", "mnn", "smnn"])
    def test_jit(self, match_type, device, dtype):
        desc1 = torch.rand(5, 8, device=device, dtype=dtype)
        desc2 = torch.rand(7, 8, device=device, dtype=dtype)
        matcher = DescriptorMatcher(match_type, 0.8).to(device)
        matcher_jit = torch.jit.script(DescriptorMatcher(match_type, 0.8).to(device))
        self.assert_close(matcher(desc1, desc2)[0], matcher_jit(desc1, desc2)[0])
        self.assert_close(matcher(desc1, desc2)[1], matcher_jit(desc1, desc2)[1])


class TestMatchFGINN(BaseTester):
    @pytest.mark.parametrize("num_desc1, num_desc2, dim", [(2, 4, 4), (2, 5, 128), (6, 2, 32)])
    def test_shape_one_way(self, num_desc1, num_desc2, dim, device):
        desc1 = torch.rand(num_desc1, dim, device=device)
        desc2 = torch.rand(num_desc2, dim, device=device)
        lafs1 = torch.rand(1, num_desc1, 2, 3, device=device)
        lafs2 = torch.rand(1, num_desc2, 2, 3, device=device)

        dists, idxs = match_fginn(desc1, desc2, lafs1, lafs2, 0.9, 1000)
        assert idxs.shape[1] == 2
        assert dists.shape[1] == 1
        assert idxs.shape[0] == dists.shape[0]
        assert dists.shape[0] <= num_desc1

    @pytest.mark.parametrize("num_desc1, num_desc2, dim", [(2, 4, 4), (2, 5, 128), (6, 2, 32)])
    def test_shape_two_way(self, num_desc1, num_desc2, dim, device):
        desc1 = torch.rand(num_desc1, dim, device=device)
        desc2 = torch.rand(num_desc2, dim, device=device)
        lafs1 = torch.rand(1, num_desc1, 2, 3, device=device)
        lafs2 = torch.rand(1, num_desc2, 2, 3, device=device)

        dists, idxs = match_fginn(desc1, desc2, lafs1, lafs2, 0.9, 1000, mutual=True)
        assert idxs.shape[1] == 2
        assert dists.shape[1] == 1
        assert idxs.shape[0] == dists.shape[0]
        assert dists.shape[0] <= num_desc1
        assert dists.shape[0] <= num_desc2

    def test_matching1(self, device, dtype):
        desc1 = torch.tensor([[0, 0.0], [1, 1.001], [2, 2], [3, 3.0], [5, 5.0]], dtype=dtype, device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1.001], [0, 0.0]], dtype=dtype, device=device)
        lafs1 = laf_from_center_scale_ori(desc1[None])
        lafs2 = laf_from_center_scale_ori(desc2[None])

        dists, idxs = match_fginn(desc1, desc2, lafs1, lafs2, 0.8, 0.01)
        expected_dists = torch.tensor([0, 0, 0.3536, 0, 0], dtype=dtype, device=device).view(-1, 1)
        expected_idx = torch.tensor([[0, 4], [1, 3], [2, 2], [3, 1], [4, 0]], device=device)
        self.assert_close(dists, expected_dists, rtol=0.001, atol=1e-3)
        self.assert_close(idxs, expected_idx)
        matcher = GeometryAwareDescriptorMatcher("fginn", {"spatial_th": 0.01}).to(device)
        dists1, idxs1 = matcher(desc1, desc2, lafs1, lafs2)
        self.assert_close(dists1, expected_dists, rtol=0.001, atol=1e-3)
        self.assert_close(idxs1, expected_idx)

    def test_matching_mutual(self, device, dtype):
        desc1 = torch.tensor([[0, 0.1], [1, 1.001], [2, 2], [3, 3.0], [5, 5.0], [0.0, 0]], dtype=dtype, device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1.001], [0, 0.0]], dtype=dtype, device=device)
        lafs1 = laf_from_center_scale_ori(desc1[None])
        lafs2 = laf_from_center_scale_ori(desc2[None])

        dists, idxs = match_fginn(desc1, desc2, lafs1, lafs2, 0.8, 2.0, mutual=True)
        expected_dists = torch.tensor([0, 0.1768, 0, 0, 0], dtype=dtype, device=device).view(-1, 1)
        expected_idx = torch.tensor([[1, 3], [2, 2], [3, 1], [4, 0], [5, 4]], device=device)
        self.assert_close(dists, expected_dists, rtol=0.001, atol=1e-3)
        self.assert_close(idxs, expected_idx)
        matcher = GeometryAwareDescriptorMatcher("fginn", {"spatial_th": 2.0, "mutual": True}).to(device)
        dists1, idxs1 = matcher(desc1, desc2, lafs1, lafs2)
        self.assert_close(dists1, expected_dists, rtol=0.001, atol=1e-3)
        self.assert_close(idxs1, expected_idx)

    def test_nomatch(self, device, dtype):
        desc1 = torch.tensor([[0, 0.0]], dtype=dtype, device=device)
        desc2 = torch.tensor([[5, 5.0]], dtype=dtype, device=device)
        lafs1 = laf_from_center_scale_ori(desc1[None])
        lafs2 = laf_from_center_scale_ori(desc2[None])

        dists, idxs = match_fginn(desc1, desc2, lafs1, lafs2, 0.8)
        assert len(dists) == 0
        assert len(idxs) == 0

    def test_matching2(self, device, dtype):
        desc1 = torch.tensor([[0, 0.0], [1, 1.001], [2, 2], [3, 3.0], [5, 5.0]], dtype=dtype, device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1.001], [0, 0.0]], dtype=dtype, device=device)
        lafs1 = laf_from_center_scale_ori(desc1[None])
        lafs2 = laf_from_center_scale_ori(desc2[None])

        dists, idxs = match_fginn(desc1, desc2, lafs1, lafs2, 0.8, 2.0)
        expected_dists = torch.tensor([0, 0, 0.1768, 0, 0], dtype=dtype, device=device).view(-1, 1)
        expected_idx = torch.tensor([[0, 4], [1, 3], [2, 2], [3, 1], [4, 0]], device=device)
        self.assert_close(dists, expected_dists, rtol=0.001, atol=1e-3)
        self.assert_close(idxs, expected_idx)
        matcher = GeometryAwareDescriptorMatcher("fginn", {"spatial_th": 2.0}).to(device)
        dists1, idxs1 = matcher(desc1, desc2, lafs1, lafs2)
        self.assert_close(dists1, expected_dists, rtol=0.001, atol=1e-3)
        self.assert_close(idxs1, expected_idx)

    def test_gradcheck(self, device):
        desc1 = torch.rand(5, 8, device=device, dtype=torch.float64)
        desc2 = torch.rand(7, 8, device=device, dtype=torch.float64)
        center1 = torch.rand(1, 5, 2, device=device, dtype=torch.float64)
        center2 = torch.rand(1, 7, 2, device=device, dtype=torch.float64)
        lafs1 = laf_from_center_scale_ori(center1)
        lafs2 = laf_from_center_scale_ori(center2)
        self.gradcheck(match_fginn, (desc1, desc2, lafs1, lafs2, 0.8, 0.05), nondet_tol=1e-4)

    @pytest.mark.jit()
    @pytest.mark.skip("keyword-arg expansion is not supported")
    def test_jit(self, device, dtype):
        desc1 = torch.rand(5, 8, device=device, dtype=dtype)
        desc2 = torch.rand(7, 8, device=device, dtype=dtype)
        center1 = torch.rand(1, 5, 2, device=device)
        center2 = torch.rand(1, 7, 2, device=device)
        lafs1 = laf_from_center_scale_ori(center1)
        lafs2 = laf_from_center_scale_ori(center2)
        matcher = GeometryAwareDescriptorMatcher("fginn", 0.8).to(device)
        matcher_jit = torch.jit.script(GeometryAwareDescriptorMatcher("fginn", 0.8).to(device))
        self.assert_close(matcher(desc1, desc2)[0], matcher_jit(desc1, desc2, lafs1, lafs2)[0])
        self.assert_close(matcher(desc1, desc2)[1], matcher_jit(desc1, desc2, lafs1, lafs2)[1])


class TestAdalam(BaseTester):
    @pytest.mark.slow
    @pytest.mark.parametrize("data", ["adalam_idxs"], indirect=True)
    def test_real(self, device, dtype, data):
        torch.random.manual_seed(0)
        # This is not unit test, but that is quite good integration test
        data_dev = dict_to(data, device, dtype)
        with torch.no_grad():
            dists, idxs = match_adalam(data_dev["descs1"], data_dev["descs2"], data_dev["lafs1"], data_dev["lafs2"])
        assert idxs.shape[1] == 2
        assert dists.shape[1] == 1
        assert idxs.shape[0] == dists.shape[0]
        assert dists.shape[0] <= data_dev["descs1"].shape[0]
        assert dists.shape[0] <= data_dev["descs2"].shape[0]
        expected_idxs = data_dev["expected_idxs"].long()
        self.assert_close(idxs, expected_idxs, rtol=1e-4, atol=1e-4)

    @pytest.mark.slow
    @pytest.mark.parametrize("data", ["adalam_idxs"], indirect=True)
    def test_single_nocrash(self, device, dtype, data):
        torch.random.manual_seed(0)
        # This is not unit test, but that is quite good integration test
        data_dev = dict_to(data, device, dtype)
        with torch.no_grad():
            dists, idxs = match_adalam(
                data_dev["descs1"], data_dev["descs2"][:1], data_dev["lafs1"], data_dev["lafs2"][:, :1]
            )
            dists, idxs = match_adalam(
                data_dev["descs1"][:1], data_dev["descs2"], data_dev["lafs1"][:, :1], data_dev["lafs2"]
            )

    @pytest.mark.slow
    @pytest.mark.parametrize("data", ["adalam_idxs"], indirect=True)
    def test_small_user_conf(self, device, dtype, data):
        torch.random.manual_seed(0)
        # This is not unit test, but that is quite good integration test
        data_dev = dict_to(data, device, dtype)
        adalam_config = {"device": device}
        with torch.no_grad():
            dists, idxs = match_adalam(
                data_dev["descs1"][:4],
                data_dev["descs2"][:4],
                data_dev["lafs1"][:, :4],
                data_dev["lafs2"][:, :4],
                config=adalam_config,
            )

    @pytest.mark.slow
    @pytest.mark.parametrize("data", ["adalam_idxs"], indirect=True)
    def test_empty_nocrash(self, device, dtype, data):
        torch.random.manual_seed(0)
        # This is not unit test, but that is quite good integration test
        data_dev = dict_to(data, device, dtype)
        with torch.no_grad():
            dists, idxs = match_adalam(
                data_dev["descs1"],
                torch.empty(0, 128, device=device, dtype=dtype),
                data_dev["lafs1"],
                torch.empty(0, 0, 2, 3, device=device, dtype=dtype),
            )
            dists, idxs = match_adalam(
                torch.empty(0, 128, device=device, dtype=dtype),
                data_dev["descs2"],
                torch.empty(0, 0, 2, 3, device=device, dtype=dtype),
                data_dev["lafs2"],
            )

    @pytest.mark.slow
    @pytest.mark.parametrize("data", ["adalam_idxs"], indirect=True)
    def test_small(self, device, dtype, data):
        torch.random.manual_seed(0)
        # This is not unit test, but that is quite good integration test
        data_dev = dict_to(data, device, dtype)
        with torch.no_grad():
            dists, idxs = match_adalam(
                data_dev["descs1"][:4], data_dev["descs2"][:4], data_dev["lafs1"][:, :4], data_dev["lafs2"][:, :4]
            )

    @pytest.mark.slow
    @pytest.mark.parametrize("data", ["adalam_idxs"], indirect=True)
    def test_seeds_fail(self, device, dtype, data):
        torch.random.manual_seed(0)
        # This is not unit test, but that is quite good integration test
        data_dev = dict_to(data, device, dtype)
        with torch.no_grad():
            dists, idxs = match_adalam(
                data_dev["descs1"][:100],
                data_dev["descs2"][:100],
                data_dev["lafs1"][:, :100],
                data_dev["lafs2"][:, :100],
            )

    @pytest.mark.slow
    @pytest.mark.parametrize("data", ["adalam_idxs"], indirect=True)
    def test_module(self, device, dtype, data):
        torch.random.manual_seed(0)
        # This is not unit test, but that is quite good integration test
        data_dev = dict_to(data, device, dtype)
        matcher = GeometryAwareDescriptorMatcher("adalam", {"device": device}).to(device, dtype)
        with torch.no_grad():
            dists, idxs = matcher(data_dev["descs1"], data_dev["descs2"], data_dev["lafs1"], data_dev["lafs2"])
        assert idxs.shape[1] == 2
        assert dists.shape[1] == 1
        assert idxs.shape[0] == dists.shape[0]
        assert dists.shape[0] <= data_dev["descs1"].shape[0]
        assert dists.shape[0] <= data_dev["descs2"].shape[0]
        expected_idxs = data_dev["expected_idxs"].long()
        self.assert_close(idxs, expected_idxs, rtol=1e-4, atol=1e-4)


class TestLightGlueDISK(BaseTester):
    @pytest.mark.slow
    @pytest.mark.skipif(torch_version_le(1, 9, 1), reason="Needs autocast")
    @pytest.mark.parametrize("data", ["lightglue_idxs"], indirect=True)
    def test_real(self, device, dtype, data):
        torch.random.manual_seed(0)
        # This is not unit test, but that is quite good integration test
        data_dev = dict_to(data, device, dtype)
        config = {"depth_confidence": -1, "width_confidence": -1}
        lg = LightGlueMatcher("disk", config).to(device=device, dtype=dtype).eval()
        with torch.no_grad():
            dists, idxs = lg(data_dev["descs1"], data_dev["descs2"], data_dev["lafs1"], data_dev["lafs2"])
        assert idxs.shape[1] == 2
        assert dists.shape[1] == 1
        assert idxs.shape[0] == dists.shape[0]
        assert dists.shape[0] <= data_dev["descs1"].shape[0]
        assert dists.shape[0] <= data_dev["descs2"].shape[0]
        expected_idxs = data_dev["lightglue_disk_idxs"].long()
        self.assert_close(idxs, expected_idxs, rtol=1e-4, atol=1e-4)

    @pytest.mark.slow
    @pytest.mark.parametrize("data", ["lightglue_idxs"], indirect=True)
    def test_single_nocrash(self, device, dtype, data):
        torch.random.manual_seed(0)
        # This is not unit test, but that is quite good integration test
        data_dev = dict_to(data, device, dtype)
        lg = LightGlueMatcher("disk").to(device, dtype).eval()
        with torch.no_grad():
            dists, idxs = lg(data_dev["descs1"], data_dev["descs2"][:1], data_dev["lafs1"], data_dev["lafs2"][:, :1])
            dists, idxs = lg(data_dev["descs1"][:1], data_dev["descs2"], data_dev["lafs1"][:, :1], data_dev["lafs2"])

    @pytest.mark.slow
    @pytest.mark.parametrize("data", ["lightglue_idxs"], indirect=True)
    def test_empty_nocrash(self, device, dtype, data):
        torch.random.manual_seed(0)
        # This is not unit test, but that is quite good integration test
        data_dev = dict_to(data, device, dtype)
        lg = LightGlueMatcher("disk").to(device, dtype).eval()
        with torch.no_grad():
            dists, idxs = lg(
                data_dev["descs1"],
                torch.empty(0, 256, device=device, dtype=dtype),
                data_dev["lafs1"],
                torch.empty(0, 0, 2, 3, device=device, dtype=dtype),
            )
            dists, idxs = lg(
                torch.empty(0, 256, device=device, dtype=dtype),
                data_dev["descs2"],
                torch.empty(0, 0, 2, 3, device=device, dtype=dtype),
                data_dev["lafs2"],
            )


class TestLightGlueHardNet(BaseTester):
    @pytest.mark.skip(reason="download weight from github")
    def test_smoke(self):
        lg = LightGlueMatcher("doghardnet")
        assert isinstance(lg, LightGlueMatcher)


class TestMatchSteererGlobal(BaseTester):
    @pytest.mark.parametrize("num_desc1, num_desc2, dim", [(1, 4, 4), (2, 5, 128), (6, 2, 32), (32, 32, 8)])
    @pytest.mark.parametrize("matching_mode", ["nn", "mnn", "snn", "smnn"])
    @pytest.mark.parametrize("fast", [False, True])
    def test_shape(self, num_desc1, num_desc2, dim, matching_mode, fast, device):
        desc1 = torch.rand(num_desc1, dim, device=device)
        generator = torch.rand(dim, dim, device=device)
        steerer = DiscreteSteerer(generator)
        desc2 = steerer(desc1)

        matcher = DescriptorMatcherWithSteerer(
            steerer=steerer, steerer_order=3, steer_mode="global", match_mode=matching_mode
        )

        dists, idxs, num_rot = matcher(
            desc1,
            desc2,
            subset_size=max(1, min(num_desc1 // 2, num_desc2 // 2)) if fast else None,
        )
        assert dists.shape[1] == 1
        assert dists.shape[0] <= num_desc1
        assert idxs.shape[1] == 2
        assert idxs.shape[0] == dists.shape[0]

    def test_matching(self, device):
        desc1 = torch.tensor([[0, 0.0], [1, 1], [2, 2], [3, 3.0], [5, 5.0]], device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1], [0, 0.0]], device=device)

        # rotate desc2 270 deg anti-clockwise
        desc2 = desc2[:, [1, 0]]
        desc2[:, 0] = -desc2[:, 0]

        generator = torch.tensor([[0.0, 1], [-1, 0]], device=device)
        steerer = DiscreteSteerer(generator)
        matcher = DescriptorMatcherWithSteerer(steerer=steerer, steerer_order=4, steer_mode="global", match_mode="mnn")

        dists, idxs, num_rot = matcher(desc1, desc2)
        expected_dists = torch.tensor([0, 0, 0.5, 0, 0], device=device).view(-1, 1)
        expected_idx = torch.tensor([[0, 4], [1, 3], [2, 2], [3, 1], [4, 0]], device=device)
        self.assert_close(dists, expected_dists)
        self.assert_close(idxs, expected_idx)

        assert num_rot == 3


class TestMatchSteererLocal(BaseTester):
    @pytest.mark.parametrize("num_desc1, num_desc2, dim", [(1, 4, 4), (2, 5, 128), (6, 2, 32)])
    def test_shape(self, num_desc1, num_desc2, dim, device):
        desc1 = torch.rand(num_desc1, dim, device=device)
        generator = torch.rand(dim, dim, device=device)
        steerer = DiscreteSteerer(generator)
        desc2 = steerer(desc1)
        desc2[:1] = steerer(desc2[:1])

        matcher = DescriptorMatcherWithSteerer(steerer=steerer, steerer_order=3, steer_mode="local", match_mode="mnn")

        dists, idxs, num_rot = matcher(desc1, desc2)
        assert dists.shape[1] == 1
        assert idxs.shape == (dists.shape[0], 2)
        assert dists.shape[0] == num_desc1

    def test_matching(self, device):
        desc1 = torch.tensor([[0, 0.0], [1, 1], [2, 2], [3, 3.0], [5, 5.0]], device=device)
        desc2 = torch.tensor([[5, 5.0], [3, 3.0], [2.3, 2.4], [1, 1], [0, 0.0]], device=device)

        # rotate second to last element of desc2 90 deg anti-clockwise
        desc2[-2] = desc2[-2, [1, 0]]
        desc2[-2, 1] = -desc2[-2, 1]

        # rotate first two elements of desc2 270 deg anti-clockwise
        desc2[:2] = desc2[:2, [1, 0]]
        desc2[:2, 0] = -desc2[:2, 0]

        generator = torch.tensor([[0.0, 1], [-1, 0]], device=device)
        steerer = DiscreteSteerer(generator)
        matcher = DescriptorMatcherWithSteerer(steerer=steerer, steerer_order=4, steer_mode="local", match_mode="mnn")

        dists, idxs, num_rot = matcher(desc1, desc2)
        expected_dists = torch.tensor([0, 0, 0.5, 0, 0], device=device).view(-1, 1)
        expected_idx = torch.tensor([[0, 4], [1, 3], [2, 2], [3, 1], [4, 0]], device=device)
        self.assert_close(dists, expected_dists)
        self.assert_close(idxs, expected_idx)

        assert num_rot is None
