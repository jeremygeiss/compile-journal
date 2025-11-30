import os
import glob
from datetime import datetime
from collections import defaultdict
import shutil
import logging


def parse_journal(file_path):
    """
    Parse the existing Journal.md into a nested dict: year -> month -> list of (dt, content)
    """
    logging.info(f"Starting to parse {file_path}")
    structure = defaultdict(lambda: defaultdict(list))
    if not os.path.exists(file_path):
        logging.info(f"{file_path} does not exist, returning empty structure")
        return structure

    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
        logging.info(f"Successfully read {len(lines)} lines from {file_path}")
    except IOError as e:
        logging.error(f"Error reading {file_path}: {e}")
        return structure

    current_year = None
    current_month = None
    current_dt = None
    current_content = []

    for line in lines:
        stripped = line.strip()

        # Check for year header
        if stripped.startswith("# "):
            year_str = stripped[2:].strip()
            if len(year_str) == 4 and year_str.isdigit():
                if current_dt:
                    structure[current_year][current_month].append(
                        (current_dt, "".join(current_content))
                    )
                    current_content = []
                current_year = year_str
                current_month = None
                current_dt = None
                logging.debug(f"New year section: {current_year}")
                continue

        # Check for month header
        if stripped.startswith("## "):
            month_str = stripped[3:].strip()
            if (
                len(month_str) == 7
                and month_str[:4].isdigit()
                and month_str[4] == "-"
                and month_str[5:7].isdigit()
            ):
                if current_dt:
                    structure[current_year][current_month].append(
                        (current_dt, "".join(current_content))
                    )
                    current_content = []
                current_month = month_str
                current_dt = None
                logging.debug(f"New month section: {current_month}")
                continue

        # Check for entry header
        if stripped.startswith("### "):
            dt_str = stripped[4:].strip()
            try:
                new_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                if current_dt:
                    structure[current_year][current_month].append(
                        (current_dt, "".join(current_content))
                    )
                current_dt = new_dt
                current_content = []
                logging.debug(f"New entry at {dt_str}")
                continue
            except ValueError:
                logging.warning(
                    f"Invalid date format in {file_path}: {dt_str}. Treating as content."
                )
                # Fall through to append as content

        # Append to current content if in an entry
        if current_dt:
            current_content.append(line)

    # Don't forget the last one
    if current_dt:
        structure[current_year][current_month].append(
            (current_dt, "".join(current_content))
        )

    logging.info(f"Parsing completed. Structure has {len(structure)} years")
    return structure


def add_new_entries(structure):
    """
    Find all journal_*.md files, parse their dates and content, add to structure
    """
    logging.info("Starting to add new entries")
    source_files = glob.glob("journal_*.md")
    logging.info(f"Found {len(source_files)} potential source files")
    new_entries = []
    skipped_files = []

    for file in source_files:
        logging.debug(f"Processing file: {file}")
        filename = os.path.basename(file)
        if not filename.endswith(".md") or not filename.startswith("journal_"):
            logging.warning(f"File {file} does not match pattern, skipping")
            skipped_files.append(file)
            continue
        date_time_str = filename[8:-3]  # Remove 'journal_' and '.md'
        try:
            date_str, time_str = date_time_str.split("_")
            time_formatted = time_str[:2] + ":" + time_str[2:]
            dt = datetime.strptime(f"{date_str} {time_formatted}", "%Y-%m-%d %H:%M")
            logging.debug(f"Parsed date: {dt}")
        except ValueError as e:
            logging.error(f"Skipping invalid file {file}: {e}")
            skipped_files.append(file)
            continue

        try:
            with open(file, "r") as f:
                content = f.read().strip() + "\n\n"  # Ensure ends with newlines
            logging.debug(f"Read content from {file}, length: {len(content)}")
        except IOError as e:
            logging.error(f"Error reading {file}: {e}")
            skipped_files.append(file)
            continue

        year = str(dt.year)
        month = dt.strftime("%Y-%m")
        structure[year][month].append((dt, content))
        logging.info(f"Added entry from {file} to {year}-{month}")

        new_entries.append(file)

    logging.info(f"Added {len(new_entries)} new entries, skipped {len(skipped_files)}")
    return new_entries, skipped_files


def sort_structure(structure):
    """
    Sort entries within each month
    """
    logging.info("Starting to sort structure")
    for year in structure:
        for month in structure[year]:
            logging.debug(
                f"Sorting {year}-{month} with {len(structure[year][month])} entries"
            )
            structure[year][month].sort(key=lambda x: x[0])  # Sort by datetime
    logging.info("Sorting completed")


def write_journal(file_path, structure):
    """
    Write the structure back to Journal.md in markdown format
    """
    logging.info(f"Starting to write to {file_path}")
    try:
        with open(file_path, "w") as f:
            # Sort years ascending
            for year in sorted(structure.keys()):
                f.write(f"# {year}\n\n")
                logging.debug(f"Wrote year header: {year}")
                # Sort months ascending
                for month in sorted(structure[year].keys()):
                    f.write(f"## {month}\n\n")
                    logging.debug(f"Wrote month header: {month}")
                    for dt, content in structure[year][month]:
                        f.write(f"### {dt.strftime('%Y-%m-%d %H:%M')}\n\n")
                        f.write(content)
                        logging.debug(f"Wrote entry for {dt}")
        logging.info(f"Successfully wrote to {file_path}")
    except IOError as e:
        logging.error(f"Error writing to {file_path}: {e}")
        raise IOError(f"Error writing to {file_path}: {e}")


def backup_source_files(files):
    """
    Backup the processed source files to 'backup' subfolder
    """
    logging.info("Starting backup of source files")
    backup_dir = "backup"
    try:
        os.makedirs(backup_dir, exist_ok=True)
        logging.info(f"Backup directory {backup_dir} ensured")
    except OSError as e:
        logging.error(f"Error creating backup directory: {e}")
        return files  # If can't create, treat all as failed

    failed_backups = []
    for file in files:
        logging.debug(f"Backing up {file}")
        try:
            shutil.copy(file, os.path.join(backup_dir, os.path.basename(file)))
            logging.info(f"Backed up {file}")
        except (IOError, OSError) as e:
            logging.error(f"Error backing up {file}: {e}")
            failed_backups.append(file)
    logging.info(f"Backup completed, failed: {len(failed_backups)}")
    return failed_backups


def remove_source_files(files):
    """
    Remove the processed source files
    """
    logging.info("Starting removal of source files")
    failed_removals = []
    for file in files:
        logging.debug(f"Removing {file}")
        try:
            os.remove(file)
            logging.info(f"Removed {file}")
        except OSError as e:
            logging.error(f"Error removing {file}: {e}")
            failed_removals.append(file)
    logging.info(f"Removal completed, failed: {len(failed_removals)}")
    return failed_removals


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Script started")
    journal_file = "Journal.md"
    try:
        structure = parse_journal(journal_file)
        new_entries, skipped = add_new_entries(structure)
        if not new_entries:
            logging.info("No new journal files to compile.")
            return
        failed_backups = backup_source_files(new_entries)
        sort_structure(structure)
        write_journal(journal_file, structure)
        failed_removals = remove_source_files(new_entries)
        logging.info(f"Compiled {len(new_entries)} files into {journal_file}.")
        if skipped:
            logging.info(f"Skipped {len(skipped)} invalid files.")
        if failed_backups:
            logging.info(f"Failed to backup {len(failed_backups)} files.")
        if failed_removals:
            logging.info(f"Failed to remove {len(failed_removals)} files.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    logging.info("Script ended")


if __name__ == "__main__":
    main()
