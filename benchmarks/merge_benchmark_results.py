from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


RESULT_NAME = "benchmark_result.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_result(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.is_file():
        return resolved
    candidate = resolved / RESULT_NAME
    if candidate.is_file():
        return candidate
    matches = sorted(resolved.rglob(RESULT_NAME)) if resolved.is_dir() else []
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(f"No se encontró {RESULT_NAME} en {resolved}")
    raise ValueError(
        f"Hay {len(matches)} resultados en {resolved}; indica cada archivo."
    )


def _validate_complete_result(payload: dict, path: Path) -> None:
    if payload.get("status") != "ok":
        raise ValueError(
            f"El resultado no está completo (status != ok): {path}. "
            "Use --allow-partial solo para diagnóstico."
        )

    manifest = payload["manifest"]
    if manifest.get("identity_status") != "verified_at_runtime":
        raise ValueError(
            f"La identidad de la computadora no fue verificada por el "
            f"lanzador nativo en {path}"
        )
    for artifact_name in ("startup_artifact", "installer_artifact"):
        artifact = manifest.get(artifact_name)
        if (
            not isinstance(artifact, dict)
            or not artifact.get("path")
            or not artifact.get("sha256")
            or not isinstance(artifact.get("size_bytes"), int)
            or artifact["size_bytes"] < 1
        ):
            raise ValueError(f"{artifact_name} no está completo en {path}")
    runtime = manifest.get("runtime")
    if (
        not isinstance(runtime, dict)
        or runtime.get("packaged_self_test") != "passed"
    ):
        raise ValueError(
            f"El cálculo de autoprueba del ejecutable empaquetado no pasó en {path}"
        )
    protocol = manifest.get("protocol")
    if not isinstance(protocol, dict):
        raise ValueError(f"Falta manifest.protocol en {path}")
    if protocol.get("startup_enabled") is not True:
        raise ValueError(f"La fase de arranque no fue ejecutada en {path}")
    if protocol.get("calculations_enabled") is not True:
        raise ValueError(f"La fase de cálculos no fue ejecutada en {path}")

    startup_runs = protocol.get("startup_runs")
    calculation_runs = protocol.get("calculation_runs")
    cases = protocol.get("cases")
    if not isinstance(startup_runs, int) or startup_runs < 1:
        raise ValueError(f"startup_runs inválido en {path}")
    if not isinstance(calculation_runs, int) or calculation_runs < 1:
        raise ValueError(f"calculation_runs inválido en {path}")
    if (
        not isinstance(cases, list)
        or not cases
        or any(not isinstance(case, str) or not case for case in cases)
        or len(set(cases)) != len(cases)
    ):
        raise ValueError(f"Lista de casos inválida en {path}")

    startup_records = payload.get("startup_records")
    calculation_records = payload.get("calculation_records")
    if not isinstance(startup_records, list) or len(startup_records) != startup_runs:
        raise ValueError(f"Cobertura de arranque incompleta en {path}")
    if any(
        not isinstance(record, dict) or record.get("status") != "ready"
        for record in startup_records
    ):
        raise ValueError(f"Hay arranques fallidos en {path}")

    expected_calculations = len(cases) * calculation_runs
    if (
        not isinstance(calculation_records, list)
        or len(calculation_records) != expected_calculations
    ):
        raise ValueError(f"Cobertura de cálculos incompleta en {path}")
    for case in cases:
        matching = [
            record
            for record in calculation_records
            if isinstance(record, dict)
            and record.get("case") == case
            and record.get("status") == "ok"
        ]
        if len(matching) != calculation_runs:
            raise ValueError(
                f"El caso {case} no tiene {calculation_runs} mediciones correctas "
                f"en {path}"
            )

    summary = payload.get("summary")
    if not isinstance(summary, list):
        raise ValueError(f"Falta la lista summary en {path}")
    summary_by_case = {
        item.get("case"): item for item in summary if isinstance(item, dict)
    }
    expected_summary_counts = {
        "startup_to_first_paint": startup_runs,
        **{case: calculation_runs for case in cases},
    }
    for case, expected_count in expected_summary_counts.items():
        item = summary_by_case.get(case)
        if not item or item.get("successful_runs") != expected_count:
            raise ValueError(
                f"El resumen de {case} no confirma {expected_count} "
                f"mediciones en {path}"
            )


