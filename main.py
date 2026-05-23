"""AstrBot 入口兼容文件。

AstrBot 通常会从插件根目录的 ``main.py`` 加载插件；实际实现放在
``astrbot_plugin_xutheringwavesuid`` 包内，方便与原早柚核心版本代码隔离。
"""

import sys
from pathlib import Path

# AstrBot 的 Git 插件加载器有些版本会直接按文件路径执行 main.py，
# 此时插件根目录不一定在 sys.path，导致同级包导入失败。
PLUGIN_ROOT = Path(__file__).resolve().parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from astrbot_plugin_xutheringwavesuid.main import XutheringWavesUIDAstrBot

__all__ = ["XutheringWavesUIDAstrBot"]
