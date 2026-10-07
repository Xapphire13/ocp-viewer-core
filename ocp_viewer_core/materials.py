"""Conversions between OCCT's XCAFDoc_VisMaterial and threejs-materials' PbrProperties.

OCCT documents carry visual materials as `XCAFDoc_VisMaterial` - a PBR block
(base color, metallic, roughness, refraction index, emissive) plus alpha mode
and double-sidedness. cadquery's `Material` wraps one in `wrapped_vis`, and any
STEP/glTF round trip through XCAF produces them. The viewer side speaks
`PbrProperties`. These two functions translate between the paradigms so a
material can enter the show pipeline from an OCCT document and a catalogue
material can be written back into one. The OCCT side is ocp_tessellate's
(`vis_material_values`, `make_vis_material`, for OCP and nanocct alike).

Both directions are scalar-only and lossy where the vocabularies differ:
`XCAFDoc_VisMaterialPBR` has no clearcoat, sheen, transmission or texture maps,
so those `PbrProperties` fields do not survive the trip into OCCT.

Color spaces: `PbrValues.color` is sRGB ratios, `PbrValues.emissive` is linear -
per that class's docstring - and so are the values ocp_tessellate reads and
writes. The emissive factor exists in OCP 7.9 and nanocct; cadquery-ocp 8 does
not bind it, and the emissive term is skipped there.
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

from ocp_tessellate.ocp_utils import make_vis_material, vis_material_values
from threejs_materials import PbrProperties, PbrValues

__all__ = ["pbr_to_vis_material", "vis_material_to_pbr"]

# Three.js side constants (three/src/constants.js): FrontSide=0, BackSide=1
THREEJS_DOUBLE_SIDE = 2


def vis_material_to_pbr(vis_material, name=None):
    """Convert an `XCAFDoc_VisMaterial` to a `PbrProperties`.

    Reads the PBR block when the material has one; a common (Phong-style)
    material is converted through OCCT's own `ConvertToPbrMaterial`, which
    leaves the input untouched. An empty material holds nothing to render,
    so the answer is None - callers must check.

    @param vis_material: The `XCAFDoc_VisMaterial` to read
    @param name: Material name; falls back to the material's raw name, then "material"

    @return: A `PbrProperties`, or None if the material is empty
    """
    occt = vis_material_values(vis_material)
    if occt is None:
        return None

    if name is None:
        name = occt["name"]
    if name is None or name == "":
        name = "material"

    values = PbrValues(
        color=list(occt["color"]),
        metalness=occt["metallic"],
        roughness=occt["roughness"],
        ior=occt["ior"],
    )

    emissive = occt["emissive"]
    if emissive is not None and not (emissive[0] == 0.0 and emissive[1] == 0.0 and emissive[2] == 0.0):
        values.emissive = list(emissive)

    if occt["alpha_mode"] == "Mask":
        values.alpha_test = occt["alpha_cutoff"]
    alpha = occt["alpha"]
    if alpha < 1.0:
        values.opacity = alpha
        values.transparent = True

    if occt["double_sided"] is True:
        values.side = THREEJS_DOUBLE_SIDE

    return PbrProperties(
        id=name,
        name=name,
        source="occt",
        url="",
        license="",
        values=values,
    )


def pbr_to_vis_material(pbr_properties):
    """Convert a `PbrProperties` to a new `XCAFDoc_VisMaterial`.

    Only the fields `XCAFDoc_VisMaterialPBR` can hold survive: color plus
    opacity (as base color RGBA), metalness, roughness, ior, and emissive
    with `emissive_intensity` folded in. `alpha_test` becomes alpha mode
    Mask with its cutoff, a translucent material becomes mode Blend, and
    `side` double-sided marks the material double-sided. Everything else -
    clearcoat, sheen, transmission, texture maps - is not representable
    and is dropped.

    @param pbr_properties: The `PbrProperties` to write

    @return: A new `XCAFDoc_VisMaterial` with the PBR block set
    """
    values = pbr_properties.values

    opacity = values.opacity
    if opacity is None:
        opacity = 1.0

    color = None
    if values.color is not None:
        color = (values.color[0], values.color[1], values.color[2])

    emissive = None
    if values.emissive is not None:
        intensity = values.emissive_intensity
        if intensity is None:
            intensity = 1.0
        emissive = (
            values.emissive[0] * intensity,
            values.emissive[1] * intensity,
            values.emissive[2] * intensity,
        )

    alpha_mode = None
    alpha_cutoff = None
    if values.alpha_test is not None:
        alpha_mode = "Mask"
        alpha_cutoff = values.alpha_test
    elif values.transparent is True or opacity < 1.0:
        alpha_mode = "Blend"

    return make_vis_material(
        pbr_properties.name,
        color=color,
        alpha=opacity,
        metallic=values.metalness,
        roughness=values.roughness,
        ior=values.ior,
        emissive=emissive,
        alpha_mode=alpha_mode,
        alpha_cutoff=alpha_cutoff,
        double_sided=values.side == THREEJS_DOUBLE_SIDE,
    )
