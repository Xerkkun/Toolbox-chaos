"""Collect HAFO as physical Python source for Numba's cache locators."""

# HAFO contains Numba ``cache=True`` dispatchers.  PyInstaller's documented
# source collection mode keeps those modules out of PYZ and gives every
# dispatcher a real ``__file__`` while preserving HAFO's installed wheel.
module_collection_mode = {"hidden_attractors": "py"}

