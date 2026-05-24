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

try:
    # 新版实现类名。
    from astrbot_plugin_xutheringwavesuid.main import (
        XutheringWavesUIDAstrBotBase as _XutheringWavesUIDImpl,
    )
except ImportError:
    # 兼容安装目录中子模块仍是旧实现类名的情况。
    from astrbot_plugin_xutheringwavesuid.main import (
        XutheringWavesUIDAstrBot as _XutheringWavesUIDImpl,
    )

try:
    from astrbot.api.star import register
except Exception:
    def register(*args, **kwargs):  # type: ignore
        def deco(cls):
            return cls

        return deco


@register(
    "XutheringWavesUID",
    "XutheringWavesUID contributors / Cline",
    "鸣潮 XutheringWavesUID 的 AstrBot 基础适配版",
    "1.0.0",
)
class XutheringWavesUIDAstrBot(_XutheringWavesUIDImpl):
    """AstrBot 根入口注册类。

    AstrBot v4.24 会扫描根模块中被 register 标记的类；如果只从子模块
    re-export，部分类扫描逻辑拿不到 classes，导致 classes[0] 越界。
    """
    pass
1
__all__ = ["XutheringWavesUIDAstrBot"]
