import os
import sys
import subprocess
import csv
import time
import glob  # <---【修改1】补充这个库，因为你后面用到了 glob.glob

class AVSeparationPipeline:
    def __init__(self, base_data_dir="data"):
        # 你的项目根目录 (假设 data 和 scripts 都在这个根目录下)
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_data_dir = os.path.join(self.project_root, "data")
        
        # 脚本所在的绝对路径
        self.scripts_dir = "/root/autodl-tmp/iQuery-2/code/scripts"

        # ---【修改2】添加下面这一行 ---
        # sys.executable 会自动获取当前运行环境的 python 路径
        self.python_path = sys.executable

    def process_pair(self, video_paths):
        """
        主流程: 
        1. 接收上传的两个视频路径
        2. 手动创建 motion 和 detection 的分类目录 (新增步骤)
        3. 调用提取脚本
        4. 生成 CSV
        5. 调用模型
        """
        print(f"--- [Step 1] 收到视频，准备调用预处理脚本 ---")
        
        # --- [Step 1.5] 关键修改：手动创建分类文件夹 ---
        # 你的 extract_motion.py 需要目录已经存在才能写入
        print(f"--- [Step 1.5] 预先创建 Motion/Detection 分类目录 ---")
        
        for v_path in video_paths:
            # v_path 例如: .../data/uploads/20251226_205436_0/video.mp4
            
            # 1. 提取文件夹名 -> "20251226_205436_0"
            batch_folder_name = os.path.basename(os.path.dirname(v_path))
            
            # 2. 构造 motion_features 下的目标路径
            # 结果: .../data/motion_features/20251226_205436_0
            motion_target_dir = os.path.join(self.base_data_dir, "motion_features", batch_folder_name)
            os.makedirs(motion_target_dir, exist_ok=True)
            
            # 3. (建议) 顺便把 detection_results 的目录也创建了
            # 结果: .../data/detection_results/20251226_205436_0
            detect_target_dir = os.path.join(self.base_data_dir, "detection_results", batch_folder_name)
            os.makedirs(detect_target_dir, exist_ok=True)
            
            print(f"    √ 已创建目录: {batch_folder_name}")

        # --- [Step 2] 依次调用脚本 ---
        self._run_script_no_args("extract_frames.py")
        self._run_script_no_args("extract_audio.py")
        
        # 此时文件夹已创建好，脚本可以放心写入了
        self._run_script_no_args("extract_motion.py") 
        self._run_script_no_args("object_detect.py")

        print(f"--- [Step 3] 预处理脚本执行完毕，开始生成 CSV ---")

        # --- [Step 3] 搜集信息 ---
        csv_infos = []
        for v_path in video_paths:
            info = self._get_generated_file_info(v_path)
            if info:
                csv_infos.append(info)
            else:
                print(f"⚠️ 警告: 无法找到视频 {v_path} 的处理结果")

        # --- [Step 4] 写入 CSV ---
        csv_output_dir = os.path.join(self.base_data_dir, "csv_files")
        os.makedirs(csv_output_dir, exist_ok=True)
        
        self._generate_csv_files(csv_infos, csv_output_dir)

        # --- [Step 5] 启动模型 ---
        print(f"--- [Step 5] 启动模型推理 ---")
        self._run_script_no_args("evaluate.sh", is_shell=True)
        
        return {
            "status": "done",
            "csv_dir": csv_output_dir
        }

    # =========================================================
    #  核心逻辑：路径推断与帧数统计
    # =========================================================
    def _get_generated_file_info(self, original_video_path):
        """
        根据上传文件的路径，推断出音频和帧的路径，并统计帧数。
        """
        # 1. 解析路径结构
        # 假设 original_video_path = .../uploads/20251226_205436_0/0VyVd_QUCl8.mp4
        
        # 获取父文件夹名 -> "20251226_205436_0"
        upload_dir = os.path.dirname(original_video_path)
        batch_folder_name = os.path.basename(upload_dir)
        
        # 获取文件名 -> "0VyVd_QUCl8.mp4"
        filename = os.path.basename(original_video_path)
        # 获取文件名主体 -> "0VyVd_QUCl8"
        base_name = os.path.splitext(filename)[0]

        # 2. 构造物理路径 (用于 Python 去读取文件)
        # 帧目录: data/frames/20251226_205436_0/0VyVd_QUCl8.mp4/
        real_frame_dir = os.path.join(self.base_data_dir, "frames", batch_folder_name, filename)
        
        # 音频文件: data/audio/20251226_205436_0/0VyVd_QUCl8.wav
        real_audio_file = os.path.join(self.base_data_dir, "audio", batch_folder_name, f"{base_name}.wav")

        # 3. 统计帧数 (读取 jpg 文件数量)
        if not os.path.exists(real_frame_dir):
            print(f"❌ 错误: 找不到帧目录 {real_frame_dir}")
            return None
            
        # 统计 jpg 数量
        jpg_files = glob.glob(os.path.join(real_frame_dir, "*.jpg"))
        frame_count = len(jpg_files)
        
        if frame_count == 0:
            print(f"⚠️ 警告: 目录 {real_frame_dir} 下没有图片")

        # 4. 构造 CSV 需要的相对路径字符串 (严格按照你的要求)
        # 格式: /20251226_205436_0/0VyVd_QUCl8.wav
        
        # 注意：这里我们手动拼接 /，确保生成的是 Linux 风格路径
        csv_audio_path = f"/{batch_folder_name}/{base_name}.wav"
        csv_frame_path = f"/{batch_folder_name}/{filename}" # 注意这里你的csv要求带.mp4后缀

        print(f"✅ 解析成功: {filename} -> {frame_count} 帧")

        return {
            "audio_str": csv_audio_path,
            "frame_str": csv_frame_path,
            "count": frame_count
        }

    # =========================================================
    #  CSV 生成逻辑
    # =========================================================
    def _generate_csv_files(self, infos, output_dir):
        """
        生成 test.csv 和 testsep.csv
        """
        if not infos or len(infos) < 2:
            print("❌ 错误: 有效文件信息不足 2 个，无法生成 CSV")
            return

        test_csv_path = os.path.join(output_dir, "test.csv")
        testsep_csv_path = os.path.join(output_dir, "testsep.csv")

        # --- 1. 生成 test.csv ---
        # 格式: /路径/音频.wav,/路径/视频.mp4,帧数
        with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
            # 使用 writer 自动处理逗号分隔
            # 但你的格式非常简单，也可以直接 write 字符串来确保完全可控
            for info in infos:
                # 拼接行: /.../a.wav,/.../a.mp4,147
                line = f"{info['audio_str']},{info['frame_str']},{info['count']}\n"
                f.write(line)
        
        print(f"📄 已生成 test.csv: {test_csv_path}")

        # --- 2. 生成 testsep.csv ---
        # 格式: /路径/音频1.wav, /路径/音频2.wav (注意中间有个空格)
        with open(testsep_csv_path, 'w', newline='', encoding='utf-8') as f:
            # 取前两个信息
            audio1 = infos[0]['audio_str']
            audio2 = infos[1]['audio_str']
            
            # 按照你给的例子，中间加个空格: "path1, path2"
            line = f"{audio1}, {audio2}\n"
            f.write(line)
            
        print(f"📄 已生成 testsep.csv: {testsep_csv_path}")

    # =========================================================
    #  工具：调用脚本 (已修复路径问题)
    # =========================================================
    def _run_script_no_args(self, script_name, is_shell=False):
        # 1. 默认设置：在 scripts 目录下运行
        run_cwd = self.scripts_dir
        script_exe_path = script_name # 相对路径
        
        # 2. 特殊处理 run_model.sh
        # 因为 main_music.py 在 code/ 目录下，而不在 scripts/ 目录下
        # 所以我们需要在 code/ 目录下运行这个 shell 脚本
        if script_name == "evaluate.sh":
            # 获取 code 目录 (即 scripts 的上一级)
            # /root/.../iQuery-2/code
            code_dir = os.path.dirname(self.scripts_dir) 
            
            run_cwd = code_dir
            # 在 code 目录下调用 scripts/run_model.sh
            script_exe_path = os.path.join("scripts", script_name)
            
            print(f"🔄 切换运行目录到: {run_cwd}")

        # 3. 构建命令
        if is_shell:
            cmd = ["bash", script_exe_path]
        else:
            # 其他 python 脚本 (extract_*.py) 还是在 scripts 目录下运行
            # 必须用绝对路径或相对当前cwd的路径
            if run_cwd == self.scripts_dir:
                 cmd = [self.python_path, script_name]
            else:
                 # 如果cwd变了，这里要指明脚本在哪里
                 cmd = [self.python_path, os.path.join("scripts", script_name)]
        
        print(f">>> 正在运行: {cmd} (在 {run_cwd} 下) ...")
        
        try:
            subprocess.run(
                cmd, 
                cwd=run_cwd, # <--- 关键点：这里决定了脚本运行时的“当前位置”
                check=True,
                capture_output=True, 
                text=True
            )
            print(f"    √ 完成")
        except subprocess.CalledProcessError as e:
            print(f"!!! {script_name} 运行失败 !!!")
            print(f"Stderr: {e.stderr}")
            print(f"Stdout: {e.stdout}")
            # 如果是模型推理失败，建议抛出异常，不要假装成功
            raise e