# main/blender_scripts/render_thumbnail.py
import bpy
import sys
import os
import math
import mathutils  # 确保导入mathutils


def render_model_thumbnail(model_path, output_image_path, width=200, height=200):
    try:
        print(f"Blender script: Starting render for {model_path}")

        # --- 根据文件类型加载模型 ---
        file_ext = os.path.splitext(model_path)[1].lower()

        if file_ext == '.blend':
            # 对于.blend文件，直接打开它。这会替换当前场景。
            try:
                bpy.ops.wm.open_mainfile(filepath=model_path)
                print(f"Blender script: Opened .blend file: {model_path}")
            except RuntimeError as e:
                print(f"Blender script: Error opening .blend file '{model_path}': {e}")
                return False
        else:
            # 对于其他类型的文件 (GLB, FBX, OBJ)，先清空当前场景再导入
            bpy.ops.object.select_all(action='SELECT')
            # 检查是否有可选中的对象，避免在空场景中调用delete报错
            if bpy.context.selected_objects:
                bpy.ops.object.delete()
            print(f"Blender script: Cleared default scene for import.")

            if file_ext == '.glb' or file_ext == '.gltf':
                bpy.ops.import_scene.gltf(filepath=model_path)
                print(f"Blender script: Imported GLTF/GLB: {model_path}")
            elif file_ext == '.fbx':
                bpy.ops.import_scene.fbx(filepath=model_path)
                print(f"Blender script: Imported FBX: {model_path}")
            elif file_ext == '.obj':
                bpy.ops.import_scene.obj(filepath=model_path, use_edges=True, use_smooth_groups=True, split_mode='OFF')
                print(f"Blender script: Imported OBJ: {model_path}")
            else:
                print(f"Blender script: Unsupported model format: {file_ext}")
                return False

        # --- 场景和渲染设置 ---
        scene = bpy.context.scene
        if not scene:  # 如果打开的.blend文件没有场景，或者场景获取失败
            print(f"Blender script: Could not get current scene after loading/importing {model_path}")
            return False

        # 强制使用Eevee以加快渲染速度，并设置输出参数
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        scene.render.image_settings.file_format = 'JPEG'
        scene.render.image_settings.color_mode = 'RGB'
        scene.render.film_transparent = True  # 背景透明
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100

        # Eevee特定设置 (如果需要)
        # scene.eevee.taa_render_samples = 16 # 调整渲染采样数

        # --- 相机设置 ---
        # 尝试找到或创建一个名为 "ThumbnailCamera_Auto" 的相机
        cam_name = "ThumbnailCamera_Auto"
        cam_obj = scene.objects.get(cam_name)
        if not cam_obj or cam_obj.type != 'CAMERA':
            # 如果找不到或类型不对，删除同名非相机对象（如果有的话）
            if cam_obj:
                bpy.data.objects.remove(cam_obj, do_unlink=True)
            cam_data = bpy.data.cameras.new(cam_name)
            cam_obj = bpy.data.objects.new(cam_name, cam_data)
            scene.collection.objects.link(cam_obj)  # 将相机链接到场景的主集合
        scene.camera = cam_obj  # 设置为活动相机

        # --- 自动聚焦和定位相机 ---
        # 收集场景中所有可见的网格对象用于计算边界
        visible_mesh_objects = [obj for obj in scene.objects if
                                obj.type == 'MESH' and obj.visible_get(view_layer=bpy.context.view_layer)]

        if not visible_mesh_objects:
            print("Blender script: No visible mesh objects found in the scene to focus on.")
            # 可以考虑一个默认的回退渲染（比如渲染一个空场景或特定标记）
            # 或者直接返回False，让Celery任务知道没有生成有效缩略图
            return False  # 没有可聚焦的对象，渲染可能无意义

        # 计算所有可见网格对象的整体边界框
        min_coord = [float('inf')] * 3
        max_coord = [float('-inf')] * 3
        has_valid_bounds = False

        for obj in visible_mesh_objects:
            # 确保对象数据存在且有顶点
            if not obj.data or not hasattr(obj.data, 'vertices') or not obj.data.vertices:
                continue

            obj_mat = obj.matrix_world
            # obj.bound_box 是对象的局部边界框的8个角点
            for corner_local in obj.bound_box:
                world_coord = obj_mat @ mathutils.Vector(corner_local)  # 使用 mathutils.Vector
                for i in range(3):
                    min_coord[i] = min(min_coord[i], world_coord[i])
                    max_coord[i] = max(max_coord[i], world_coord[i])
                has_valid_bounds = True

        if not has_valid_bounds:
            print("Blender script: Could not determine a valid bounding box for visible mesh objects.")
            return False

        # 计算边界框中心和最大尺寸
        center = mathutils.Vector([(min_coord[i] + max_coord[i]) / 2 for i in range(3)])
        size = max(max_coord[i] - min_coord[i] for i in range(3))
        if size == 0: size = 1.0  # 避免尺寸为0导致的问题

        # 相机定位：这是一个经验值，需要针对您的模型类型和期望效果进行大量调整
        # 目标是让相机能看到整个模型，并保持一定距离
        # 这里的(1, -1, 0.7)是方向因子，size是距离因子
        cam_distance_factor = 1.8  # 调整这个值来控制相机远近
        cam_obj.location = center + mathutils.Vector(
            (size * cam_distance_factor, -size * cam_distance_factor, size * (cam_distance_factor * 0.6)))

        # 相机指向模型中心
        direction = center - cam_obj.location
        # track_axis通常是相机的"后方"轴，up_axis是相机的"上方"轴
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam_obj.rotation_euler = rot_quat.to_euler()

        # 设置相机参数
        cam_obj.data.type = 'PERSP'  # 透视相机
        cam_obj.data.lens = 50  # 焦距 (mm)，常用值
        # 调整剪切平面以确保模型完整可见
        cam_obj.data.clip_start = max(0.01, size / 100.0)  # 避免裁剪太近的物体
        cam_obj.data.clip_end = max(cam_obj.data.clip_start * 100, size * 10.0)  # 确保远平面足够远

        # --- 灯光设置 ---
        # 尝试找到或创建一个名为 "ThumbnailLight_Auto" 的太阳灯
        light_name = "ThumbnailLight_Auto_Sun"
        light_obj = scene.objects.get(light_name)
        if not light_obj or light_obj.type != 'LIGHT' or light_obj.data.type != 'SUN':
            if light_obj:  # 如果存在同名但类型不对的对象，先移除
                bpy.data.objects.remove(light_obj, do_unlink=True)
            light_data = bpy.data.lights.new(name=light_name, type='SUN')
            light_data.energy = 3.0  # 太阳光的强度
            light_data.angle = 0.1  # 太阳光角度，影响阴影柔和度
            light_obj = bpy.data.objects.new(name=light_name, object_data=light_data)
            scene.collection.objects.link(light_obj)

        # 太阳灯的方向：通常与相机方向相关联，或从一个经典的角度照射
        # 例如，让太阳光从相机的左上后方照射过来
        light_obj.rotation_euler = cam_obj.rotation_euler
        light_obj.rotation_euler.x += math.radians(-15)  # 向上偏15度
        light_obj.rotation_euler.y += math.radians(15)  # 向右偏15度

        # --- 渲染并保存 ---
        scene.render.filepath = output_image_path
        print(f"Blender script: Attempting to render to {output_image_path} using engine {scene.render.engine}")
        bpy.ops.render.render(write_still=True)

        if os.path.exists(output_image_path) and os.path.getsize(output_image_path) > 0:
            print(f"Blender script: Rendered image successfully saved to {output_image_path}")
            return True
        else:
            print(
                f"Blender script: Rendered image file not found or empty at {output_image_path}. Rendering might have failed silently.")
            return False

    except Exception as e:
        print(f"Blender script: An error occurred in render_model_thumbnail - {str(e)}")
        import traceback
        traceback.print_exc()  # 打印完整的Python异常堆栈
        return False


