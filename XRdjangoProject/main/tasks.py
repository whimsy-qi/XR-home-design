# main/tasks.py
import os
import subprocess
import tempfile
import uuid
from urllib.parse import urlparse

from celery import shared_task
from PIL import Image, UnidentifiedImageError  # Pillow库
from django.conf import settings  # 用于访问项目配置
from django.apps import apps  # 用于动态获取模型
import requests  # 用于从URL下载文件
import oss2  # 阿里云OSS SDK

# --- Blender 相关配置 ---
# ！！！请根据您的实际Blender安装路径进行修改！！！
# 如果Blender已加入系统PATH，可以直接写 "blender"
# 在Windows上，如果路径含空格，建议使用r""原始字符串，例如: r"C:\Program Files\Blender Foundation\Blender 3.x\blender.exe"
BLENDER_EXECUTABLE_PATH = "/opt/blender/blender" # 【修改】
# 例如，如果您的Blender不在系统PATH中:
# BLENDER_EXECUTABLE_PATH = r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"

# ！！！请确认您的render_thumbnail.py脚本的准确路径！！！
# settings.BASE_DIR 通常指向您Django项目的根目录
BLENDER_SCRIPT_PATH = os.path.join(settings.BASE_DIR, 'main', 'blender_scripts', 'render_thumbnail.py')


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_thumbnail_task(self, asset_id, original_file_url_from_view, asset_type_key_str):
    Asset = apps.get_model('main', 'Asset')  #动态获取Asset模型
    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        print(f"Task Error: Asset with ID {asset_id} not found.")
        return

    print(
        f"Task Started: Generate thumbnail for Asset ID: {asset_id}, Base URL: {original_file_url_from_view}, AssetType: {asset_type_key_str}")

    temp_downloaded_file_path = None  #下载的原始文件的临时路径
    temp_output_thumbnail_path = None  #的临时路径
    new_thumbnail_url = None  #最终上传到OSS的缩略图URL

    try:

        parsed_url = urlparse(original_file_url_from_view)
        object_key_for_download = parsed_url.path.lstrip('/')

        original_filename_from_key = os.path.basename(object_key_for_download)
        _, file_extension = os.path.splitext(original_filename_from_key)
        file_extension = file_extension.lower()

        print(f"Task: Extracted Object Key: '{object_key_for_download}' with extension '{file_extension}'")

        #为下载操作生成临时的预签名GET URL
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        bucket_endpoint_with_protocol = f"https://{settings.OSS_ENDPOINT}"
        bucket = oss2.Bucket(auth, bucket_endpoint_with_protocol, settings.OSS_BUCKET_NAME)

        signed_download_url = bucket.sign_url('GET', object_key_for_download, expires=900)
        print(f"Task: Generated signed GET URL for download: {signed_download_url}")


        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            temp_downloaded_file_path = tmp_file.name

        response = requests.get(signed_download_url, stream=True, timeout=60)
        response.raise_for_status()

        with open(temp_downloaded_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(
            f"Task: Original file for Asset ID {asset_id} (key: {object_key_for_download}) downloaded to {temp_downloaded_file_path}")


        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        model_extensions = ['.fbx', '.glb', '.gltf', '.obj','.blend']
        output_thumbnail_format = 'jpeg'

        if file_extension in image_extensions:
            print(f"Task: Processing Asset ID {asset_id} as an image file.")
            thumbnail_size = (200, 200)

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_thumbnail_format}") as tmp_thumb_img_file:
                temp_output_thumbnail_path = tmp_thumb_img_file.name

            with Image.open(temp_downloaded_file_path) as img:
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA')
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                img.save(temp_output_thumbnail_path, format=output_thumbnail_format.upper(), quality=85)
            print(f"Task: Image thumbnail for Asset ID {asset_id} generated at {temp_output_thumbnail_path}")

        elif file_extension in model_extensions:
            print(
                f"Task: Processing Asset ID {asset_id} as a 3D model file using Blender ({temp_downloaded_file_path}).")

            with tempfile.NamedTemporaryFile(delete=False,
                                             suffix=f".{output_thumbnail_format}") as tmp_thumb_model_file:
                temp_output_thumbnail_path = tmp_thumb_model_file.name

            cmd = [
                BLENDER_EXECUTABLE_PATH, '-b', '-P', BLENDER_SCRIPT_PATH,
                '--',
                temp_downloaded_file_path, temp_output_thumbnail_path, '200', '200'
            ]
            print(f"Task: Executing Blender command: {' '.join(cmd)}")

            try:
                # 以二进制模式捕获输出，避免直接在subprocess.run中解码导致错误
                process = subprocess.run(cmd, capture_output=True, check=False, timeout=300)
                stdout_str = ""
                stderr_str = ""
                # 尝试用UTF-8解码，如果失败则用GBK，并替换无法解码的字符
                if process.stdout:
                    try:
                        stdout_str = process.stdout.decode('utf-8')
                    except UnicodeDecodeError:
                        print(
                            f"Task Warning: Blender stdout for Asset ID {asset_id} could not be decoded as UTF-8, trying GBK with replace.")
                        stdout_str = process.stdout.decode('gbk', errors='replace')

                if process.stderr:
                    try:
                        stderr_str = process.stderr.decode('utf-8')
                    except UnicodeDecodeError:
                        print(
                            f"Task Warning: Blender stderr for Asset ID {asset_id} could not be decoded as UTF-8, trying GBK with replace.")
                        stderr_str = process.stderr.decode('gbk', errors='replace')

                print(f"Task: Blender stdout for Asset ID {asset_id}:\n{stdout_str}")
                if stderr_str:  # 只在stderr_str有内容时打印
                    print(f"Task: Blender stderr for Asset ID {asset_id}:\n{stderr_str}")

                # 判断Blender是否成功的主要依据：返回码 和 期望的输出文件是否生成且有效
                if process.returncode == 0 and os.path.exists(temp_output_thumbnail_path) and os.path.getsize(
                        temp_output_thumbnail_path) > 0:
                    print(
                        f"Task: Blender rendering successful for Asset ID {asset_id}. Thumbnail at {temp_output_thumbnail_path}")
                else:
                    print(
                        f"Task: Blender rendering failed for Asset ID {asset_id}. Return code: {process.returncode}. Output file valid: {os.path.exists(temp_output_thumbnail_path) and os.path.getsize(temp_output_thumbnail_path) > 0 if temp_output_thumbnail_path else False}")
                    # 如果Blender脚本自身打印了错误（例如 "Blender script: An error occurred..."），即使返回码是0，也可能没有生成有效图片
                    # 额外的检查：如果stdout_str或stderr_str包含Blender脚本内部的错误提示，也可以认为失败
                    if "Blender script: An error occurred" in stdout_str or "Blender script: An error occurred" in stderr_str:
                        print(f"Task: Blender script reported an internal error for Asset ID {asset_id}.")
                    temp_output_thumbnail_path = None  # 标记渲染失败
            # ... (except FileNotFoundError, except Exception as e_blender) ...
            except subprocess.TimeoutExpired:
                print(f"Task Error: Blender rendering process timed out for Asset ID {asset_id}.")
                temp_output_thumbnail_path = None
            except FileNotFoundError:  # 特别捕捉Blender可执行文件找不到的错误
                print(
                    f"CRITICAL TASK ERROR: Blender executable not found at '{BLENDER_EXECUTABLE_PATH}'. Please check configuration. Asset ID: {asset_id}")
                temp_output_thumbnail_path = None  # 标记失败
            except Exception as e_blender:  # 其他Blender执行期间的错误
                print(f"Task Error: Exception during Blender execution for Asset ID {asset_id}: {e_blender}")
                temp_output_thumbnail_path = None  # 标记失败

        else:  # 文件类型既不是图片也不是支持的模型
            print(f"Task: Asset ID {asset_id}: Unsupported file type '{file_extension}' for any thumbnail generation.")
            # temp_output_thumbnail_path 此时应为 None

        # --- 3. 如果成功生成了缩略图图片 (无论是Pillow还是Blender) ---
        # bucket 对象已经从上面为GET操作签名URL时初始化了，理论上可以复用
        # 但为确保独立性，可以重新初始化，或者确信之前的 bucket 实例仍然可用且配置正确
        # auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        # bucket_endpoint_with_protocol = f"https://{settings.OSS_ENDPOINT}"
        # bucket = oss2.Bucket(auth, bucket_endpoint_with_protocol, settings.OSS_BUCKET_NAME)

        if temp_output_thumbnail_path and os.path.exists(temp_output_thumbnail_path) and os.path.getsize(
                temp_output_thumbnail_path) > 0:
            thumb_oss_key = f"thumbnail_uploads/{asset.user.id if asset.user else 'public'}/{asset.id}/{uuid.uuid4()}.{output_thumbnail_format}"
            bucket.put_object_from_file(thumb_oss_key, temp_output_thumbnail_path)
            new_thumbnail_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{thumb_oss_key}"
            print(f"Task: Generated thumbnail for Asset ID {asset_id} uploaded to OSS: {new_thumbnail_url}")
        else:
            print(
                f"Task: Thumbnail was not generated or process failed for Asset ID {asset_id}. No thumbnail uploaded.")
            # 如果没有生成有效的缩略图，则不设置 new_thumbnail_url（保持为None）

    except requests.exceptions.HTTPError as e:
        print(
            f"Task Critical Error: HTTP error downloading original file for Asset ID {asset_id} (URL: {signed_download_url if 'signed_download_url' in locals() else original_file_url_from_view}): {e}. Response: {e.response.status_code if e.response else 'No status code'}")
        # 4xx 错误通常不应重试，5xx可以
        if e.response is not None and e.response.status_code < 500 and e.response.status_code not in [408,
                                                                                                      429]:  # 408 Request Timeout, 429 Too Many Requests
            pass  # 不重试客户端错误 (如403, 404)，除非是可重试的特定状态
        else:
            self.retry(exc=e)  # 重试服务器错误或可重试的客户端错误
    except requests.exceptions.RequestException as e:  # 更广泛的网络相关错误
        print(
            f"Task Critical Error: Network-related error downloading original file for Asset ID {asset_id} (URL: {signed_download_url if 'signed_download_url' in locals() else original_file_url_from_view}): {e}")
        self.retry(exc=e)
    except UnidentifiedImageError as e:
        print(
            f"Task Error: Pillow could not identify image file for Asset ID {asset_id}. File: {temp_downloaded_file_path if temp_downloaded_file_path else 'Not Downloaded'}. Error: {e}")
    except IOError as e:
        print(f"Task Error: Pillow I/O error processing image for Asset ID {asset_id}: {e}")
    except Exception as e:  # 捕获所有其他未知异常
        print(f"Task Error: An unexpected error occurred during thumbnail generation for Asset ID {asset_id}: {e}")
        import traceback
        traceback.print_exc()
        # self.retry(exc=e) # 对于某些未知错误，也可以考虑重试，但需谨慎
    finally:
        # 清理临时文件
        if temp_downloaded_file_path and os.path.exists(temp_downloaded_file_path):
            try:
                os.remove(temp_downloaded_file_path)
                print(f"Task: Cleaned up temporary downloaded file: {temp_downloaded_file_path}")
            except Exception as e_clean1:
                print(f"Task: Error cleaning up temporary downloaded file {temp_downloaded_file_path}: {e_clean1}")
        if temp_output_thumbnail_path and os.path.exists(temp_output_thumbnail_path):
            try:
                os.remove(temp_output_thumbnail_path)
                print(f"Task: Cleaned up temporary output thumbnail: {temp_output_thumbnail_path}")
            except Exception as e_clean2:
                print(f"Task: Error cleaning up temporary output thumbnail {temp_output_thumbnail_path}: {e_clean2}")

    # 移除协议头，只保留域名部分
    clean_oss_endpoint = settings.OSS_ENDPOINT.replace('https://', '').replace('http://', '')  # 【新增此行】

    # 构造最终的缩略图URL
    new_thumbnail_url = f"https://{settings.OSS_BUCKET_NAME}.{clean_oss_endpoint}/{thumb_oss_key}"  # 【修改此行】

    #根据是否有新的缩略图URL来更新数据库
    if new_thumbnail_url:
        asset.thumbnail_url = new_thumbnail_url
        asset.save(update_fields=['thumbnail_url'])
        print(f"Task Succeeded: Asset ID {asset_id} thumbnail_url updated to: {asset.thumbnail_url}")
    else:
        print(
            f"Task Completed (or failed to produce thumbnail): Asset ID {asset_id} thumbnail_url was not set or updated (remains: {asset.thumbnail_url}).")