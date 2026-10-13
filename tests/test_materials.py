"""The XCAFDoc_VisMaterial <-> PbrProperties translation, both directions.

OCCT documents and cadquery's Material speak `XCAFDoc_VisMaterial`; the viewer
speaks `PbrProperties`. The two functions in `materials.py` translate between
them, and the show pipeline's extractor uses the forward direction for any
material duck-typed as cadquery's. The extractor must also survive what it
cannot translate: a cadquery Material whose vis material is empty (which is
every one cadquery constructs today), and a material type nobody knows -
both are dropped with a message, never a crash.
"""

#
# Copyright 2026 Bernhard Walter
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import importlib
import importlib.util

import pytest
from ocp_tessellate.ocp_utils import make_vis_material, vis_material_values
from threejs_materials import PbrProperties, PbrValues

from ocp_viewer_core.materials import (
    THREEJS_DOUBLE_SIDE,
    pbr_to_vis_material,
    vis_material_to_pbr,
)
from ocp_viewer_core.show import (
    _extract_material_objects,
    is_cadquery_material,
)

# the binding pbr_to_vis_material builds in when nothing else decides:
# nanocct if it is installed, else OCP (ocp_tessellate's rule)
BINDING = "nanocct" if importlib.util.find_spec("nanocct") is not None else "OCP"
XCAFDoc = importlib.import_module(f"{BINDING}.XCAFDoc")
Quantity = importlib.import_module(f"{BINDING}.Quantity")

# cadquery-ocp 8 binds no emissive factor; OCP 7.9 and nanocct do
HAS_EMISSIVE = vis_material_values(make_vis_material("probe", emissive=(1.0, 0.0, 0.0)))["emissive"] is not None
needs_emissive = pytest.mark.skipif(
    HAS_EMISSIVE is False, reason=f"{BINDING} binds no XCAFDoc_VisMaterialPBR.EmissiveFactor"
)


def make_pbr(name="Gold", **values):
    return PbrProperties(
        id=name.lower(),
        name=name,
        source="test",
        url="",
        license="",
        values=PbrValues(**values),
    )


INSTALLED = [b for b in ("OCP", "nanocct") if importlib.util.find_spec(b) is not None]


@pytest.mark.parametrize("binding", INSTALLED)
def test_pbr_to_vis_material_takes_the_binding_of_like(binding):
    """The material for a shape of either binding, e.g. CadQuery on OCP where
    nanocct is installed and would otherwise be the binding."""
    like = importlib.import_module(f"{binding}.TopLoc").TopLoc_Location()
    vis = pbr_to_vis_material(make_pbr(color=[1.0, 0.8, 0.3]), like=like)
    assert type(vis).__module__.partition(".")[0] == binding
    assert vis_material_to_pbr(vis).values.color == pytest.approx([1.0, 0.8, 0.3])


def test_pbr_to_vis_material_without_like_uses_the_default_binding():
    vis = pbr_to_vis_material(make_pbr(color=[1.0, 0.8, 0.3]))
    assert type(vis).__module__.partition(".")[0] == BINDING


# ------------------------- vis_material_to_pbr ------------------------- #


def test_empty_vis_material_is_none():
    assert vis_material_to_pbr(XCAFDoc.XCAFDoc_VisMaterial()) is None


def test_pbr_roundtrip_scalars():
    original = make_pbr(
        color=[1.0, 0.8, 0.3], metalness=1.0, roughness=0.08, ior=1.4
    )
    result = vis_material_to_pbr(pbr_to_vis_material(original))

    assert result is not None
    assert result.name == "Gold"
    assert result.values.metalness == pytest.approx(1.0)
    assert result.values.roughness == pytest.approx(0.08)
    assert result.values.ior == pytest.approx(1.4, abs=1e-6)
    assert result.values.color == pytest.approx([1.0, 0.8, 0.3], abs=1e-6)
    assert result.values.opacity is None
    assert result.values.transparent is None


@needs_emissive
def test_pbr_roundtrip_emissive_is_linear():
    original = make_pbr(color=[0.5, 0.5, 0.5], emissive=[0.1, 0.2, 0.3])
    result = vis_material_to_pbr(pbr_to_vis_material(original))

    assert result.values.emissive == pytest.approx([0.1, 0.2, 0.3], abs=1e-6)


