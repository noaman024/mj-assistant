"""
MJ Storage Compression & Archive Manager
Provides high-efficiency ZIP compression, extraction, inspection, and automatic archiving
to maintain ultra-lean storage and minimal memory footprint.
"""

import os
import sys
import zipfile
import shutil
import logging
from pathlib import Path
from datetime import datetime

from backend.config.settings import DATA_DIR, USER_NAME

logger = logging.getLogger("MJ.CompressionManager")

ARCHIVES_DIR = DATA_DIR / "archives"
ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)

class CompressionManager:
    """Manages ZIP archiving, extraction, and automated storage optimization"""

    def __init__(self):
        self.archives_dir = ARCHIVES_DIR

    def create_data_backup(self, custom_name: str = None) -> str:
        """
        Compresses all active JSON databases, learned skills, and memories into a high-compression ZIP file.
        Returns detailed summary of bytes saved.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mj_data_vault_{timestamp}.zip" if not custom_name else f"{custom_name}.zip"
        zip_path = self.archives_dir / filename

        total_uncompressed = 0

        files_to_pack = [
            DATA_DIR / "memories.json",
            DATA_DIR / "learned_rules.json",
            DATA_DIR / "learned_skills.json",
            DATA_DIR / "contacts.json",
            DATA_DIR / "apps_cache.json",
            DATA_DIR / "voicemails.json",
        ]

        # Also pack custom skills, autonomous tasks, and voicemails
        directories_to_pack = [
            DATA_DIR / "skills",
            DATA_DIR / "autonomous_tasks",
            DATA_DIR / "voicemails"
        ]

        try:
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                for file_path in files_to_pack:
                    if file_path.exists():
                        size = file_path.stat().st_size
                        total_uncompressed += size
                        zipf.write(file_path, arcname=file_path.name)

                for dir_path in directories_to_pack:
                    if dir_path.exists():
                        for root, _, files in os.walk(dir_path):
                            for file in files:
                                full_file = Path(root) / file
                                rel_path = full_file.relative_to(DATA_DIR)
                                total_uncompressed += full_file.stat().st_size
                                zipf.write(full_file, arcname=str(rel_path))

            compressed_size = zip_path.stat().st_size
            saved_percent = round((1 - (compressed_size / max(total_uncompressed, 1))) * 100, 1)

            logger.info(f"Created ZIP archive: {zip_path} ({compressed_size} bytes, saved {saved_percent}%)")

            orig_kb = round(total_uncompressed / 1024, 1)
            comp_kb = round(compressed_size / 1024, 1)

            return (
                f"Noaman, maine saara data ZIP archive me compress kar diya hai! "
                f"Original size {orig_kb} KB se kam hokar sirf {comp_kb} KB ho gaya hai "
                f"({saved_percent}% storage memory bachi). Archive file: '{filename}'."
            )
        except Exception as e:
            logger.error(f"Error creating data backup ZIP: {e}")
            return f"ZIP backup banate waqt error aaya Noaman: {e}"

    def list_archive_contents(self, zip_filename: str = None) -> str:
        """
        Inspects inside a ZIP archive without needing to extract it onto disk.
        """
        target_zip = self._resolve_zip_path(zip_filename)
        if not target_zip or not target_zip.exists():
            return "Noaman, koi valid ZIP archive file nahi mili."

        try:
            with zipfile.ZipFile(target_zip, "r") as zipf:
                info_list = zipf.infolist()
                if not info_list:
                    return f"ZIP file '{target_zip.name}' khali hai Noaman."

                lines = [f"Noaman, ZIP archive '{target_zip.name}' ke andar {len(info_list)} files hain:"]
                total_orig = 0
                total_comp = 0
                for info in info_list[:12]: # Show first 12 entries
                    orig_kb = round(info.file_size / 1024, 1)
                    comp_kb = round(info.compress_size / 1024, 1)
                    total_orig += info.file_size
                    total_comp += info.compress_size
                    lines.append(f"  - {info.filename}: {orig_kb} KB (Compressed: {comp_kb} KB)")

                saved = round((1 - (total_comp / max(total_orig, 1))) * 100, 1)
                lines.append(f"\nTotal Space Saved: {saved}% (Less memory optimized)")
                return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error reading ZIP contents: {e}")
            return f"ZIP file read karte waqt error aaya: {e}"

    def extract_archive(self, zip_filename: str = None, destination_subfolder: str = "extracted_data") -> str:
        """
        Extracts files from a ZIP archive safely into a target folder.
        Includes path traversal / Zip Slip protection.
        """
        target_zip = self._resolve_zip_path(zip_filename)
        if not target_zip or not target_zip.exists():
            return "Noaman, extract karne ke liye ZIP archive file nahi mili."

        dest_dir = self.archives_dir / destination_subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(target_zip, "r") as zipf:
                for member in zipf.infolist():
                    # Zip Slip Security check: ensure path does not escape dest_dir
                    target_path = dest_dir / member.filename
                    if not str(target_path.resolve()).startswith(str(dest_dir.resolve())):
                        logger.warning(f"Prevented unsafe path traversal in ZIP member: {member.filename}")
                        continue
                    zipf.extract(member, dest_dir)

            return f"Noaman, maine ZIP archive '{target_zip.name}' ko successfully '{destination_subfolder}' folder me extract kar diya hai."
        except Exception as e:
            logger.error(f"Error extracting ZIP archive: {e}")
            return f"ZIP file extract karte waqt error aaya: {e}"

    def auto_optimize_storage(self) -> str:
        """
        Scans temporary folders (autonomous tasks, old screenshots) and compresses
        them into an archive to free up host disk space and RAM.
        """
        tasks_dir = DATA_DIR / "autonomous_tasks"
        screens_dir = DATA_DIR / "screenshots"

        archive_tasks_zip = self.archives_dir / "tasks_history.zip"
        files_archived = 0

        try:
            with zipfile.ZipFile(archive_tasks_zip, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                # Archive autonomous generated scripts
                if tasks_dir.exists():
                    for f in tasks_dir.glob("*.py"):
                        zipf.write(f, arcname=f"tasks/{f.name}")
                        f.unlink()
                        files_archived += 1

                # Archive screenshots
                if screens_dir.exists():
                    for f in screens_dir.glob("*.png"):
                        zipf.write(f, arcname=f"screenshots/{f.name}")
                        f.unlink()
                        files_archived += 1

            # Also create fresh data backup
            self.create_data_backup("latest_data_vault")

            return (
                f"Storage optimize ho gayi hai Noaman! Maine {files_archived} temporary files ko ZIP me compress karke "
                f"active memory aur storage free kar di hai. Saara data vault archive me safe hai."
            )
        except Exception as e:
            logger.error(f"Auto storage optimization failed: {e}")
            return f"Storage optimize karte waqt error aaya: {e}"

    def compress_any_folder_or_file(self, source_path_str: str, output_zip_str: str = None) -> str:
        """Compresses any arbitrary user folder or file into a ZIP archive"""
        src = Path(source_path_str)
        if not src.exists():
            return f"Path '{source_path_str}' nahi mila Noaman."

        if not output_zip_str:
            out_zip = src.parent / f"{src.stem}.zip"
        else:
            out_zip = Path(output_zip_str)

        try:
            with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                if src.is_file():
                    zipf.write(src, arcname=src.name)
                else:
                    for root, _, files in os.walk(src):
                        for file in files:
                            full_path = Path(root) / file
                            rel = full_path.relative_to(src)
                            zipf.write(full_path, arcname=str(rel))

            orig_mb = round(src.stat().st_size / (1024 * 1024), 2) if src.is_file() else "Folder"
            comp_mb = round(out_zip.stat().st_size / (1024 * 1024), 2)
            return f"'{src.name}' ko successfully compress karke '{out_zip.name}' ({comp_mb} MB) me save kar diya hai Noaman."
        except Exception as e:
            return f"Compress karte waqt dikkat aayi: {e}"

    def _resolve_zip_path(self, zip_filename: str = None) -> Path | None:
        if zip_filename:
            candidate = Path(zip_filename)
            if candidate.exists():
                return candidate
            candidate2 = self.archives_dir / zip_filename
            if candidate2.exists():
                return candidate2
            candidate3 = self.archives_dir / f"{zip_filename}.zip"
            if candidate3.exists():
                return candidate3

        # Default to latest zip in archives directory
        all_zips = sorted(self.archives_dir.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)
        if all_zips:
            return all_zips[0]
        return None

# Global instance
compression_manager = CompressionManager()
