import sys
from importlib.metadata import version, PackageNotFoundError

print("Python 路径：", sys.executable)
print("Python 版本：", sys.version)

for package in ["openai", "python-dotenv", "sentence-transformers"]:
    try:
        print(f"{package}=={version(package)}")
    except PackageNotFoundError:
        print(f"{package}：当前解释器中未找到")