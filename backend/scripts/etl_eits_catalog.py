#!/usr/bin/env python3
"""
E-ITS Catalog ETL Pipeline
Downloads E-ITS Excel from RIA, transforms, loads into PostgreSQL.

Usage:
    PYTHONPATH=. python scripts/etl_eits_catalog.py --year 2024
    PYTHONPATH=. python scripts/etl_eits_catalog.py --year 2024 --log-level DEBUG
    PYTHONPATH=. python scripts/etl_eits_catalog.py --dry-run
    PYTHONPATH=. python scripts/etl_eits_catalog.py --local-file /path/to/file.xlsx
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
import tempfile
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.eits_catalog_measure import EitsCatalogMeasure
from app.models.eits_catalog_version import EitsCatalogVersion
from app.models.eits_measure import EitsMeasure
from app.models.eits_module import EitsModule
from app.models.eits_module_measure import EitsModuleMeasure


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


logger = logging.getLogger("etl_eits_catalog")

PROCESS_GROUPS = {"ISMS", "ORP", "CON", "OPS", "DER"}
SYSTEM_GROUPS = {"INF", "NET", "SYS", "APP", "IND"}

LEVEL_MAP = {
    "põhimeede": "BASE",
    "standardturve": "STANDARD",
    "standardmeede": "STANDARD",
    "tuumikuturve": "STANDARD",
    "kõrgturve": "HIGH",
    "kõrgmeede": "HIGH",
    "base": "BASE",
    "standard": "STANDARD",
    "high": "HIGH",
}


def get_level(raw: str) -> str | None:
    if not raw or not isinstance(raw, str):
        return None
    normalized = raw.strip().lower()
    return LEVEL_MAP.get(normalized)


def get_module_type(group: str) -> str:
    if group in PROCESS_GROUPS:
        return "PROCESS"
    if group in SYSTEM_GROUPS:
        return "SYSTEM"
    return "PROCESS"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E-ITS Catalog ETL: Download and import E-ITS catalog from RIA Excel."
    )
    parser.add_argument(
        "--year",
        type=str,
        default=os.environ.get("EITS_IMPORT_YEAR", ""),
        help="E-ITS year to import (e.g. 2024). Overrides EITS_IMPORT_YEAR env var.",
    )
    parser.add_argument(
        "--source-url",
        type=str,
        default=os.environ.get("EITS_SOURCE_URL", ""),
        help="Override download URL.",
    )
    parser.add_argument(
        "--local-file",
        type=str,
        help="Use a local Excel file instead of downloading.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract + Transform only. No database writes.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    return parser.parse_args()


def download_file(url: str) -> tuple[bytes, str]:
    logger.info("Downloading: %s", url)
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    content = response.content
    file_hash = hashlib.sha256(content).hexdigest()
    size_kb = len(content) / 1024
    logger.info("Downloaded %.1f KB, SHA256: %s", size_kb, file_hash[:16])
    return content, file_hash


def load_excel(content: bytes | None, local_path: str | None) -> pd.DataFrame:
    logger.info("Loading Excel data...")
    if local_path:
        logger.info("Reading from local file: %s", local_path)
        df = pd.read_excel(local_path, engine="openpyxl", header=None)
    else:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            f.write(content)
            tmp_path = f.name
        try:
            df = pd.read_excel(tmp_path, engine="openpyxl", header=None)
        finally:
            os.unlink(tmp_path)

    header_row = 3
    for i in range(min(10, len(df))):
        row_vals = [str(v).lower() for v in df.iloc[i].values if pd.notna(v)]
        if any("moodulgrupp" in v or "e-its versioon" in v for v in row_vals):
            header_row = i
            break

    df.columns = df.iloc[header_row].values
    df = df.iloc[header_row + 1:].reset_index(drop=True)
    df.columns = [str(c) if pd.notna(c) else f"col_{i}" for i, c in enumerate(df.columns)]

    logger.info("Loaded %d rows, %d columns (header at row %d)", len(df), len(df.columns), header_row)
    return df


def detect_columns(df: pd.DataFrame) -> dict:
    col_map = {}
    lower_cols = {str(c).lower().strip(): c for c in df.columns}

    col_map["module_group"] = next(
        (lower_cols[k] for k in lower_cols if "moodulgrupp" in k), None
    )
    col_map["module_code"] = next(
        (lower_cols[k] for k in lower_cols if "moodul: 1" in k or "moodul: 1. taseme" in k), None
    )
    col_map["module_name"] = next(
        (lower_cols[k] for k in lower_cols if "moodul: 2" in k or "moodul: 3" in k), None
    )
    col_map["module_category"] = next(
        (lower_cols[k] for k in lower_cols if any(x in k for x in ["kategooria", "category", "valdkond"])), None
    )
    col_map["measure_code"] = next(
        (lower_cols[k] for k in lower_cols if "meetme tunnus" in k), None
    )
    col_map["measure_name"] = next(
        (lower_cols[k] for k in lower_cols if "meetme nimetus" in k), None
    )
    col_map["measure_level"] = next(
        (lower_cols[k] for k in lower_cols if "meetme tase" in k), None
    )
    col_map["description"] = next(
        (lower_cols[k] for k in lower_cols if "meetme sisu" in k), None
    )
    col_map["responsible"] = next(
        (lower_cols[k] for k in lower_cols if "mooduli vastutaja" in k), None
    )

    found = {k: v for k, v in col_map.items() if v is not None}
    missing = [k for k, v in col_map.items() if v is None]
    logger.info("Detected columns: %s", found)
    if missing:
        logger.warning("Could not auto-detect columns: %s", missing)
    return col_map


def transform(df: pd.DataFrame, col_map: dict, year: str) -> dict:
    modules: dict[str, dict] = {}
    measures: dict[str, dict] = {}
    catalog_entries: list[dict] = []

    for idx, row in df.iterrows():
        row_dict = {str(k): v for k, v in row.items() if pd.notna(v)}

        raw_module_code = str(row_dict.get(col_map["module_code"], "")).strip() if col_map.get("module_code") else ""

        code_match = raw_module_code.split(":")[0].strip() if ":" in raw_module_code else raw_module_code.split(".")[0].strip()
        if not code_match or "." not in code_match:
            logger.debug("Row %d: no valid module code ('%s'), skipping", idx, raw_module_code)
            continue

        module_code = code_match.strip()
        module_name = raw_module_code.split(":")[-1].strip() if ":" in raw_module_code else module_code

        module_group = module_code.split(".")[0].strip() if module_code else ""
        module_category = str(row_dict.get(col_map["module_category"], "")).strip() if col_map.get("module_category") else ""

        if module_code not in modules:
            modules[module_code] = {
                "code": module_code,
                "name": module_name or module_code,
                "module_group": module_group,
                "module_type": get_module_type(module_group),
                "category": module_category,
                "description": str(row_dict.get(col_map["description"], "")).strip() if col_map.get("description") else "",
            }

        raw_level = str(row_dict.get(col_map["measure_level"], "")).strip() if col_map.get("measure_level") else ""
        level = get_level(raw_level)
        if not level:
            logger.warning("Row %d: unknown measure level '%s', skipping measure", idx, raw_level)
            continue

        raw_measure_code = str(row_dict.get(col_map["measure_code"], "")).strip() if col_map.get("measure_code") else ""
        measure_name = str(row_dict.get(col_map["measure_name"], "")).strip() if col_map.get("measure_name") else ""

        if not raw_measure_code:
            logger.debug("Row %d: no measure code, skipping", idx)
            continue

        full_measure_code = raw_measure_code.strip()
        if full_measure_code not in measures:
            measures[full_measure_code] = {
                "code": full_measure_code,
                "title": measure_name or full_measure_code,
                "description": str(row_dict.get(col_map["description"], "")).strip() if col_map.get("description") else "",
                "measure_level": level,
                "responsible_role": str(row_dict.get(col_map["responsible"], "")).strip() if col_map.get("responsible") else "",
            }

        catalog_entries.append({
            "module_code": module_code,
            "measure_code": full_measure_code,
            "code": full_measure_code,
            "name": measure_name or full_measure_code,
            "measure_level": level,
            "description": str(row_dict.get(col_map["description"], "")).strip() if col_map.get("description") else "",
            "responsible_role": str(row_dict.get(col_map["responsible"], "")).strip() if col_map.get("responsible") else "",
        })

    logger.info(
        "Transformed: %d modules, %d unique measures, %d catalog entries",
        len(modules), len(measures), len(catalog_entries),
    )
    return {"modules": modules, "measures": measures, "catalog_entries": catalog_entries}


def _delete_existing_version(session: Session, version_id: uuid.UUID) -> None:
    session.query(EitsModuleMeasure).filter(
        EitsModuleMeasure.module_id.in_(
            session.query(EitsModule.id).filter(EitsModule.catalog_version_id == version_id)
        )
    ).delete(synchronize_session=False)
    session.query(EitsCatalogMeasure).filter(
        EitsCatalogMeasure.module_id.in_(
            session.query(EitsModule.id).filter(EitsModule.catalog_version_id == version_id)
        )
    ).delete(synchronize_session=False)
    session.query(EitsModule).filter(
        EitsModule.catalog_version_id == version_id
    ).delete(synchronize_session=False)
    session.query(EitsMeasure).filter(
        EitsMeasure.catalog_version_id == version_id
    ).delete(synchronize_session=False)


def load(
    session: Session,
    data: dict,
    year: str,
    source_url: str,
    file_hash: str,
    dry_run: bool,
) -> EitsCatalogVersion:
    existing = session.query(EitsCatalogVersion).filter(
        EitsCatalogVersion.year == year
    ).first()

    if existing:
        if existing.source_file_hash == file_hash:
            logger.warning(
                "E-ITS %s already imported (hash matches). Skipping. "
                "Use --dry-run first to preview what would be imported.",
                year
            )
            return existing
        logger.warning(
            "E-ITS %s exists but file changed. Deleting old records and re-importing.",
            year
        )
        _delete_existing_version(session, existing.id)
        session.flush()

        version_obj = existing
        version_obj.source_file_hash = file_hash
        version_obj.source_name = f"RIA E-ITS {year} Excel"
        version_obj.imported_at = datetime.now(UTC)
    else:
        version_obj = EitsCatalogVersion(
            version=year,
            year=year,
            name=f"E-ITS {year} Catalog",
            source_name=f"RIA E-ITS {year} Excel",
            source_file_hash=file_hash,
            active=False,
            is_active=False,
        )
        session.add(version_obj)
        session.flush()

    module_id_map: dict[str, uuid.UUID] = {}
    measure_id_map: dict[str, uuid.UUID] = {}

    for m_data in data["modules"].values():
        module = EitsModule(
            catalog_version_id=version_obj.id,
            code=m_data["code"],
            name=m_data["name"],
            module_group=m_data["module_group"],
            module_type=m_data["module_type"],
            category=m_data["category"],
            description=m_data["description"],
            source_url=source_url,
        )
        session.add(module)
        session.flush()
        module_id_map[m_data["code"]] = module.id
        logger.debug("Inserted module: %s (%s)", m_data["code"], module.id)

    for m_data in data["measures"].values():
        measure = EitsMeasure(
            catalog_version_id=version_obj.id,
            code=m_data["code"],
            title=m_data["title"],
            description=m_data["description"],
            measure_level=m_data["measure_level"],
            responsible_role=m_data["responsible_role"],
        )
        session.add(measure)
        session.flush()
        measure_id_map[m_data["code"]] = measure.id
        logger.debug("Inserted measure: %s (%s)", m_data["code"], measure.id)

    for entry in data["catalog_entries"]:
        module_id = module_id_map.get(entry["module_code"])
        measure_id = measure_id_map.get(entry["measure_code"])
        if not module_id or not measure_id:
            logger.warning(
                "Skipping catalog entry: module=%s (found=%s), measure=%s (found=%s)",
                entry["module_code"], bool(module_id),
                entry["measure_code"], bool(measure_id),
            )
            continue

        catalog_measure = EitsCatalogMeasure(
            module_id=module_id,
            code=entry["code"],
            name=entry["name"],
            measure_level=entry["measure_level"],
            description=entry["description"],
            responsible_role=entry["responsible_role"],
        )
        session.add(catalog_measure)
        session.flush()

        link = EitsModuleMeasure(
            module_id=module_id,
            measure_id=measure_id,
        )
        session.add(link)

    if dry_run:
        session.rollback()
        logger.info("Dry run complete. No data written.")
        return version_obj

    session.commit()
    logger.info(
        "Import complete: %d modules, %d measures, %d catalog entries",
        len(module_id_map), len(measure_id_map), len(data["catalog_entries"]),
    )
    return version_obj


def main() -> int:
    start = datetime.now(UTC)
    args = parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    year = args.year
    if not year:
        settings = get_settings()
        year = getattr(settings, "EITS_IMPORT_YEAR", None) or ""
    if not year:
        logger.error(
            "Year is required. Use --year, set EITS_IMPORT_YEAR in .env, or provide --source-url."
        )
        return 1

    source_url = args.source_url
    if not source_url:
        settings = get_settings()
        source_url = getattr(settings, "EITS_SOURCE_URL", None) or ""

    if not source_url and not args.local_file:
        logger.error(
            "No source URL. Set EITS_SOURCE_URL in .env, use --source-url, or --local-file."
        )
        return 1

    file_hash = "manual"
    try:
        if args.local_file:
            content = None
            file_hash = "local:" + args.local_file
        else:
            content, file_hash = download_file(source_url)
    except requests.RequestException as e:
        logger.error("Download failed: %s", e)
        return 1
    except Exception as e:
        logger.error("Unexpected error during download: %s", e)
        return 1

    try:
        df = load_excel(content, args.local_file)
    except Exception as e:
        logger.error("Failed to load Excel: %s", e)
        return 1

    col_map = detect_columns(df)
    data = transform(df, col_map, year)

    if args.dry_run:
        logger.info("=== DRY RUN SUMMARY ===")
        logger.info("Year: %s", year)
        logger.info("Modules (%d): %s", len(data["modules"]), list(data["modules"].keys())[:10])
        logger.info("Measures (%d): %s", len(data["measures"]), list(data["measures"].keys())[:10])
        logger.info("Catalog entries: %d", len(data["catalog_entries"]))
        return 0

    try:
        with get_session() as session:
            try:
                version = load(session, data, year, source_url, file_hash, args.dry_run)
            except SQLAlchemyError as e:
                logger.error("Database error: %s", e)
                session.rollback()
                return 1
            except Exception as e:
                logger.error("Unexpected error during load: %s", e)
                session.rollback()
                return 1
    except Exception as e:
        logger.error("Failed to get database session: %s", e)
        return 1

    elapsed = (datetime.now(UTC) - start).total_seconds()
    logger.info("ETL completed in %.1fs", elapsed)
    version_id = version.id
    version_ver = version.version
    logger.info("Catalog version: %s (%s)", version_id, version_ver)
    return 0


if __name__ == "__main__":
    sys.exit(main())
