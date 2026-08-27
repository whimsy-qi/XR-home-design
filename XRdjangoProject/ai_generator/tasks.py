# ai_generator/tasks.py
from celery import shared_task
from django.conf import settings
from django.apps import apps
import requests
import os
import uuid
import tempfile
import time
import json  # 确保导入json
import oss2  # 阿里云OSS SDK

# 从main应用导入相关模型和任务
from main.models import Asset, AssetSource  # AssetSource现在从main.models导入
from main.tasks import generate_thumbnail_task as generate_blender_thumbnail_task

# 导入本应用的AIGenerationTask模型
from .models import AIGenerationTask

# 从settings获取Meshy AI的配置
MESHY_API_KEY = settings.MESHY_API_KEY
MESHY_IMAGE_TO_3D_ENDPOINT = settings.MESHY_IMAGE_TO_3D_ENDPOINT
# 您可能还需要为其他Meshy功能定义端点
MESHY_TEXT_TO_3D_ENDPOINT = settings.MESHY_TEXT_TO_3D_ENDPOINT
MESHY_MULTI_IMAGE_TO_3D_ENDPOINT = settings.MESHY_MULTI_IMAGE_TO_3D_ENDPOINT
MESHY_TEXT_TO_TEXTURE_ENDPOINT = settings.MESHY_TEXT_TO_TEXTURE_ENDPOINT


