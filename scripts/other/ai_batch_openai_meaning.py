#!/usr/bin/env python3
"""Run an OpenAI Batch API translation job end-to-end: upload, wait, save to db."""

import json
import time

import openai
from openai import OpenAI
from openai.types import Batch

from db.db_helpers import get_db_session
from db.models import Russian, Tamil
from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr

dpspth = DPSPaths()
pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

_TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}


def _get_openai_client() -> OpenAI | None:
    """Return an OpenAI client for the Batch API, which AIManager does not support."""
    api_key = config_read("apis", "openai")
    if not api_key:
        pr.red("OpenAI API key is not configured (apis.openai).")
        return None
    return OpenAI(api_key=api_key)


def upload_and_create_batch(file_name: str) -> str | None:
    """Upload a batch input file and create the batch job. Returns the batch ID."""
    pr.tic()
    client = _get_openai_client()
    if client is None:
        pr.toc()
        return None

    file_path = dpspth.ai_for_batch_api_dir / f"{file_name}.jsonl"
    batch_id: str | None = None
    try:
        pr.green_tmr(f"uploading {file_path.name}")
        with open(file_path, "rb") as file:
            batch_input_file = client.files.create(file=file, purpose="batch")
        pr.yes("ok")

        pr.green_tmr("creating batch")
        with open(file_path, encoding="utf-8") as f:
            num_lines = sum(1 for _ in f)
        batch_response = client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": f"batch of {num_lines} words"},
        )
        pr.yes(batch_response.id)
        pr.white(f"Status: {batch_response.status}")
        batch_id = batch_response.id
    except openai.APIConnectionError as e:
        pr.red("The server could not be reached")
        pr.red(str(e.__cause__))
    except openai.RateLimitError:
        pr.red("A 429 status code was received; we should back off a bit.")
    except openai.APIStatusError as e:
        pr.red(f"Another non-200-range status code was received: {e.status_code}")

    pr.toc()
    return batch_id


def check_batch_list() -> None:
    client = _get_openai_client()
    if client is None:
        return

    try:
        batches = client.batches.list()
        pr.green_title("OpenAI Batch List")
        for batch in batches:
            status_msg = f"Batch ID: {batch.id}, Status: {batch.status}"
            if batch.request_counts:
                counts = serialize_request_counts(batch.request_counts)
                status_msg += (
                    f", Progress: {counts.get('completed')}/{counts.get('total')}"
                )
            pr.white(status_msg)
    except openai.OpenAIError as e:
        pr.red(f"An error occurred while retrieving batch list: {e}")


def check_batch_status(batch_id: str) -> Batch | None:
    client = _get_openai_client()
    if client is None:
        return None

    try:
        pr.green_tmr(f"checking status: {batch_id}")
        batch_info = client.batches.retrieve(batch_id=batch_id)
        status_msg = f"Status: {batch_info.status}"
        if batch_info.request_counts:
            counts = serialize_request_counts(batch_info.request_counts)
            status_msg += f", Progress: {counts.get('completed')}/{counts.get('total')}"
            if counts.get("failed", 0) > 0:
                status_msg += f", Failed: {counts.get('failed')}"
        pr.yes(batch_info.status)
        pr.white(status_msg)
        return batch_info
    except openai.OpenAIError as e:
        pr.no("failed")
        pr.red(f"An error occurred while retrieving batch {batch_id} status: {e}")
        return None


def serialize_request_counts(request_counts: object | None) -> dict[str, int]:
    if request_counts is None:
        return {}
    return {
        "total": getattr(request_counts, "total", 0),
        "completed": getattr(request_counts, "completed", 0),
        "failed": getattr(request_counts, "failed", 0),
    }


def print_batch_info(batch_id: str) -> None:
    client = _get_openai_client()
    if client is None:
        return

    try:
        batch_info = client.batches.retrieve(batch_id=batch_id)
        batch_details = {
            "id": batch_info.id,
            "object": batch_info.object,
            "endpoint": batch_info.endpoint,
            "errors": batch_info.errors,
            "input_file_id": batch_info.input_file_id,
            "completion_window": batch_info.completion_window,
            "status": batch_info.status,
            "output_file_id": batch_info.output_file_id,
            "error_file_id": batch_info.error_file_id,
            "created_at": batch_info.created_at,
            "in_progress_at": batch_info.in_progress_at,
            "expires_at": batch_info.expires_at,
            "finalizing_at": batch_info.finalizing_at,
            "completed_at": batch_info.completed_at,
            "failed_at": batch_info.failed_at,
            "expired_at": batch_info.expired_at,
            "cancelling_at": batch_info.cancelling_at,
            "cancelled_at": batch_info.cancelled_at,
            "request_counts": serialize_request_counts(batch_info.request_counts),
            "metadata": batch_info.metadata,
        }
        pr.white(json.dumps(batch_details, indent=2))
    except openai.OpenAIError as e:
        pr.red(f"An error occurred while retrieving batch {batch_id} information: {e}")