def _load_result(path: Path, *, allow_partial: bool) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError(f"Versión de esquema no compatible en {path}")
    manifest = payload.get("manifest")
    if not isinstance(manifest, dict) or not manifest.get("machine_id"):
        raise ValueError(f"Falta manifest.machine_id en {path}")
    if not isinstance(payload.get("summary"), list):
        raise ValueError(f"Falta la lista summary en {path}")
    if not allow_partial:
        _validate_complete_result(payload, path)
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combina resultados de varias computadoras sin alterarlos."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Archivos benchmark_result.json o directorios que los contienen.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark_comparison.json"),
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Permite resultados incompletos únicamente para diagnóstico.",
    )
    parser.add_argument(
        "--allow-mismatch",
        action="store_true",
        help="Escribe la comparación aunque cambie el contrato o el código.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    resolved_inputs = [_resolve_result(path) for path in args.inputs]
    records = []
    machine_ids: set[str] = set()
    reference_contract: dict | None = None
    reference_source_fingerprints: dict | None = None
    warnings: list[str] = []

    for path in resolved_inputs:
        payload = _load_result(path, allow_partial=args.allow_partial)
        machine_id = str(payload["manifest"]["machine_id"])
        if machine_id in machine_ids:
            raise ValueError(f"machine_id repetido: {machine_id}")
        machine_ids.add(machine_id)

        protocol = payload["manifest"].get("protocol", {})
        contract = {
            "benchmark_script_sha256": protocol.get("benchmark_script_sha256"),
            "cases": protocol.get("cases"),
            "workers": protocol.get("workers"),
            "startup_definition": protocol.get("startup_definition"),
            "startup_execution": protocol.get("startup_execution"),
            "startup_enabled": protocol.get("startup_enabled"),
            "calculations_enabled": protocol.get("calculations_enabled"),
            "calculation_execution": protocol.get("calculation_execution"),
            "startup_warmups": protocol.get("startup_warmups"),
            "startup_runs": protocol.get("startup_runs"),
            "calculation_runs": protocol.get("calculation_runs"),
            "calculation_warmups_per_worker": protocol.get(
                "calculation_warmups_per_worker"
            ),
            "startup_timeout_seconds": protocol.get("startup_timeout_seconds"),
            "calculation_timeout_seconds": protocol.get(
                "calculation_timeout_seconds"
            ),
            "thread_environment": protocol.get("thread_environment"),
        }
        if reference_contract is None:
            reference_contract = contract
        elif contract != reference_contract:
            warnings.append(
                f"{machine_id}: el contrato no coincide con la primera ejecución."
            )

        software = payload["manifest"].get("software", {})
        source_fingerprints = software.get("source_fingerprints")
        if reference_source_fingerprints is None:
            reference_source_fingerprints = source_fingerprints
        elif source_fingerprints != reference_source_fingerprints:
            warnings.append(
                f"{machine_id}: el código fuente no coincide con la primera ejecución."
            )

        records.append(
            {
                "machine_id": machine_id,
                "source_file": f"{machine_id}/{path.name}",
                "source_sha256": _sha256(path),
                "result": payload,
            }
        )

    if warnings and not args.allow_mismatch:
        raise ValueError(
            "Los resultados no son directamente comparables: "
            + " ".join(warnings)
            + " Use --allow-mismatch solo para diagnóstico."
        )

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    combined = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reference_contract": reference_contract,
        "reference_source_fingerprints": reference_source_fingerprints,
        "warnings": warnings,
        "machines": records,
    }
    output.write_text(
        json.dumps(combined, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
