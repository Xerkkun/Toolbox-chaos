from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
EXPECTED_TIME_SHAPE = [101]
EXPECTED_STATE_SHAPE = [101, 3]
EXPECTED_HAFO_TIME_SHAPE = [6]
EXPECTED_HAFO_STATE_SHAPE = [6, 2]
EXPECTED_NUMBA_RESULT_SHAPE = [257, 16]
EXPECTED_NUMBA_POOLS = {
    'omp': ('numba.np.ufunc.omppool', 'omppool'),
    'workqueue': ('numba.np.ufunc.workqueue', 'workqueue'),
}
EXPECTED_HAFO_SOURCE_MODULES = {
    'hidden_attractors',
    'hidden_attractors.systems',
    'hidden_attractors.simulation',
    'hidden_attractors.integrations.numba_kernels',
    'hidden_attractors.fractional.convolution_quadrature',
    'hidden_attractors.fractional.grunwald_letnikov',
}


class SelfTestValidationError(ValueError):
    pass


def validate_self_test_payload(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise SelfTestValidationError('Self-test output must be a JSON object.')
    if payload.get('schema_version') != 1:
        raise SelfTestValidationError('Unsupported self-test schema_version.')
    if payload.get('status') != 'ok':
        raise SelfTestValidationError(
            f"Packaged self-test did not succeed: {payload.get('status')!r}."
        )
    if payload.get('time_shape') != EXPECTED_TIME_SHAPE:
        raise SelfTestValidationError(
            f"Unexpected time_shape: {payload.get('time_shape')!r}."
        )
    if payload.get('state_shape') != EXPECTED_STATE_SHAPE:
        raise SelfTestValidationError(
            f"Unexpected state_shape: {payload.get('state_shape')!r}."
        )
    if payload.get('all_finite') is not True:
        raise SelfTestValidationError('Packaged native result is not finite.')
    for key in (
        'result_sha256',
        'hafo_bridge_result_sha256',
        'hafo_gl_result_sha256',
        'numba_result_sha256',
    ):
        digest = payload.get(key)
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise SelfTestValidationError(
                f'{key} is not a lowercase SHA-256 digest.'
            )
        if int(digest, 16) == 0:
            raise SelfTestValidationError(f'{key} must not be the all-zero digest.')
    for key in ('application', 'version'):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise SelfTestValidationError(f'{key} is missing from self-test output.')
    if payload.get('hafo_engine_available') is not True:
        raise SelfTestValidationError('The HAFO engine was not available.')
    if not isinstance(payload.get('hafo_version'), str) or not payload['hafo_version'].strip():
        raise SelfTestValidationError('hafo_version is missing from self-test output.')
    expected_hafo_api = (
        'ExpressionSystemDefinition.from_mapping+'
        'compile_expression_system+simulate'
    )
    if payload.get('hafo_bridge_api') != expected_hafo_api:
        raise SelfTestValidationError('The required HAFO expression-system bridge was not used.')
    if payload.get('hafo_bridge_status') != 'ok':
        raise SelfTestValidationError('The HAFO expression-system simulation did not succeed.')
    if payload.get('hafo_bridge_time_shape') != EXPECTED_HAFO_TIME_SHAPE:
        raise SelfTestValidationError(
            f"Unexpected hafo_bridge_time_shape: {payload.get('hafo_bridge_time_shape')!r}."
        )
    if payload.get('hafo_bridge_state_shape') != EXPECTED_HAFO_STATE_SHAPE:
        raise SelfTestValidationError(
            f"Unexpected hafo_bridge_state_shape: {payload.get('hafo_bridge_state_shape')!r}."
        )
    if payload.get('hafo_bridge_all_finite') is not True:
        raise SelfTestValidationError('The HAFO bridge result is not finite.')
    if payload.get('hafo_bridge_use_acceleration') is not False:
        raise SelfTestValidationError(
            'The HAFO bridge must use its deterministic Python integration path.'
        )
    if payload.get('hafo_modules_collected_as_source') is not True:
        raise SelfTestValidationError('HAFO modules were not loaded from physical sources.')
    origins = payload.get('hafo_module_origins')
    if not isinstance(origins, dict) or set(origins) != EXPECTED_HAFO_SOURCE_MODULES:
        raise SelfTestValidationError('HAFO module origins are incomplete.')
    if any(
        not isinstance(origin, str) or not origin.casefold().endswith('.py')
        for origin in origins.values()
    ):
        raise SelfTestValidationError('A HAFO module origin is not a Python source file.')
    spec_origins = payload.get('hafo_module_spec_origins')
    if (
        not isinstance(spec_origins, dict)
        or set(spec_origins) != EXPECTED_HAFO_SOURCE_MODULES
    ):
        raise SelfTestValidationError('HAFO module spec origins are incomplete.')
    if any(
        not isinstance(origin, str) or not origin.casefold().endswith('.py')
        for origin in spec_origins.values()
    ):
        raise SelfTestValidationError(
            'A HAFO module spec origin is not a Python source file.'
        )
    loaders = payload.get('hafo_module_loaders')
    if not isinstance(loaders, dict) or set(loaders) != EXPECTED_HAFO_SOURCE_MODULES:
        raise SelfTestValidationError('HAFO module loaders are incomplete.')
    if any(not isinstance(loader, str) or not loader for loader in loaders.values()):
        raise SelfTestValidationError('A HAFO module loader is missing.')
    if payload.get('hafo_gl_method') != 'gl_direct_numba':
        raise SelfTestValidationError('The real HAFO Numba GL dispatch was not used.')
    gl_cache_enabled = payload.get('hafo_gl_numba_persistent_cache_enabled')
    if gl_cache_enabled is not True:
        raise SelfTestValidationError(
            'The reviewed HAFO GL dispatcher does not enable its external cache.'
        )
    if payload.get('hafo_gl_kernel_parallel_target') is not True:
        raise SelfTestValidationError('The HAFO Numba GL target is not marked parallel.')
    gl_signatures = payload.get('hafo_gl_kernel_compiled_signatures')
    if (
        isinstance(gl_signatures, bool)
        or not isinstance(gl_signatures, int)
        or gl_signatures < 1
    ):
        raise SelfTestValidationError('The HAFO Numba GL kernel was not compiled.')
    if payload.get('hafo_gl_result_shape') != EXPECTED_NUMBA_RESULT_SHAPE:
        raise SelfTestValidationError(
            f"Unexpected hafo_gl_result_shape: {payload.get('hafo_gl_result_shape')!r}."
        )
    if payload.get('hafo_gl_all_finite') is not True:
        raise SelfTestValidationError('The HAFO Numba GL result is not finite.')
    frozen_runtime = payload.get('frozen_runtime')
    if not isinstance(frozen_runtime, bool):
        raise SelfTestValidationError('frozen_runtime must be Boolean.')
    if frozen_runtime:
        for origin in (*origins.values(), *spec_origins.values()):
            normalized_origin = origin.replace('\\', '/')
            if (
                Path(origin).is_absolute()
                or not normalized_origin.startswith('hidden_attractors/')
            ):
                raise SelfTestValidationError(
                    'A frozen HAFO source origin is outside the application runtime.'
                )
    if payload.get('numba_cache_configured') is not True:
        raise SelfTestValidationError('A writable Numba cache was not configured.')
    if payload.get('numba_cache_outside_bundle') is not True:
        raise SelfTestValidationError('The Numba cache is inside the frozen bundle.')
    cache_dir = payload.get('numba_cache_dir')
    if not isinstance(cache_dir, str) or not Path(cache_dir).is_absolute():
        raise SelfTestValidationError('numba_cache_dir is not an absolute path.')
    cache_artifact_count = payload.get('numba_cache_artifact_count')
    cache_artifacts = payload.get('numba_cache_artifacts')
    if (
        isinstance(cache_artifact_count, bool)
        or not isinstance(cache_artifact_count, int)
        or cache_artifact_count < 2
        or not isinstance(cache_artifacts, list)
        or len(cache_artifacts) != cache_artifact_count
    ):
        raise SelfTestValidationError('Numba cache artifact inventory is incomplete.')
    cache_paths = set()
    for artifact in cache_artifacts:
        if not isinstance(artifact, dict):
            raise SelfTestValidationError('A Numba cache artifact is not an object.')
        relative_path = artifact.get('path')
        if (
            not isinstance(relative_path, str)
            or Path(relative_path).is_absolute()
            or Path(relative_path).suffix not in {'.nbc', '.nbi'}
        ):
            raise SelfTestValidationError('A Numba cache artifact path is invalid.')
        if relative_path in cache_paths:
            raise SelfTestValidationError('A Numba cache artifact path is duplicated.')
        cache_paths.add(relative_path)
        artifact_bytes = artifact.get('bytes')
        if (
            isinstance(artifact_bytes, bool)
            or not isinstance(artifact_bytes, int)
            or artifact_bytes < 1
        ):
            raise SelfTestValidationError('A Numba cache artifact size is invalid.')
        artifact_hash = artifact.get('sha256')
        if (
            not isinstance(artifact_hash, str)
            or not SHA256_RE.fullmatch(artifact_hash)
            or int(artifact_hash, 16) == 0
        ):
            raise SelfTestValidationError('A Numba cache artifact hash is invalid.')
    requested_layer = payload.get('numba_threading_layer_requested')
    active_layer = payload.get('numba_threading_layer')
    if requested_layer not in EXPECTED_NUMBA_POOLS:
        raise SelfTestValidationError(
            f'Unsupported requested Numba threading layer: {requested_layer!r}.'
        )
    if active_layer != requested_layer:
        raise SelfTestValidationError(
            f'Numba threading-layer mismatch: requested={requested_layer!r}, '
            f'active={active_layer!r}.'
        )
    expected_pool_module, expected_pool_stem = EXPECTED_NUMBA_POOLS[active_layer]
    if payload.get('numba_pool_module') != expected_pool_module:
        raise SelfTestValidationError(
            f'Unexpected Numba pool module: {payload.get("numba_pool_module")!r}.'
        )
    pool_file = payload.get('numba_pool_file')
    if (
        not isinstance(pool_file, str)
        or not pool_file.startswith(expected_pool_stem + '.')
        or '/' in pool_file
        or '\\' in pool_file
    ):
        raise SelfTestValidationError(f'Unexpected Numba pool file: {pool_file!r}.')
    numba_threads = payload.get('numba_num_threads')
    if isinstance(numba_threads, bool) or not isinstance(numba_threads, int) or numba_threads < 1:
        raise SelfTestValidationError('numba_num_threads must be a positive integer.')
    if payload.get('numba_probe_scope') != 'backend_only_not_hafo_gl_dispatch':
        raise SelfTestValidationError('The Numba probe scope is missing or overstated.')
    if payload.get('numba_kernel_method') != 'packaged_parallel_probe_cache_false':
        raise SelfTestValidationError('The packaged cache-free Numba probe was not used.')
    if payload.get('numba_kernel_cache_enabled') is not False:
        raise SelfTestValidationError('The packaged Numba probe unexpectedly enables JIT caching.')
    if payload.get('numba_kernel_parallel_target') is not True:
        raise SelfTestValidationError('The packaged Numba target is not marked parallel.')
    signatures = payload.get('numba_kernel_compiled_signatures')
    if isinstance(signatures, bool) or not isinstance(signatures, int) or signatures < 1:
        raise SelfTestValidationError('The packaged Numba kernel was not compiled.')
    if payload.get('numba_result_shape') != EXPECTED_NUMBA_RESULT_SHAPE:
        raise SelfTestValidationError(
            f'Unexpected numba_result_shape: {payload.get("numba_result_shape")!r}.'
        )
    if payload.get('numba_all_finite') is not True:
        raise SelfTestValidationError('The packaged Numba result is not finite.')
    if payload.get('numba_tbbpool_loaded') is not False:
        raise SelfTestValidationError('The excluded Numba TBB pool was loaded.')
    bundled_tbbpool = payload.get('numba_tbbpool_bundled')
    if frozen_runtime and bundled_tbbpool is not False:
        raise SelfTestValidationError('The frozen runtime contains the excluded TBB pool.')
    if not frozen_runtime and bundled_tbbpool not in {None, False}:
        raise SelfTestValidationError('Invalid non-frozen TBB-pool inventory value.')
    return payload


def load_and_validate_self_test(path: str | Path) -> dict:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SelfTestValidationError(
            f'Could not read packaged self-test JSON {source}: {exc}'
        ) from exc
    return validate_self_test_payload(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Validate the headless native self-test produced by a packaged app.'
    )
    parser.add_argument('json_path')
    args = parser.parse_args(argv)
    try:
        payload = load_and_validate_self_test(args.json_path)
    except SelfTestValidationError as exc:
        print(f'PACKAGED_SELF_TEST_FAILED: {exc}', file=sys.stderr)
        return 1
    print(f"PACKAGED_SELF_TEST_OK {payload['result_sha256']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
