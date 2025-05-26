#!/bin/bash

# 创建目标目录
mkdir -p merged_results/Patches
mkdir -p merged_results/swe-bench-lite

# 合并 Patches 目录
for i in {1..5}; do
    if [ -d "results-claude${i}/Patches" ]; then
        echo "Processing Patches from results-claude${i}"
        # 遍历所有项目目录
        for project_dir in results-claude${i}/Patches/*; do
            if [ -d "$project_dir" ]; then
                project_name=$(basename "$project_dir")
                # 遍历项目下的所有issue目录
                for issue_dir in "$project_dir"/*; do
                    if [ -d "$issue_dir" ]; then
                        issue_name=$(basename "$issue_dir")
                        # 创建对应的目标目录
                        mkdir -p "merged_results/Patches/$project_name/$issue_name"
                        # 复制所有patch文件
                        cp "$issue_dir"/*.patch "merged_results/Patches/$project_name/$issue_name/"
                    fi
                done
            fi
        done
    fi
done

# 合并 swe-bench-lite 目录
for i in {1..5}; do
    if [ -d "results-claude${i}/swe-bench-lite" ]; then
        echo "Processing swe-bench-lite from results-claude${i}"
        cp -r "results-claude${i}/swe-bench-lite/"* "merged_results/swe-bench-lite/"
    fi
done

echo "合并完成！结果保存在 merged_results 目录中" 