import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from tqdm import tqdm

from milkbottle.modules.pdfmilker.discovery import discover_pdfs, hash_pdf
from milkbottle.modules.pdfmilker.extract import (
    extract_images,
    extract_metadata,
    extract_text,
)
from milkbottle.modules.pdfmilker.prepare import prepare_output_tree
from milkbottle.modules.pdfmilker.relocate import relocate_pdf
from milkbottle.modules.pdfmilker.report import print_report, write_report
from milkbottle.modules.pdfmilker.transform import pdf_to_markdown
from milkbottle.modules.pdfmilker.utils import format_file_size
from milkbottle.modules.pdfmilker.validate import validate_assets, validate_pdf_hash

logger = logging.getLogger("pdfmilker.pipeline")
console = Console()


def log_jsonl(meta_dir: Path, event: str, message: str, **data) -> None:
    """
    Write a structured JSONL log entry to /meta/<slug>.log.
    Args:
        meta_dir (Path): The /meta directory for the PDF.
        event (str): Event type (e.g., 'step', 'error', 'info').
        message (str): Log message.
        **data: Additional fields to include in the log.
    """
    log_path = meta_dir / "pipeline.log"
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "message": message,
        **data,
    }
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write JSONL log: {e}")


def run_pdfmilker_pipeline(
    directory: Optional[str] = None,
    outdir: Optional[str] = None,
    overwrite: bool = False,
    images: bool = True,
    log_level: str = "info",
    dry_run: bool = False,
    pattern: Optional[str] = None,
) -> None:
    """
    Run the full PDFmilker pipeline on all PDFs in the target directory.
    Args:
        directory (Optional[str]): Directory to search for PDFs.
        outdir (Optional[str]): Output root directory.
        overwrite (bool): Overwrite existing outputs.
        images (bool): Extract images or not.
        log_level (str): Logging level.
        dry_run (bool): If True, do not write files.
        pattern (Optional[str]): Glob pattern to filter PDFs.
    """
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))
    pdf_dir = Path(directory) if directory else Path.cwd()
    output_root = Path(outdir).expanduser().resolve() if outdir else pdf_dir
    pdfs = discover_pdfs(str(pdf_dir))
    if pattern:
        pdfs = [p for p in pdfs if p.match(pattern)]
    if not pdfs:
        console.print("[yellow]No PDF files found.[/yellow]")
        return
    for pdf_path in tqdm(pdfs, desc="Processing PDFs", unit="pdf"):
        try:
            # Prepare output tree
            subdirs = prepare_output_tree(pdf_path, output_root)
            log_jsonl(
                subdirs["meta"], "step", "Prepared output tree", pdf=str(pdf_path)
            )
            # Hash before relocation
            original_hash = hash_pdf(pdf_path)
            log_jsonl(
                subdirs["meta"],
                "step",
                "Computed original hash",
                pdf=str(pdf_path),
                hash=original_hash,
            )
            # Extract
            text = extract_text(pdf_path) or ""
            log_jsonl(subdirs["meta"], "step", "Extracted text", pdf=str(pdf_path))
            meta = extract_metadata(pdf_path)
            log_jsonl(subdirs["meta"], "step", "Extracted metadata", pdf=str(pdf_path))
            image_paths = []
            if images:
                image_paths = extract_images(pdf_path, subdirs["images"])
                log_jsonl(
                    subdirs["meta"],
                    "step",
                    "Extracted images",
                    pdf=str(pdf_path),
                    images=[str(p) for p in image_paths],
                )
            # Transform
            md = pdf_to_markdown(text, meta)
            md_path = subdirs["markdown"] / f"{pdf_path.stem}.md"
            if not dry_run:
                md_path.write_text(md, encoding="utf-8")
            log_jsonl(
                subdirs["meta"],
                "step",
                "Transformed to Markdown",
                pdf=str(pdf_path),
                markdown=str(md_path),
            )
            # Validate
            assets = {
                "markdown": [md_path],
                "images": image_paths,
                "pdf": [subdirs["pdf"] / pdf_path.name],
            }
            validation = validate_assets(assets)
            log_jsonl(
                subdirs["meta"],
                "step",
                "Validated assets",
                pdf=str(pdf_path),
                validation=validation,
            )
            # Relocate
            relocated_pdf = relocate_pdf(
                pdf_path, subdirs["pdf"], overwrite=overwrite, dry_run=dry_run
            )
            log_jsonl(
                subdirs["meta"],
                "step",
                "Relocated PDF",
                pdf=str(pdf_path),
                relocated=str(relocated_pdf),
            )
            # Hash after relocation and validate
            relocated_hash = None
            hash_valid = None
            if relocated_pdf and not dry_run:
                relocated_hash = hash_pdf(relocated_pdf)
                if original_hash is not None:
                    hash_valid = validate_pdf_hash(relocated_pdf, original_hash)
                    log_jsonl(
                        subdirs["meta"],
                        "step",
                        "Validated relocated PDF hash",
                        pdf=str(pdf_path),
                        original_hash=original_hash,
                        relocated_hash=relocated_hash,
                        hash_valid=hash_valid,
                    )
                    if not hash_valid:
                        logger.error(f"Hash mismatch after relocation for {pdf_path}")
                        log_jsonl(
                            subdirs["meta"],
                            "error",
                            "Hash mismatch after relocation",
                            pdf=str(pdf_path),
                        )
                else:
                    hash_valid = None
            # Report
            report_data = {
                "file": str(pdf_path),
                "size": format_file_size(pdf_path.stat().st_size),
                "output": str(subdirs["markdown"].parent),
                "markdown": str(md_path),
                "images": [str(p) for p in image_paths],
                "metadata": meta,
                "validation": validation,
                "relocated_pdf": str(relocated_pdf) if relocated_pdf else None,
                "original_hash": original_hash,
                "relocated_hash": relocated_hash,
                "hash_valid": hash_valid,
            }
            write_report(report_data, subdirs["meta"])
            print_report(report_data)
            log_jsonl(
                subdirs["meta"],
                "info",
                "Pipeline completed successfully",
                pdf=str(pdf_path),
            )
        except Exception as e:
            logger.error(f"Pipeline failed for {pdf_path}: {e}")
            console.print(f"[red]Pipeline failed for {pdf_path}: {e}[/red]")
            # Log error to JSONL
            try:
                subdirs  # type: ignore
                log_jsonl(subdirs["meta"], "error", str(e), pdf=str(pdf_path))
            except Exception:
                pass