if __name__ == "__main__":
    argv = sys.argv
    model_path_arg = None
    output_image_path_arg = None

    try:
        # 命令行参数应该在 '--' 之后
        args_after_script = argv[argv.index("--") + 1:]
        if len(args_after_script) < 2:
            raise ValueError("Not enough arguments provided for model path and output path.")

        model_path_arg = args_after_script[0]
        output_image_path_arg = args_after_script[1]

        render_width_arg = int(args_after_script[2]) if len(args_after_script) > 2 else 200
        render_height_arg = int(args_after_script[3]) if len(args_after_script) > 3 else 200

    except ValueError as e:
        print(f"Blender script: Error parsing arguments: {e}")
        print(
            "Blender script: Usage: blender -b -P render_thumbnail.py -- <model_input_path> <image_output_path> [width] [height]")
        sys.exit(1)  # 错误退出

    if not os.path.exists(model_path_arg):
        print(f"Blender script: Error - Input model file does not exist: {model_path_arg}")
        sys.exit(1)

    print(
        f"Blender script: Received args: model='{model_path_arg}', output='{output_image_path_arg}', width={render_width_arg}, height={render_height_arg}")

    success = render_model_thumbnail(model_path_arg, output_image_path_arg, render_width_arg, render_height_arg)

    if not success:
        print("Blender script: render_model_thumbnail function returned False.")
        sys.exit(1)  # 错误退出

    print("Blender script: Exiting successfully.")
    sys.exit(0)  # 成功退出