def cancel_batch(batch_id: str) -> None:
    client = _get_openai_client()
    if client is None:
        return

    try:
        pr.green_tmr(f"cancelling batch {batch_id}")
        batch_info = client.batches.retrieve(batch_id=batch_id)
        if batch_info:
            client.batches.cancel(batch_id=batch_id)
            pr.yes("ok")
        else:
            pr.no("not found")
    except openai.APIError as e:
        pr.no("failed")
        pr.red(f"Error canceling batch '{batch_id}': {e}")


def save_batch_results(
    batch_id: str, file_name: str, skip_empty: bool = True
) -> dict[str, str]:
    pr.tic()
    client = _get_openai_client()
    if client is None:
        pr.toc()
        return {}

    ids_and_contents: dict[str, str] = {}
    try:
        pr.green_tmr(f"retrieving batch {batch_id}")
        batch_info = client.batches.retrieve(batch_id=batch_id)
        if not batch_info.output_file_id:
            pr.no("no output")
            pr.amber("No output file is available for this batch.")
            pr.toc()
            return {}

        pr.yes("ok")
        output_file_id = batch_info.output_file_id
        file_response = client.files.content(file_id=output_file_id)
        response_lines = file_response.text.splitlines()
        file_path = dpspth.ai_for_batch_api_dir / f"{file_name}.jsonl"

        total_lines = len(response_lines)
        processed_count = 0
        skipped_empty_count = 0
        error_count = 0
        missing_id_count = 0

        pr.green_tmr("saving results")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            for line_num, line in enumerate(response_lines, 1):
                try:
                    decoded_response = json.loads(line)
                    custom_id = decoded_response.get("custom_id", "")

                    if not custom_id:
                        missing_id_count += 1
                        pr.amber(f"Line {line_num}: Missing custom_id in response")
                        continue
                    record_id = (
                        custom_id.split("-")[1] if "-" in custom_id else custom_id
                    )

                    response_data = decoded_response.get("response", {})

                    if response_data.get("status_code", 200) != 200:
                        error_count += 1
                        error_msg = (
                            response_data.get("body", {})
                            .get("error", {})
                            .get("message", "Unknown error")
                        )
                        pr.red(
                            f"Line {line_num} - HTTP {response_data.get('status_code', 'unknown')}: {error_msg}"
                        )
                        continue

                    choices = response_data.get("body", {}).get("choices", [])
                    if not choices:
                        error_count += 1
                        pr.red(f"Line {line_num} - No choices in response")
                        continue

                    message = choices[0].get("message", {})
                    translated_text = message.get("content", None)

                    if not translated_text:
                        if skip_empty:
                            skipped_empty_count += 1
                        else:
                            error_count += 1
                            error_msg = response_data.get("error", {}).get(
                                "message", "Unknown error"
                            )
                            pr.red(f"Line {line_num} - Error: {error_msg}")
                        continue

                    ids_and_contents[record_id] = translated_text
                    json.dump(
                        {"id": record_id, "translated_text": translated_text},
                        f,
                        ensure_ascii=False,
                    )
                    f.write("\n")
                    processed_count += 1

                except json.JSONDecodeError as e:
                    error_count += 1
                    pr.red(f"Line {line_num} - JSON decode error: {e}")
                except KeyError as e:
                    error_count += 1
                    pr.red(f"Line {line_num} - Missing key: {e}")
                except (TypeError, AttributeError) as e:
                    error_count += 1
                    pr.red(f"Line {line_num} - Unexpected error: {e}")

        pr.yes("ok")

        pr.summary("Processed", processed_count)
        pr.summary("Skipped", skipped_empty_count)
        pr.summary("Errors", error_count)
        pr.summary("Missing IDs", missing_id_count)
        pr.summary("Total", total_lines)

        if processed_count > 0:
            pr.green(
                f"Successfully saved {processed_count} translations to {file_path}"
            )
        else:
            pr.amber("No valid translations found to save")

    except (openai.OpenAIError, OSError) as e:
        pr.no("failed")
        pr.red(f"An error occurred while downloading batch {batch_id} output file: {e}")
        return {}

    pr.toc()
    return ids_and_contents