def test_pbr_roundtrip_opacity_and_alpha_mode():
    original = make_pbr(color=[1.0, 0.0, 0.0], opacity=0.5)
    vis = pbr_to_vis_material(original)

    assert vis_material_values(vis)["alpha_mode"] == "Blend"

    result = vis_material_to_pbr(vis)
    assert result.values.opacity == pytest.approx(0.5, abs=1e-6)
    assert result.values.transparent is True


def test_pbr_roundtrip_alpha_test():
    original = make_pbr(color=[1.0, 1.0, 1.0], alpha_test=0.25)
    vis = pbr_to_vis_material(original)

    assert vis_material_values(vis)["alpha_mode"] == "Mask"

    result = vis_material_to_pbr(vis)
    assert result.values.alpha_test == pytest.approx(0.25, abs=1e-6)


def test_pbr_roundtrip_double_sided():
    original = make_pbr(color=[1.0, 1.0, 1.0], side=THREEJS_DOUBLE_SIDE)
    vis = pbr_to_vis_material(original)

    assert vis.IsDoubleSided() is True
    assert vis_material_to_pbr(vis).values.side == THREEJS_DOUBLE_SIDE


def test_name_from_raw_name_and_override():
    vis = pbr_to_vis_material(make_pbr(name="Copper", color=[0.9, 0.5, 0.3]))

    assert vis_material_to_pbr(vis).name == "Copper"
    assert vis_material_to_pbr(vis, name="Kupfer").name == "Kupfer"


def test_common_material_converts_to_pbr():
    common = XCAFDoc.XCAFDoc_VisMaterialCommon()
    common.DiffuseColor = Quantity.Quantity_Color(
        0.5, 0.5, 0.5, Quantity.Quantity_TypeOfColor.Quantity_TOC_sRGB
    )
    common.IsDefined = True
    vis = XCAFDoc.XCAFDoc_VisMaterial()
    vis.SetCommonMaterial(common)

    result = vis_material_to_pbr(vis, name="common")
    assert result is not None
    assert result.values.metalness is not None
    assert result.values.roughness is not None


@needs_emissive
def test_emissive_intensity_is_folded_in():
    original = make_pbr(
        color=[1.0, 1.0, 1.0], emissive=[0.5, 0.5, 0.5], emissive_intensity=2.0
    )
    result = vis_material_to_pbr(pbr_to_vis_material(original))

    assert result.values.emissive == pytest.approx([1.0, 1.0, 1.0], abs=1e-6)


# ---------------------- the extractor's material gate ---------------------- #


class StubCadqueryMaterial:
    """The duck type of cadquery.occ_impl.assembly.Material, without cadquery."""

    def __init__(self, name, vis_material):
        self.wrapped = object()
        self.wrapped_vis = vis_material
        self.name = name
        self.density = 1.0


class StubNode:
    def __init__(self, material):
        self.material = material


def test_is_cadquery_material():
    stub = StubCadqueryMaterial("Gold", XCAFDoc.XCAFDoc_VisMaterial())
    assert is_cadquery_material(stub) is True
    assert is_cadquery_material("Gold") is False
    assert is_cadquery_material(make_pbr()) is False


def test_cadquery_material_with_pbr_is_extracted():
    vis = pbr_to_vis_material(make_pbr(color=[1.0, 0.8, 0.3], metalness=1.0))
    node = StubNode(StubCadqueryMaterial("Gold", vis))

    extracted = _extract_material_objects(node)

    assert node.material == "Gold"
    assert list(extracted.keys()) == ["Gold"]
    assert extracted["Gold"]["values"]["metalness"] == pytest.approx(1.0)


def test_empty_cadquery_material_is_dropped(capsys):
    node = StubNode(StubCadqueryMaterial("Gold", XCAFDoc.XCAFDoc_VisMaterial()))

    extracted = _extract_material_objects(node)

    assert node.material is None
    assert extracted is None
    assert "no visual properties" in capsys.readouterr().out


def test_unknown_material_is_dropped(capsys):
    node = StubNode(object())

    extracted = _extract_material_objects(node)

    assert node.material is None
    assert extracted is None
    assert "Unknown material" in capsys.readouterr().out