# --- 辅助函数：轮询Meshy任务状态 ---
def poll_meshy_task_status(base_task_url, task_id, headers, ai_generation_record_id, max_attempts=120,
                           interval_seconds=30, stream_endpoint=False):
    AIGenerationTaskModel = apps.get_model('ai_generator', 'AIGenerationTask')
    get_task_url = f"{base_task_url}/{task_id}"


    def update_task_record_status(new_status_enum_val, progress_val=None, error_msg=None):
        if ai_generation_record_id:
            try:
                task_record_to_update = AIGenerationTaskModel.objects.get(id=ai_generation_record_id)
                task_record_to_update.status = new_status_enum_val
                if progress_val is not None:
                    task_record_to_update.progress = progress_val
                if error_msg:
                    existing_error = task_record_to_update.error_message or ""
                    task_record_to_update.error_message = (existing_error + "\n" + error_msg).strip()
                task_record_to_update.save()
            except AIGenerationTaskModel.DoesNotExist:
                print(f"Error updating AIGenerationTask status: Record {ai_generation_record_id} not found.")


    if stream_endpoint:
        status_url_stream = get_task_url + "/stream"
        print(f"Polling Meshy task {task_id} via SSE stream: {status_url_stream}...")
        try:
            response = requests.get(status_url_stream, headers={**headers, "Accept": "text/event-stream"}, stream=True,
                                    timeout=(max_attempts * interval_seconds) + 60)
            response.raise_for_status()
            last_event_data = None
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data:'):
                        data_str = line_str[5:]
                        try:
                            event_data = json.loads(data_str)
                            last_event_data = event_data
                            status_from_event = event_data.get("status")
                            progress_from_event = event_data.get("progress", 0)
                            print(
                                f"Meshy task {task_id} STREAM status: {status_from_event}, progress: {progress_from_event}%")

                            current_status_enum = AIGenerationTaskModel.AITaskStatus.AI_API_PENDING
                            if status_from_event == "SUCCEEDED":
                                current_status_enum = AIGenerationTaskModel.AITaskStatus.AI_API_SUCCEEDED
                            elif status_from_event in ["FAILED", "CANCELED"]:
                                current_status_enum = AIGenerationTaskModel.AITaskStatus.FAILED

                            update_task_record_status(current_status_enum, progress_from_event)

                            if status_from_event in ['SUCCEEDED', 'FAILED', 'CANCELED']:
                                if hasattr(response, 'close'): response.close()
                                if status_from_event == "SUCCEEDED": return event_data
                                error_message_from_event = event_data.get("task_error", {}).get("message",
                                                                                                "Unknown error from Meshy stream.")
                                raise Exception(
                                    f"Meshy task {task_id} {status_from_event}. Error: {error_message_from_event}")
                        except json.JSONDecodeError:
                            print(f"Warning: Could not decode JSON from SSE line: {data_str}")

            if last_event_data and last_event_data.get("status") == "SUCCEEDED":
                return last_event_data

            print(f"Meshy task {task_id} SSE stream ended, trying one final poll for status...")
            final_poll_response = requests.get(get_task_url, headers=headers, timeout=30)
            final_poll_response.raise_for_status()
            final_data = final_poll_response.json()
            final_status = final_data.get("status")
            if final_status == "SUCCEEDED":
                update_task_record_status(AIGenerationTaskModel.AITaskStatus.AI_API_SUCCEEDED,
                                          final_data.get("progress", 100))
                return final_data
            error_msg = final_data.get("task_error", {}).get("message", "Task ended stream without clear success.")
            update_task_record_status(AIGenerationTaskModel.AITaskStatus.FAILED, final_data.get("progress", 0),
                                      error_msg)
            raise Exception(f"Meshy task {task_id} final poll status: {final_status}. Error: {error_msg}")

        except requests.exceptions.Timeout:
            error_msg = f"Meshy task {task_id} SSE stream timed out."
            update_task_record_status(AIGenerationTaskModel.AITaskStatus.FAILED, error_msg=error_msg)
            raise Exception(error_msg)
        finally:
            if 'response' in locals() and response and hasattr(response, 'close'):
                # 尝试关闭，如果还没有关闭的话
                try:
                    # iter_lines 结束后，连接可能已自动关闭或处于可关闭状态
                    response.close()
                    print(f"Ensured SSE stream for task {task_id} is closed in finally.")
                except Exception as e_final_close:
                    print(
                        f"Note: Error or already closed during final attempt to close SSE stream for task {task_id}: {e_final_close}")
    else:  # 普通轮询
        for attempt in range(max_attempts):
            print(f"Polling Meshy task {task_id}, attempt {attempt + 1}/{max_attempts} from URL {get_task_url}...")
            response = requests.get(get_task_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            status_from_api = data.get("status")
            progress_from_api = data.get("progress", 0)
            print(f"Meshy task {task_id} status: {status_from_api}, progress: {progress_from_api}%")

            current_status_enum = AIGenerationTaskModel.AITaskStatus.AI_API_PENDING
            if status_from_api == "SUCCEEDED":
                current_status_enum = AIGenerationTaskModel.AITaskStatus.AI_API_SUCCEEDED
            elif status_from_api in ["FAILED", "CANCELED"]:
                current_status_enum = AIGenerationTaskModel.AITaskStatus.FAILED
            update_task_record_status(current_status_enum, progress_from_api)

            if status_from_api == "SUCCEEDED": return data
            if status_from_api in ["FAILED", "CANCELED"]:
                error_message = data.get("task_error", {}).get("message", "Unknown error from Meshy.")
                raise Exception(f"Meshy task {task_id} {status_from_api}. Error: {error_message}")

            if attempt == max_attempts - 1:
                # *** 这是修正的地方 ***
                error_msg_timeout = f"Meshy task {task_id} timed out after {max_attempts * interval_seconds} seconds."
                update_task_record_status(AIGenerationTaskModel.AITaskStatus.FAILED, progress_from_api,
                                          error_msg_timeout)
                raise Exception(error_msg_timeout)

            time.sleep(interval_seconds)
        # 如果循环正常结束但没有返回（理论上不应发生，因为上面有超时异常）
        error_msg_exhausted = f"Meshy task {task_id} polling exhausted and task did not reach a final state."
        update_task_record_status(AIGenerationTaskModel.AITaskStatus.FAILED, error_msg=error_msg_exhausted)
        raise Exception(error_msg_exhausted)


@shared_task(bind=True, max_retries=1, default_retry_delay=300)
def generate_3d_model_from_image_via_meshy_task(self, user_id, source_image_oss_url, generation_params,
                                                ai_generation_record_id):
    AssetModel = apps.get_model('main', 'Asset')
    User = apps.get_model('accounts', 'CustomUser')
    AIGenerationTaskModel = apps.get_model('ai_generator', 'AIGenerationTask')

    ai_task_record = None
    try:
        ai_task_record = AIGenerationTaskModel.objects.get(id=ai_generation_record_id)
        ai_task_record.status = AIGenerationTaskModel.AITaskStatus.CELERY_RECEIVED
        ai_task_record.celery_task_id = self.request.id  # 获取当前Celery任务的ID
        ai_task_record.save(update_fields=['status', 'celery_task_id'])
    except AIGenerationTaskModel.DoesNotExist:
        print(f"AI Task Log Error: AIGenerationTask {ai_generation_record_id} not found for Image-to-3D.")
        ai_generation_record_id = None  # 设为None，后续的update_task_record_status会跳过

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        error_msg = f"User with ID {user_id} not found for Image-to-3D task."
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.FAILED, error_message=error_msg)
        print(f"AI Task (ImageTo3D) Error: {error_msg}")
        return

    print(
        f"AI Task (ImageTo3D) Started for Meshy: User {user_id}, Source Image URL: {source_image_oss_url}, Params: {generation_params}")

    if not MESHY_API_KEY:
        error_msg = "MESHY_API_KEY not configured for Image-to-3D task."
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.FAILED, error_message=error_msg)
        print(f"AI Task Error: {error_msg}")
        return

    meshy_task_id_from_api = None
    temp_downloaded_3d_model_path = None
    newly_created_asset_instance = None

    try:
        headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
        payload = {
            "image_url": source_image_oss_url,
            "enable_pbr": generation_params.get("enable_pbr", True),
            "should_remesh": generation_params.get("should_remesh", True),
            "should_texture": generation_params.get("should_texture", True),
            "ai_model": generation_params.get("ai_model", "meshy-4"),
            "topology": generation_params.get("topology", "triangle"),
            "target_polycount": generation_params.get("target_polycount", 30000),
            "symmetry_mode": generation_params.get("symmetry_mode", "auto")
        }

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.AI_API_PENDING, generation_params=payload)

        print(
            f"AI Task (ImageTo3D): Calling Meshy Create Task API ({MESHY_IMAGE_TO_3D_ENDPOINT}) with payload: {payload}")
        create_task_response = requests.post(MESHY_IMAGE_TO_3D_ENDPOINT, headers=headers, json=payload, timeout=30)
        create_task_response.raise_for_status()

        meshy_task_id_from_api = create_task_response.json().get("result")
        if not meshy_task_id_from_api:
            raise Exception(f"Meshy API (ImageTo3D) did not return a task ID. Response: {create_task_response.json()}")

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            external_ai_task_id=meshy_task_id_from_api)
        print(f"AI Task (ImageTo3D): Meshy task created. ID: {meshy_task_id_from_api}")

        task_data = poll_meshy_task_status(
            MESHY_IMAGE_TO_3D_ENDPOINT,
            meshy_task_id_from_api,
            headers,
            ai_generation_record_id,
            stream_endpoint=True  # Image-to-3D API v1也支持流式 [cite: 50]
        )

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.AI_API_SUCCEEDED, meshy_result_data=task_data)

        generated_model_download_url = task_data.get("model_urls", {}).get("glb")
        # meshy_provided_thumbnail_url = task_data.get("thumbnail_url") # 暂时不直接用Meshy的缩略图

        if not generated_model_download_url:
            raise Exception(f"Meshy task {meshy_task_id_from_api} SUCCEEDED but no GLB model URL found.")
        print(f"AI Task (ImageTo3D): Meshy task SUCCEEDED. GLB URL: {generated_model_download_url}")

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.DOWNLOADING_ASSET)

        model_file_ext = '.glb'
        original_model_filename = f"ai_meshy_img3d_{meshy_task_id_from_api}{model_file_ext}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=model_file_ext) as tmp_model_file:
            temp_downloaded_3d_model_path = tmp_model_file.name

        model_response = requests.get(generated_model_download_url, stream=True, timeout=300)
        model_response.raise_for_status()
        with open(temp_downloaded_3d_model_path, 'wb') as f:
            for chunk in model_response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"AI Task (ImageTo3D): Generated 3D model downloaded to {temp_downloaded_3d_model_path}")

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.UPLOADING_TO_OSS)

        generated_3d_model_oss_key = f"generated_assets/{user_id}/{uuid.uuid4()}/{original_model_filename}"
        oss_auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        oss_bucket_endpoint = f"https://{settings.OSS_ENDPOINT}"
        oss_bucket = oss2.Bucket(oss_auth, oss_bucket_endpoint, settings.OSS_BUCKET_NAME)
        oss_bucket.put_object_from_file(generated_3d_model_oss_key, temp_downloaded_3d_model_path)
        generated_model_oss_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{generated_3d_model_oss_key}"
        print(f"AI Task (ImageTo3D): Uploaded generated 3D model to OSS key: {generated_3d_model_oss_key}")

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.CREATING_ASSET_RECORD)

        newly_created_asset_instance = AssetModel.objects.create(
            name=generation_params.get('name', f"AI Meshy - {meshy_task_id_from_api[:8]}"),
            description=generation_params.get('description',
                                              f"AI generated 3D model from image via Meshy. Task ID: {meshy_task_id_from_api}."),
            file_url=generated_model_oss_url,
            asset_type=AssetModel.AssetType.MODEL_3D,
            user=user,
            source_type=AssetSource.AI_IMAGE_TO_3D,  # 使用从main.models导入的AssetSource
            source_reference_input={'source_image_oss_url': source_image_oss_url, 'meshy_params': generation_params},
            external_ai_task_id=meshy_task_id_from_api,
            ai_model_used=payload.get("ai_model", "meshy-4")
        )
        print(f"AI Task (ImageTo3D): Created Asset record with ID: {newly_created_asset_instance.id}")

        if ai_task_record:
            AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
                generated_asset=newly_created_asset_instance,
                status=AIGenerationTaskModel.AITaskStatus.TRIGGERING_THUMBNAIL
            )

        generate_blender_thumbnail_task.delay(
            asset_id=str(newly_created_asset_instance.id),
            original_file_url_from_view=generated_model_oss_url,
            asset_type_key_str=newly_created_asset_instance.asset_type
        )
        print(
            f"AI Task (ImageTo3D): Triggered Blender thumbnail generation for Asset ID: {newly_created_asset_instance.id}")

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.COMPLETED)

    except requests.exceptions.HTTPError as e_http:
        error_message = f"HTTP error during Meshy API interaction (ImageTo3D). Task ID: {meshy_task_id_from_api if meshy_task_id_from_api else 'N/A'}."
        if e_http.response is not None: error_message += f" Status: {e_http.response.status_code}. Body: {e_http.response.text[:500]}"
        print(error_message)
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.FAILED, error_message=error_message)
        if e_http.response is not None and e_http.response.status_code >= 500: self.retry(exc=e_http)
    except Exception as e_generic:
        error_message = f"An unexpected error in AI Task (ImageTo3D). Task ID: {meshy_task_id_from_api if meshy_task_id_from_api else 'N/A'}: {e_generic}"
        print(error_message)
        import traceback
        traceback.print_exc()
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.FAILED,
            error_message=error_message + "\n" + traceback.format_exc())
    finally:
        if temp_downloaded_3d_model_path and os.path.exists(temp_downloaded_3d_model_path):
            try:
                os.remove(temp_downloaded_3d_model_path)
                print(f"AI Task: Cleaned up temp model: {temp_downloaded_3d_model_path}")
            except Exception as e_clean:
                print(f"AI Task: Error cleaning up temp model {temp_downloaded_3d_model_path}: {e_clean}")