def save_processed_ids(ids_and_contents: dict[str, str]) -> None:
    """Extract IDs from ids_and_contents and save to ai_processed_ids_json file."""
    ids = list(ids_and_contents.keys())

    try:
        if dpspth.ai_processed_ids_json.exists():
            dpspth.ai_processed_ids_json.unlink()
            pr.white(
                f"Removed existing processed IDs file: {dpspth.ai_processed_ids_json}"
            )

        with open(dpspth.ai_processed_ids_json, "w", encoding="utf-8") as f:
            json.dump(ids, f, ensure_ascii=False, indent=2)
        pr.green(f"Fresh processed IDs saved to {dpspth.ai_processed_ids_json}")
        pr.summary("Total IDs saved", len(ids))
    except OSError as e:
        pr.red(f"Error saving processed IDs: {e}")


def update_translation_table(
    ids_and_contents: dict[str, str], file_name_in: str
) -> None:
    pr.tic()
    pr.green_title("Updating translation in db")
    updated_count: int = 0
    added_count: int = 0

    # Expected filename format: {mode}-{lang}-{date}.jsonl
    parts = file_name_in.split("-")
    if len(parts) < 2:
        pr.red(f"Could not parse mode and language from filename: {file_name_in}")
        return

    mode = parts[0]
    lang = parts[1]

    if lang == "ru":
        orm_model = Russian
        field_to_update = "ru_meaning_lit" if mode == "lit" else "ru_meaning_raw"
    elif lang == "ta":
        orm_model = Tamil
        field_to_update = "ta_meaning"
    else:
        pr.red(f"Unsupported language: {lang}")
        return

    pr.white(
        f"Updating {orm_model.__name__}.{field_to_update} for lang: {lang}, mode: {mode}"
    )

    skipped_count: int = 0

    for record_id, content in ids_and_contents.items():
        content = content.replace("\n", "")
        existing_record = (
            db_session.query(orm_model).filter(orm_model.id == record_id).first()
        )
        if existing_record:
            current_value = getattr(existing_record, field_to_update)
            if not current_value:  # Only update if field is empty
                setattr(existing_record, field_to_update, content)
                updated_count += 1
                db_session.commit()
            else:
                skipped_count += 1
        else:
            record_data = {"id": record_id, field_to_update: content}
            new_record = orm_model(**record_data)
            added_count += 1
            db_session.add(new_record)

    db_session.commit()
    pr.summary("Updated", updated_count)
    pr.summary("Added", added_count)
    if skipped_count > 0:
        pr.summary("Skipped (not empty)", skipped_count)

    save_processed_ids(ids_and_contents)
    pr.toc()


def run_batch_workflow(
    file_name: str,
    poll_interval_s: int = 60,
    max_wait_s: int = 24 * 60 * 60,
) -> None:
    """Upload a batch, poll until it finishes, then save results to the db."""
    pr.green_title(f"OpenAI batch workflow: {file_name}")

    batch_id = upload_and_create_batch(file_name)
    if not batch_id:
        pr.red("Batch upload failed — aborting workflow.")
        return

    status: str | None = None
    waited_s = 0
    while waited_s <= max_wait_s:
        batch_info = check_batch_status(batch_id)
        status = batch_info.status if batch_info else None
        if status in _TERMINAL_STATUSES:
            break
        time.sleep(poll_interval_s)
        waited_s += poll_interval_s
    else:
        pr.red(f"Batch {batch_id} did not finish within {max_wait_s}s — aborting.")
        return

    if status != "completed":
        pr.red(f"Batch {batch_id} ended with status '{status}' — nothing to save.")
        return

    ids_and_contents = save_batch_results(batch_id, file_name)
    if ids_and_contents:
        update_translation_table(ids_and_contents, file_name)
    else:
        pr.amber("No valid results to update database")


if __name__ == "__main__":
    file_name_in = "meaning-ru-2026-04-27-20-20"
    run_batch_workflow(file_name_in)
