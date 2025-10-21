#!/usr/bin/env python3

import openai

import os
import json

from tools.ai_related import get_ai_client, print_ai_config

from db.db_helpers import get_db_session
from db.models import Russian
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths  

dpspth = DPSPaths()
pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def upload_and_create_batch(file_name: str) -> None:
    """Uploads a file and creates a batch for processing."""
    client = get_ai_client()
    print_ai_config()
    if client is None or client.__class__.__module__.split('.')[0] != "openai":
        print("Batch API is only supported for OpenAI client.")
        return
    def _openai_upload_and_create_batch(client, file_name: str) -> None:
        file_path: str = os.path.join(dpspth.ai_for_batch_api_dir, f"{file_name}.jsonl")
        try:
            with open(file_path, "rb") as file:
                batch_input_file = client.files.create(
                    file=file,
                    purpose="batch"
                )
                print("File upload response:", batch_input_file)
                num_lines: int = sum(1 for line in open(file_path, 'r'))
                batch_response = client.batches.create(
                    input_file_id=batch_input_file.id,
                    endpoint="/v1/chat/completions",
                    completion_window="24h",
                    metadata={"description": f"batch of {num_lines} words"}
                )
                print("Batch creation response:", batch_response)
        except openai.APIConnectionError as e:
            print("The server could not be reached")
            print(e.__cause__)
        except openai.RateLimitError:
            print("A 429 status code was received; we should back off a bit.")
        except openai.APIStatusError as e:
            print("Another non-200-range status code was received")
            print(e.status_code)
            print(e.response)
    _openai_upload_and_create_batch(client, file_name)


def check_batch_list() -> None:
    client = get_ai_client()
    if client is None or client.__class__.__module__.split('.')[0] != "openai":
        print("Batch API is only supported for OpenAI client.")
        return
    def _openai_check_batch_list(client) -> None:
        try:
            batches = client.batches.list()
            for batch in batches:
                print(f"Batch ID: {batch.id}, Status: {batch.status}")
        except Exception as e:
            print("An error occurred while retrieving batch list:", str(e))
    _openai_check_batch_list(client)


def check_batch_status(batch_id: str) -> object | None:
    client = get_ai_client()
    if client is None or client.__class__.__module__.split('.')[0] != "openai":
        print("Batch API is only supported for OpenAI client.")
        return None
    def _openai_check_batch_status(client, batch_id: str) -> object | None:
        try:
            batch_info = client.batches.retrieve(batch_id=batch_id)
            print(f"Batch ID: {batch_info.id}, Status: {batch_info.status}")
            return batch_info
        except Exception as e:
            print(f"An error occurred while retrieving batch {batch_id} status:", str(e))
            return None
    return _openai_check_batch_status(client, batch_id)


def serialize_request_counts(request_counts: object | None) -> dict[str, int]:
    if request_counts is None:
        return {}
    return {
        "total": getattr(request_counts, "total", 0),
        "completed": getattr(request_counts, "completed", 0),
        "failed": getattr(request_counts, "failed", 0),
    }


def print_batch_info(batch_id: str) -> None:
    client = get_ai_client()
    if client is None or client.__class__.__module__.split('.')[0] != "openai":
        print("Batch API is only supported for OpenAI client.")
        return
    def _openai_print_batch_info(client, batch_id: str) -> None:
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
            print(json.dumps(batch_details, indent=2))
        except Exception as e:
            print(f"An error occurred while retrieving batch {batch_id} information:", str(e))
    _openai_print_batch_info(client, batch_id)


def cancel_batch(batch_id: str) -> None:
    client = get_ai_client()
    if client is None or client.__class__.__module__.split('.')[0] != "openai":
        print("Batch API is only supported for OpenAI client.")
        return
    def _openai_cancel_batch(client, batch_id: str) -> None:
        try:
            batch_info = client.batches.retrieve(batch_id=batch_id)
            if batch_info:
                client.batches.cancel(batch_id=batch_id)
                print(f"Batch '{batch_id}' has been canceld successfully.")
            else:
                print(f"Batch '{batch_id}' does not exist.")
        except openai.APIError as e:
            print(f"Error canceling batch '{batch_id}': {e}")
    _openai_cancel_batch(client, batch_id)



def save_batch_results(batch_id: str, file_name: str) -> dict[str, str]:
    client = get_ai_client()
    if client is None or client.__class__.__module__.split('.')[0] != "openai":
        print("Batch API is only supported for OpenAI client.")
        return {}
    def _openai_save_batch_results(client, batch_id: str, file_name: str) -> dict[str, str]:
        try:
            batch_info = client.batches.retrieve(batch_id=batch_id)
            if batch_info.output_file_id:
                output_file_id = batch_info.output_file_id
                file_response = client.files.content(file_id=output_file_id)
                response_lines = file_response.text.splitlines()
                ids_and_contents: dict[str, str] = {}
                file_path: str = os.path.join(dpspth.ai_from_batch_api_dir, f"{file_name}.jsonl")
                with open(file_path, 'a', encoding='utf-8') as f:
                    for line in response_lines:
                        try:
                            decoded_response = json.loads(line)
                            custom_id = decoded_response.get('custom_id', '')
                            id = custom_id.split('-')[1] if '-' in custom_id else custom_id
                            translated_text = (
                                decoded_response.get('response', {})
                                .get('body', {})
                                .get('choices', [{}])[0]
                                .get('message', {})
                                .get('content', None)
                            )
                            if translated_text and id:
                                ids_and_contents[id] = translated_text
                                json.dump({"id": id, "translated_text": translated_text}, f, ensure_ascii=False)
                                f.write('\n')
                            else:
                                print(f"Missing content or id in line: {line}")
                        except json.JSONDecodeError as e:
                            print(f"Error decoding line: {e}, Line: {line}")
                print(f"Translated texts saved to {file_path}")
                return ids_and_contents
            else:
                print("No output file is available for this batch.")
                return {}
        except Exception as e:
            print(f"An error occurred while downloading batch {batch_id} output file: {e}")
            return {}
    return _openai_save_batch_results(client, batch_id, file_name)


def update_ru_meaning_raw(ids_and_contents: dict[str, str]) -> None:
    print("Updating ru_meaning in db")
    updated_count: int = 0
    added_count: int = 0
    for id, content in ids_and_contents.items():
        content = content.replace("\n", "")
        existing_russian = db_session.query(Russian).filter(Russian.id == id).first()
        if existing_russian:
            existing_russian.ru_meaning_raw = content
            updated_count += 1
            db_session.commit()
        else:
            new_russian = Russian(id=id, ru_meaning_raw=content)
            added_count += 1
            db_session.add(new_russian)
    db_session.commit()
    print(f"Total updated records: {updated_count}")
    print(f"Total added records: {added_count}")


if __name__ == "__main__":

    file_name_in = "meaning-2025-10-20-15-00"

    # upload_and_create_batch(file_name_in)

    # check_batch_list()

    specific_batch_id = "batch_68f78347af4c8190bffc9f5031ba06f0"

    # print_batch_info(specific_batch_id)

    ids_and_contents = save_batch_results(specific_batch_id, file_name_in)
    update_ru_meaning_raw(ids_and_contents)

    # cancel_batch(specific_batch_id)

    # check_batch_status(specific_batch_id)



