import os
import shutil
import re

# 配置：三个大的目录路径
large_dirs = [
    "/home/fdse/agent-bugs/auto-code-rover/results-claude-1",
    "/home/fdse/agent-bugs/auto-code-rover/results-claude-2",
    "/home/fdse/agent-bugs/auto-code-rover/results-claude-3",
    "/home/fdse/agent-bugs/auto-code-rover/results-claude-4",
    "/home/fdse/agent-bugs/auto-code-rover/results-claude-5"
]

# 用于保存整理后的结果
output_base_dir = "/home/fdse/agent-bugs/auto-code-rover/ALLPatches-claude"  # 可以与 large_dirs 平级或自定义

# 匹配像 autogen__autogen-1174_2025-... 或 crewAI__crewAI-1323_2025-... 的 issue ID
issue_pattern = re.compile(r"^[^_]+__([a-zA-Z0-9_.-]+-\d+)_")

for large_dir in large_dirs:
    for subdir_name in os.listdir(large_dir):
        subdir_path = os.path.join(large_dir, subdir_name)
        if os.path.isdir(subdir_path):
            match = issue_pattern.match(subdir_name)
            if match:
                issue_id = match.group(1)  # 提取出像 autogen-1174、crewAI-1323 这样的名字
                issue_output_dir = os.path.join(output_base_dir, issue_id)
                os.makedirs(issue_output_dir, exist_ok=True)

                for root, _, files in os.walk(subdir_path):
                    for file in files:
                        if file.endswith(".diff"):
                            source_file = os.path.join(root, file)
                            # 避免重名，加上前缀
                            new_file_name = f"{subdir_name}__{file}"
                            dest_file = os.path.join(issue_output_dir, new_file_name)
                            shutil.copy2(source_file, dest_file)
                            print(f"Copied: {source_file} -> {dest_file}")