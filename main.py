"""AstrBot 入口兼容文件。

AstrBot 通常会从插件根目录的 ``main.py`` 加载插件；实际实现放在
``astrbot_plugin_xutheringwavesuid`` 包内，方便与原早柚核心版本代码隔离。
"""

from astrbot_plugin_xutheringwavesuid.main import XutheringWavesUIDAstrBot

__all__ = ["XutheringWavesUIDAstrBot"]
