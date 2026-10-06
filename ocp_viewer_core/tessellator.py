"""What the hosts need from the tessellator, so they need nothing else from it.

`ImageFace` reached past the core into `ocp_tessellate` from every host's
`__init__`, re-exported into the star surface. That was the only reason a
viewer had to name `ocp-tessellate` among its own dependencies - the pipeline
that actually tessellates is in `show.py`, here, and it carries the dependency
for everyone.

Importing this module loads the tessellator and with it the OCP kernel, so the
package root does not import it. A host does, as it does `show`.
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

from ocp_tessellate.cad_objects import ImageFace

__all__ = [
    "ImageFace",
]
