#!/usr/bin/env python3
"""
批量替换项目中的日志导入
"""
import os
import re
from pathlib import Path

def replace_logging_imports(file_path: Path):
    """替换单个文件中的日志导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换 import logging
        content = re.sub(
            r'import logging\n',
            'from app.core.logging import get_logger\n',
            content
        )

        # 替换 logger = logging.getLogger(__name__)
        content = re.sub(
            r'logger = logging\.getLogger\(__name__\)',
            'logger = get_logger(__name__)',
            content
        )

        # 替换其他常见的logging调用
        content = re.sub(
            r'logging\.info\(',
            'logger.info(',
            content
        )
        content = re.sub(
            r'logging\.error\(',
            'logger.error(',
            content
        )
        content = re.sub(
            r'logging\.warning\(',
            'logger.warning(',
            content
        )
        content = re.sub(
            r'logging\.debug\(',
            'logger.debug(',
            content
        )

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Updated: {file_path}")

    except Exception as e:
        print(f"Error updating {file_path}: {e}")

def main():
    """主函数"""
    app_dir = Path("app")

    # 查找所有Python文件
    python_files = list(app_dir.rglob("*.py"))

    # 排除日志配置文件本身
    python_files = [f for f in python_files if "logging.py" not in str(f)]

    for file_path in python_files:
        replace_logging_imports(file_path)

    print(f"Updated {len(python_files)} files")

if __name__ == "__main__":
    main()