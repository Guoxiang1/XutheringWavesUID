from __future__ import annotations

import os
import sys
import json
import types
import asyncio
import logging
from io import BytesIO
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable, Optional


_DATA_ROOT: Optional[Path] = None


class _CompatLogger:
    def __init__(self) -> None:
        self._logger = logging.getLogger("XutheringWavesUID-AstrBot")
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
            self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def _fmt(self, msg: Any, *args: Any) -> str:
        text = str(msg)
        if args:
            text += " " + " ".join(str(i) for i in args)
        return text

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(self._fmt(msg, *args))

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._logger.info(self._fmt(msg, *args))

    def success(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.info(msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(self._fmt(msg, *args))

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._logger.error(self._fmt(msg, *args))

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._logger.error(self._fmt(msg, *args), exc_info=True)


logger = _CompatLogger()


@dataclass
class ImageSegment:
    data: Any


class MessageSegment:
    @staticmethod
    def image(data: Any) -> ImageSegment:
        return ImageSegment(data)

    @staticmethod
    def node(data: Any) -> Any:
        return data


class Event:
    """gsuid_core.models.Event 的最小兼容对象。"""

    def __init__(
        self,
        bot_id: str = "astrbot",
        user_id: str = "",
        user_type: str = "direct",
        group_id: Optional[str] = None,
        bot_self_id: str = "astrbot",
        sender: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        self.bot_id = bot_id
        self.user_id = user_id
        self.user_type = user_type
        self.group_id = group_id
        self.bot_self_id = bot_self_id
        self.sender = sender or {}
        self.raw_text = kwargs.pop("raw_text", "")
        self.text = kwargs.pop("text", "")
        self.command = kwargs.pop("command", "")
        self.regex_dict = kwargs.pop("regex_dict", {})
        self.user_pm = kwargs.pop("user_pm", 6)
        for key, value in kwargs.items():
            setattr(self, key, value)


class Bot:
    logger = logger

    async def send(self, *_: Any, **__: Any) -> None:
        return None

    async def send_option(self, message: Any, *_: Any, **__: Any) -> None:
        return await self.send(message)


class _MsgJson:
    @staticmethod
    def decode(data: str | bytes, **_: Any) -> Any:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return json.loads(data)

    @staticmethod
    def encode(data: Any, **_: Any) -> bytes:
        return json.dumps(data, ensure_ascii=False).encode("utf-8")


msgjson = _MsgJson()


def _ensure_module(name: str) -> types.ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


def _to_thread(func: Optional[Callable[..., Any]] = None):
    def decorator(callable_obj: Callable[..., Any]):
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await asyncio.to_thread(callable_obj, *args, **kwargs)

        wrapper.__name__ = getattr(callable_obj, "__name__", "to_thread_wrapper")
        wrapper.__doc__ = getattr(callable_obj, "__doc__", None)
        return wrapper

    return decorator if func is None else decorator(func)


async def _convert_img(data: Any) -> bytes:
    from PIL import Image

    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, (str, Path)):
        path = Path(data)
        return path.read_bytes() if path.exists() else str(data).encode("utf-8")
    if isinstance(data, Image.Image):
        buffer = BytesIO()
        data.save(buffer, format="PNG")
        return buffer.getvalue()
    return str(data).encode("utf-8")


def _crop_center_img(img: Any, w: int, h: int):
    from PIL import Image

    if not isinstance(img, Image.Image):
        img = Image.open(img)
    img = img.convert("RGBA")
    width, height = img.size
    scale = max(w / max(width, 1), h / max(height, 1))
    resized = img.resize((max(1, int(width * scale)), max(1, int(height * scale))), Image.LANCZOS)
    left = max(0, (resized.width - w) // 2)
    top = max(0, (resized.height - h) // 2)
    return resized.crop((left, top, left + w, top + h))


async def _sget(url: str, **kwargs: Any):
    import httpx

    async with httpx.AsyncClient(timeout=kwargs.pop("timeout", 20)) as client:
        resp = await client.get(url, **kwargs)
    return types.SimpleNamespace(content=resp.content, status_code=resp.status_code, text=resp.text)


def _get_res_path(paths: Optional[list[str] | tuple[str, ...]] = None) -> Path:
    base = _DATA_ROOT or Path(os.environ.get("XUTHERINGWAVESUID_DATA", "./data")).resolve()
    return base.joinpath(*[str(i) for i in paths]) if paths else base


class _SV:
    def __init__(self, *_: Any, **__: Any) -> None:
        pass

    def _decorator(self, *_: Any, **__: Any):
        def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return wrapper

    on_fullmatch = _decorator
    on_command = _decorator
    on_regex = _decorator
    on_prefix = _decorator


class _SL:
    plugins: dict[str, Any] = {}


class _Plugins:
    def __init__(self, name: str, **kwargs: Any) -> None:
        _SL.plugins[name] = kwargs


def _get_plugin_available_prefix(_: str) -> str:
    return os.environ.get("XUTHERINGWAVESUID_PREFIX", "ww")


def _noop_decorator(*_: Any, **__: Any):
    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return wrapper



class _Scheduler:
    def scheduled_job(self, *_: Any, **__: Any):
        return _noop_decorator()


class _SubscribeManager:
    async def get_subscribe(self, *_: Any, **__: Any) -> list[Any]:
        return []


class _Gss:
    active_bot: dict[str, Any] = {}


class _CoreConfig:
    def get_config(self, key: str, default: Any = None) -> Any:
        return [] if key == "masters" else default


class _WebApp:
    def get(self, *_: Any, **__: Any):
        return _noop_decorator()

    post = get
    put = get
    delete = get


class _ConfigItem:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self.data = _args[2] if len(_args) >= 3 else (_args[0] if _args else None)


class _StringConfig:
    def __init__(self, name: str, path: Path, defaults: dict[str, Any]) -> None:
        self.name = name
        self.path = Path(path)
        self.defaults = defaults
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._override = json.loads(self.path.read_text("utf-8")) if self.path.exists() else {}
        except Exception:
            self._override = {}

    def get_config(self, key: str) -> Any:
        if key in self._override:
            value = self._override[key]
            if isinstance(value, dict) and "data" in value:
                value = value["data"]
            return types.SimpleNamespace(data=value)
        item = self.defaults.get(key)
        return types.SimpleNamespace(data=getattr(item, "data", item))

    def set_config(self, key: str, value: Any) -> None:
        self._override[key] = value
        try:
            self.path.write_text(json.dumps(self._override, ensure_ascii=False, indent=2), "utf-8")
        except Exception:
            pass


def _install_gsuid_core_modules() -> None:
    core = _ensure_module("gsuid_core")

    logger_mod = types.ModuleType("gsuid_core.logger")
    logger_mod.logger = logger
    sys.modules["gsuid_core.logger"] = logger_mod

    models_mod = types.ModuleType("gsuid_core.models")
    models_mod.Event = Event
    sys.modules["gsuid_core.models"] = models_mod

    bot_mod = types.ModuleType("gsuid_core.bot")
    bot_mod.Bot = Bot
    bot_mod.msgjson = msgjson
    sys.modules["gsuid_core.bot"] = bot_mod

    segment_mod = types.ModuleType("gsuid_core.segment")
    segment_mod.MessageSegment = MessageSegment
    sys.modules["gsuid_core.segment"] = segment_mod

    pool_mod = types.ModuleType("gsuid_core.pool")
    pool_mod.to_thread = _to_thread
    sys.modules["gsuid_core.pool"] = pool_mod

    data_store_mod = types.ModuleType("gsuid_core.data_store")
    data_store_mod.get_res_path = _get_res_path
    sys.modules["gsuid_core.data_store"] = data_store_mod

    sv_mod = types.ModuleType("gsuid_core.sv")
    sv_mod.SV = _SV
    sv_mod.SL = _SL
    sv_mod.Plugins = _Plugins
    sv_mod.get_plugin_available_prefix = _get_plugin_available_prefix
    sys.modules["gsuid_core.sv"] = sv_mod

    server_mod = types.ModuleType("gsuid_core.server")
    server_mod.on_core_shutdown = _noop_decorator
    server_mod.on_core_start = _noop_decorator
    sys.modules["gsuid_core.server"] = server_mod

    aps_mod = types.ModuleType("gsuid_core.aps")
    aps_mod.scheduler = _Scheduler()
    sys.modules["gsuid_core.aps"] = aps_mod

    subscribe_mod = types.ModuleType("gsuid_core.subscribe")
    subscribe_mod.gs_subscribe = _SubscribeManager()
    sys.modules["gsuid_core.subscribe"] = subscribe_mod

    gss_mod = types.ModuleType("gsuid_core.gss")
    gss_mod.gss = _Gss()
    sys.modules["gsuid_core.gss"] = gss_mod

    config_mod = types.ModuleType("gsuid_core.config")
    config_mod.core_config = _CoreConfig()
    sys.modules["gsuid_core.config"] = config_mod

    web_app_mod = types.ModuleType("gsuid_core.web_app")
    web_app_mod.app = _WebApp()
    sys.modules["gsuid_core.web_app"] = web_app_mod

    _ensure_module("gsuid_core.utils")
    _ensure_module("gsuid_core.utils.image")
    convert_mod = types.ModuleType("gsuid_core.utils.image.convert")
    convert_mod.convert_img = _convert_img
    sys.modules["gsuid_core.utils.image.convert"] = convert_mod
    image_tools_mod = types.ModuleType("gsuid_core.utils.image.image_tools")
    image_tools_mod.crop_center_img = _crop_center_img
    sys.modules["gsuid_core.utils.image.image_tools"] = image_tools_mod
    image_utils_mod = types.ModuleType("gsuid_core.utils.image.utils")
    image_utils_mod.sget = _sget
    sys.modules["gsuid_core.utils.image.utils"] = image_utils_mod

    _ensure_module("gsuid_core.utils.plugins_config")
    pc_models = types.ModuleType("gsuid_core.utils.plugins_config.models")
    for name in ("GSC", "GsIntConfig", "GsStrConfig", "GsBoolConfig", "GsListStrConfig", "GsImageConfig"):
        setattr(pc_models, name, _ConfigItem)
    sys.modules["gsuid_core.utils.plugins_config.models"] = pc_models
    pc_gs_config = types.ModuleType("gsuid_core.utils.plugins_config.gs_config")
    pc_gs_config.StringConfig = _StringConfig
    sys.modules["gsuid_core.utils.plugins_config.gs_config"] = pc_gs_config

    webconsole_mod = types.ModuleType("gsuid_core.webconsole.mount_app")
    webconsole_mod.PageSchema = object
    webconsole_mod.GsAdminModel = object
    webconsole_mod.site = types.SimpleNamespace(register_admin=lambda *a, **k: None)
    _ensure_module("gsuid_core.webconsole")
    sys.modules["gsuid_core.webconsole.mount_app"] = webconsole_mod

    _ensure_module("gsuid_core.help")
    help_model = types.ModuleType("gsuid_core.help.model")
    help_model.PluginHelp = dict
    sys.modules["gsuid_core.help.model"] = help_model
    help_draw = types.ModuleType("gsuid_core.help.draw_new_plugin_help")

    async def _get_new_help(**kwargs: Any) -> bytes:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (1000, 600), (28, 31, 38))
        draw = ImageDraw.Draw(img)
        draw.text((40, 40), kwargs.get("plugin_name", "XutheringWavesUID"), fill=(255, 255, 255))
        draw.text((40, 90), "AstrBot 基础适配版：请发送 ww帮助 查看文本帮助。", fill=(220, 220, 220))
        buf = BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()

    help_draw.get_new_help = _get_new_help
    sys.modules["gsuid_core.help.draw_new_plugin_help"] = help_draw
    help_utils = types.ModuleType("gsuid_core.help.utils")
    help_utils.register_help = lambda *args, **kwargs: None
    sys.modules["gsuid_core.help.utils"] = help_utils

    _ensure_module("gsuid_core.utils.download_resource")
    download_file_mod = types.ModuleType("gsuid_core.utils.download_resource.download_file")
    download_file_mod.download = lambda *args, **kwargs: None
    sys.modules["gsuid_core.utils.download_resource.download_file"] = download_file_mod
    download_core_mod = types.ModuleType("gsuid_core.utils.download_resource.download_core")

    async def _download_all_file(*_: Any, **__: Any) -> None:
        return None

    download_core_mod.download_all_file = _download_all_file
    sys.modules["gsuid_core.utils.download_resource.download_core"] = download_core_mod
    setattr(core, "logger", logger_mod)


def _install_xw_package_stubs(project_root: Path, data_root: Path) -> None:
    src_pkg = project_root / "XutheringWavesUID"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    pkg = types.ModuleType("XutheringWavesUID")
    pkg.__path__ = [str(src_pkg)]
    pkg.__file__ = str(src_pkg / "__init__.py")
    sys.modules["XutheringWavesUID"] = pkg

    defaults = {
        "HideUid": _ConfigItem("隐藏uid", "", False),
        "WavesToken": _ConfigItem("鸣潮全排行token", "", ""),
        "WavesOnlySelfCk": _ConfigItem("是否仅本人ck", "", False),
        "WavesGuide": _ConfigItem("角色攻略图提供方", "", ["all"]),
        "WavesGuideMaxSize": _ConfigItem("攻略图片最大大小", "", 2),
        "HelpExtraModules": _ConfigItem("帮助扩展", "", []),
        "UseHtmlRender": _ConfigItem("HTML渲染", "", False),
        "RefreshSingleCharBehavior": _ConfigItem("刷新发送逻辑", "", "concatenate"),
        "AutoSendCharAfterRefresh": _ConfigItem("刷新后自动发送", "", True),
        "HelpColumn": _ConfigItem("帮助列数", "", 5),
        "HelpBannerBgUpload": _ConfigItem("帮助横幅", "", ""),
        "HelpBgUpload": _ConfigItem("帮助背景", "", ""),
        "HelpIconUpload": _ConfigItem("帮助图标", "", ""),
        "CardBg": _ConfigItem("自定义背景", "", False),
        "BlurRadius": _ConfigItem("毛玻璃", "", 0),
        "BlurBrightness": _ConfigItem("亮度", "", "1.2"),
        "BlurContrast": _ConfigItem("对比度", "", "0.9"),
        "BotColorMap": _ConfigItem("颜色", "", ""),
        "RemoteRenderEnable": _ConfigItem("远程渲染", "", False),
        "RemoteRenderUrl": _ConfigItem("远程渲染地址", "", ""),
    }
    show_defaults = dict(defaults)
    show_defaults["CardBgPath"] = _ConfigItem("自定义背景路径", "", str(data_root / "XutheringWavesUID" / "show" / "card.jpg"))
    ww_config = _StringConfig("XutheringWavesUID", data_root / "XutheringWavesUID" / "config.json", defaults)
    show_config = _StringConfig("鸣潮展示配置", data_root / "XutheringWavesUID" / "show_config.json", show_defaults)

    cfg_pkg = types.ModuleType("XutheringWavesUID.wutheringwaves_config")
    cfg_pkg.__path__ = [str(src_pkg / "wutheringwaves_config")]
    cfg_pkg.PREFIX = _get_plugin_available_prefix("XutheringWavesUID")
    cfg_pkg.WutheringWavesConfig = ww_config
    cfg_pkg.ShowConfig = show_config
    sys.modules["XutheringWavesUID.wutheringwaves_config"] = cfg_pkg
    cfg_leaf = types.ModuleType("XutheringWavesUID.wutheringwaves_config.wutheringwaves_config")
    cfg_leaf.WutheringWavesConfig = ww_config
    cfg_leaf.ShowConfig = show_config
    sys.modules["XutheringWavesUID.wutheringwaves_config.wutheringwaves_config"] = cfg_leaf

    db_pkg = types.ModuleType("XutheringWavesUID.utils.database")
    db_pkg.__path__ = [str(src_pkg / "utils" / "database")]
    sys.modules["XutheringWavesUID.utils.database"] = db_pkg

    class _WavesLangSettings:
        @classmethod
        async def get_lang(cls, *_: Any, **__: Any) -> str:
            return ""

        @classmethod
        async def set_lang(cls, *_: Any, **__: Any) -> bool:
            return True

    class _WavesUser:
        cookie = ""
        uid = ""
        did = ""
        bat = ""
        status = ""
        game_id = 3
        hide_uid_self_value = ""

        @classmethod
        async def select_waves_user(cls, *_: Any, **__: Any) -> None:
            return None

        @classmethod
        async def select_data_by_cookie_and_uid(cls, *_: Any, **__: Any) -> None:
            return None

        @classmethod
        async def select_data_by_cookie(cls, *_: Any, **__: Any) -> None:
            return None

        @classmethod
        async def get_waves_all_user(cls, *_: Any, **__: Any) -> list[Any]:
            return []

        @classmethod
        async def cookie_validate(cls, *_: Any, **__: Any) -> bool:
            return False

        @classmethod
        async def update_last_used_time(cls, *_: Any, **__: Any) -> bool:
            return True

        @classmethod
        async def update_data_by_data(cls, *_: Any, **__: Any) -> bool:
            return True

    class _WavesBind:
        @classmethod
        async def get_uid_by_game(cls, *_: Any, **__: Any) -> None:
            return None

    class _NoopModel:
        pass

    db_models = types.ModuleType("XutheringWavesUID.utils.database.models")
    db_models.WavesLangSettings = _WavesLangSettings
    db_models.WavesUser = _WavesUser
    db_models.WavesBind = _WavesBind
    db_models.WavesStaminaRecord = _NoopModel
    sys.modules["XutheringWavesUID.utils.database.models"] = db_models

    for mod_name, cls_name in {
        "waves_subscribe": "WavesSubscribe",
        "waves_user_activity": "WavesUserActivity",
        "waves_user_sdk": "WavesUserSdk",
        "waves_gacha_cloud": "WavesGachaCloud",
    }.items():
        mod = types.ModuleType(f"XutheringWavesUID.utils.database.{mod_name}")
        setattr(mod, cls_name, _NoopModel)
        sys.modules[f"XutheringWavesUID.utils.database.{mod_name}"] = mod


def install(project_root: Path, data_root: Path) -> None:
    """安装早柚核心最小兼容层，需在导入 XutheringWavesUID 子模块前调用。"""
    global _DATA_ROOT
    _DATA_ROOT = Path(os.environ.get("XUTHERINGWAVESUID_DATA", str(data_root))).resolve()
    _DATA_ROOT.mkdir(parents=True, exist_ok=True)
    _install_gsuid_core_modules()
    _install_xw_package_stubs(Path(project_root).resolve(), _DATA_ROOT)


__all__ = ["install", "Event", "Bot", "ImageSegment", "MessageSegment", "logger"]