@shared_task(bind=True, max_retries=1, default_retry_delay=300)
def generate_text_to_3d_via_meshy_task(self, user_id, prompt, asset_name, asset_description, meshy_params,
                                       ai_generation_record_id):
    AssetModel = apps.get_model('main', 'Asset')
    User = apps.get_model('accounts', 'CustomUser')
    AIGenerationTaskModel = apps.get_model('ai_generator', 'AIGenerationTask')

    ai_task_record = None
    try:
        ai_task_record = AIGenerationTaskModel.objects.get(id=ai_generation_record_id)
        ai_task_record.status = AIGenerationTaskModel.AITaskStatus.CELERY_RECEIVED
        ai_task_record.celery_task_id = self.request.id
        ai_task_record.save(update_fields=['status', 'celery_task_id'])
    except AIGenerationTaskModel.DoesNotExist:
        print(f"AI Task Log Error: AIGenerationTask {ai_generation_record_id} not found for Text-to-3D.")
        ai_generation_record_id = None

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        error_msg = f"User with ID {user_id} not found for Text-to-3D task."
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.FAILED, error_message=error_msg)
        print(f"AI Task (TextTo3D) Error: {error_msg}")
        return

    print(f"AI Task (TextTo3D) Started: User {user_id}, Prompt: '{prompt}', Params: {meshy_params}")

    if not MESHY_API_KEY or not MESHY_TEXT_TO_3D_ENDPOINT:
        error_msg = "MESHY_API_KEY or MESHY_TEXT_TO_3D_ENDPOINT not configured."
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.FAILED, error_message=error_msg)
        print(f"AI Task Error: {error_msg}")
        return

    headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    preview_task_id_from_api = None
    refined_task_id_from_api = None
    temp_downloaded_3d_model_path = None
    newly_created_asset_instance = None

    try:
        # --- 阶段1: 创建并轮询预览任务 ---
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.AI_API_PENDING,
            task_type=AIGenerationTaskModel.AITaskType.TEXT_TO_3D_PREVIEW)

        preview_payload = {
            "mode": "preview",  # [cite: 38]
            "prompt": prompt,  # [cite: 38]
            "art_style": meshy_params.get("art_style", "realistic"),  # [cite: 38]
            "negative_prompt": meshy_params.get("negative_prompt", "low quality, low poly, ugly"),  # [cite: 38]
            "should_remesh": meshy_params.get("should_remesh", True),  # [cite: 38]
            "ai_model": meshy_params.get("ai_model", "meshy-4"),  # [cite: 38]
            "topology": meshy_params.get("topology", "triangle"),  # [cite: 38]
            "target_polycount": meshy_params.get("target_polycount", 30000),  # [cite: 38]
            "symmetry_mode": meshy_params.get("symmetry_mode", "auto")  # [cite: 38]
        }
        print(f"AI Task (TextTo3D - Preview): Calling Meshy Create Task with payload: {preview_payload}")
        preview_response = requests.post(MESHY_TEXT_TO_3D_ENDPOINT, headers=headers, json=preview_payload, timeout=30)
        preview_response.raise_for_status()
        preview_task_id_from_api = preview_response.json().get("result")  # [cite: 38]
        if not preview_task_id_from_api:
            raise Exception(f"Meshy Preview Task creation failed. Response: {preview_response.json()}")

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            external_ai_preview_task_id=preview_task_id_from_api)
        print(f"AI Task (TextTo3D - Preview): Meshy Preview Task created. ID: {preview_task_id_from_api}")

        preview_task_data = poll_meshy_task_status(
            MESHY_TEXT_TO_3D_ENDPOINT,
            preview_task_id_from_api,
            headers,
            ai_generation_record_id,
            stream_endpoint=True  # Text-to-3D API v2 支持 /stream [cite: 42]
        )
        # 预览成功后，更新状态
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.AI_API_PREVIEW_SUCCEEDED, meshy_result_data=preview_task_data)
        print(f"AI Task (TextTo3D - Preview): Meshy Preview Task {preview_task_id_from_api} SUCCEEDED.")
        # 预览模型URL (可选，如果需要保存预览模型)
        # preview_model_url_glb = preview_task_data.get("model_urls", {}).get("glb")

        # --- 阶段2: 创建并轮询精细化任务 ---
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.AI_API_REFINING,
            task_type=AIGenerationTaskModel.AITaskType.TEXT_TO_3D_REFINE)

        refine_payload = {
            "mode": "refine",  # [cite: 39]
            "preview_task_id": preview_task_id_from_api,  # [cite: 39]
            "enable_pbr": meshy_params.get("enable_pbr", True),  # [cite: 39]
            "texture_prompt": meshy_params.get("texture_prompt", prompt)  # [cite: 39]
            # "texture_image_url": meshy_params.get("texture_image_url") # 如果前端提供，且ai_model是meshy-4 [cite: 39]
        }
        # 根据文档，当art_style为sculpture时，enable_pbr应为false [cite: 38]
        if preview_payload.get("art_style") == "sculpture":
            refine_payload["enable_pbr"] = False
        # enable_pbr=true 和 texture_image_url 仅支持 ai_model为meshy-4 [cite: 39]
        if preview_payload.get("ai_model") != "meshy-4":
            if refine_payload.get("enable_pbr"):
                print(
                    f"AI Task (TextTo3D - Refine) Warning: enable_pbr=true not supported for {preview_payload.get('ai_model')}, setting to false.")
                refine_payload["enable_pbr"] = False
            if refine_payload.get("texture_image_url"):
                print(
                    f"AI Task (TextTo3D - Refine) Warning: texture_image_url not supported for {preview_payload.get('ai_model')}, removing.")
                del refine_payload["texture_image_url"]

        print(f"AI Task (TextTo3D - Refine): Calling Meshy Create Task with payload: {refine_payload}")
        refine_response = requests.post(MESHY_TEXT_TO_3D_ENDPOINT, headers=headers, json=refine_payload, timeout=30)
        refine_response.raise_for_status()
        refined_task_id_from_api = refine_response.json().get("result")  # [cite: 39]
        if not refined_task_id_from_api:
            raise Exception(f"Meshy Refine Task creation failed. Response: {refine_response.json()}")

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            external_ai_task_id=refined_task_id_from_api)  # 存储精细化任务ID
        print(f"AI Task (TextTo3D - Refine): Meshy Refine Task created. ID: {refined_task_id_from_api}")

        refined_task_data = poll_meshy_task_status(
            MESHY_TEXT_TO_3D_ENDPOINT,
            refined_task_id_from_api,
            headers,
            ai_generation_record_id,
            stream_endpoint=True  # Text-to-3D API v2 支持 /stream
        )

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.AI_API_SUCCEEDED, meshy_result_data=refined_task_data)

        generated_model_download_url = refined_task_data.get("model_urls", {}).get("glb")  # [cite: 40]
        if not generated_model_download_url:
            raise Exception(f"Meshy Refine Task {refined_task_id_from_api} SUCCEEDED but no GLB model URL found.")
        print(f"AI Task (TextTo3D - Refine): Meshy Refine Task SUCCEEDED. GLB URL: {generated_model_download_url}")

        # --- 后续步骤：下载模型、上传到自己OSS、创建Asset记录、触发Blender缩略图 ---
        # 这部分与 generate_3d_model_from_image_via_meshy_task 中的逻辑非常相似
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.DOWNLOADING_ASSET)

        model_file_ext = '.glb'
        original_model_filename = f"ai_meshy_text3d_{refined_task_id_from_api}{model_file_ext}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=model_file_ext) as tmp_model_file:
            temp_downloaded_3d_model_path = tmp_model_file.name

        model_response = requests.get(generated_model_download_url, stream=True, timeout=300)
        model_response.raise_for_status()
        with open(temp_downloaded_3d_model_path, 'wb') as f:
            for chunk in model_response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"AI Task (TextTo3D): Generated refined 3D model downloaded to {temp_downloaded_3d_model_path}")

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.UPLOADING_TO_OSS)

        generated_3d_model_oss_key = f"generated_assets/{user_id}/{uuid.uuid4()}/{original_model_filename}"
        oss_auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        oss_bucket_endpoint = f"https://{settings.OSS_ENDPOINT}"
        oss_bucket = oss2.Bucket(oss_auth, oss_bucket_endpoint, settings.OSS_BUCKET_NAME)
        oss_bucket.put_object_from_file(generated_3d_model_oss_key, temp_downloaded_3d_model_path)
        generated_model_oss_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{generated_3d_model_oss_key}"
        print(f"AI Task (TextTo3D): Uploaded refined 3D model to OSS key: {generated_3d_model_oss_key}")

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.CREATING_ASSET_RECORD)

        newly_created_asset_instance = AssetModel.objects.create(
            name=asset_name,
            description=asset_description,
            file_url=generated_model_oss_url,
            asset_type=AssetModel.AssetType.MODEL_3D,
            user=user,
            source_type=AssetSource.AI_TEXT_TO_3D,  # 使用新的来源类型
            source_reference_input={'prompt': prompt, 'meshy_params': meshy_params,
                                    'preview_task_id': preview_task_id_from_api},
            external_ai_task_id=refined_task_id_from_api,
            ai_model_used=preview_payload.get("ai_model")
        )
        print(f"AI Task (TextTo3D): Created Asset record with ID: {newly_created_asset_instance.id}")

        if ai_task_record:
            AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
                generated_asset=newly_created_asset_instance,
                status=AIGenerationTaskModel.AITaskStatus.TRIGGERING_THUMBNAIL
            )

        generate_blender_thumbnail_task.delay(
            asset_id=str(newly_created_asset_instance.id),
            original_file_url_from_view=generated_model_oss_url,
            asset_type_key_str=newly_created_asset_instance.asset_type
        )
        print(
            f"AI Task (TextTo3D): Triggered Blender thumbnail generation for Asset ID: {newly_created_asset_instance.id}")

        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.COMPLETED)

    except requests.exceptions.HTTPError as e_http:
        error_message = f"HTTP error during Meshy Text-to-3D. PreviewTask: {preview_task_id_from_api}, RefineTask: {refined_task_id_from_api}. Error: {e_http}."
        if e_http.response is not None: error_message += f" Status: {e_http.response.status_code}. Body: {e_http.response.text[:500]}"
        print(error_message)
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.FAILED, error_message=error_message)
        if e_http.response is not None and e_http.response.status_code >= 500: self.retry(exc=e_http)
    except Exception as e_generic:
        error_message = f"Unexpected error in Text-to-3D Task. PreviewTask: {preview_task_id_from_api}, RefineTask: {refined_task_id_from_api}: {e_generic}"
        print(error_message)
        import traceback
        traceback.print_exc()
        if ai_task_record: AIGenerationTaskModel.objects.filter(id=ai_task_record.id).update(
            status=AIGenerationTaskModel.AITaskStatus.FAILED,
            error_message=error_message + "\n" + traceback.format_exc())
    finally:
        if temp_downloaded_3d_model_path and os.path.exists(temp_downloaded_3d_model_path):
            try:
                os.remove(temp_downloaded_3d_model_path)
            except Exception as e_clean:
                print(f"AI Task (TextTo3D): Error cleaning up temp model {temp_downloaded_3d_model_path}: {e_clean}")