from __future__ import annotations

import re
import json
import base64
import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from .adapter.binds import BindStore
from .adapter.gsuid_core_shim import Event, ImageSegment, install as install_gsuid_shim


try:  # AstrBot 运行时
    from astrbot.api.event import filter, AstrMessageEvent
    from astrbot.api.star import Context, Star, register
except Exception:  # 允许普通 Python 环境静态检查
    class AstrMessageEvent:  # type: ignore
        pass

    class Context:  # type: ignore
        pass

    class Star:  # type: ignore
        def __init__(self, context: Any = None) -> None:
            self.context = context

    def register(*_: Any, **__: Any):  # type: ignore
        def deco(cls: type) -> type:
            return cls

        return deco

    class _Filter:  # type: ignore
        @staticmethod
        def command(*_: Any, **__: Any):
            def deco(func: Any) -> Any:
                return func

            return deco

        @staticmethod
        def regex(*_: Any, **__: Any):
            def deco(func: Any) -> Any:
                return func

            return deco

    filter = _Filter()


PLUGIN_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PLUGIN_DIR.parent
DATA_ROOT = PLUGIN_DIR / "data"
GSUID_DATA_ROOT = DATA_ROOT / "gsuid_data"
CACHE_DIR = DATA_ROOT / "cache"

install_gsuid_shim(PROJECT_ROOT, GSUID_DATA_ROOT)


class _CollectBot:
    """收集早柚函数 bot.send 输出，交给 AstrBot 统一发送。"""

    def __init__(self) -> None:
        self.payloads: list[Any] = []
        from gsuid_core.logger import logger

        self.logger = logger

    async def send(self, message: Any = None, *_: Any, **__: Any) -> None:
        if message is not None:
            self.payloads.append(message)

    async def send_option(self, message: Any = None, *_: Any, **__: Any) -> None:
        await self.send(message)


@register(
    "XutheringWavesUID",
    "XutheringWavesUID contributors / Cline",
    "鸣潮 XutheringWavesUID 的 AstrBot 基础适配版",
    "1.0.0-astrbot-basic",
)
class XutheringWavesUIDAstrBot(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.binds = BindStore(DATA_ROOT / "binds.json")

    @filter.command("ww")
    async def ww_command(self, event: AstrMessageEvent) -> AsyncGenerator[Any, None]:
        text = self._strip_prefix(self._event_text(event))
        async for result in self._handle_and_yield(event, text):
            yield result

    @filter.command("xw")
    async def xw_command(self, event: AstrMessageEvent) -> AsyncGenerator[Any, None]:
        text = self._strip_prefix(self._event_text(event))
        async for result in self._handle_and_yield(event, text):
            yield result

    @filter.regex(r"^(?:ww|xw|鸣潮)\s*.*$")
    async def ww_regex(self, event: AstrMessageEvent) -> AsyncGenerator[Any, None]:
        text = self._strip_prefix(self._event_text(event))
        async for result in self._handle_and_yield(event, text):
            yield result

    async def _handle_and_yield(self, event: AstrMessageEvent, text: str) -> AsyncGenerator[Any, None]:
        try:
            payloads = await self._dispatch(event, text.strip())
        except Exception as exc:
            payloads = [f"[鸣潮] AstrBot 适配层执行失败：{exc}"]
        for payload in payloads:
            async for result in self._payload_to_results(event, payload):
                yield result

    async def _dispatch(self, event: AstrMessageEvent, text: str) -> list[Any]:
        if not text or text in {"帮助", "幫助", "help", "bz"}:
            return [self._help_text()]

        if text in {"兑换码", "兌換碼", "code"}:
            return [await self._code_text()]

        if text in {"日历", "日曆", "个人日历", "個人日曆", "rl"}:
            return [await self._calendar(event, text)]

        if any(key in text for key in ("卡池倒计时", "卡池倒計時", "未复刻", "未復刻")):
            return [await self._pool(text)]

        bind_payload = await self._try_bind_command(event, text)
        if bind_payload is not None:
            return [bind_payload]

        alias_payload = await self._try_alias(text)
        if alias_payload is not None:
            return [alias_payload]

        panel_char = self._match_panel_query(text)
        if panel_char:
            return [await self._panel(event, panel_char)]

        wiki_payload = await self._try_wiki(event, text)
        if wiki_payload is not None:
            return wiki_payload if isinstance(wiki_payload, list) else [wiki_payload]

        return [f"[鸣潮] 暂未识别命令：{text}\n发送 ww帮助 查看 AstrBot 基础版支持的命令。"]

    async def _try_bind_command(self, event: AstrMessageEvent, text: str) -> Optional[str]:
        user_id = self._event_user_id(event)
        m = re.match(r"^(?:绑定|bind)\s*(?:uid|UID)?\s*(\d{9})$", text)
        if m:
            uid = m.group(1)
            await self.binds.bind(user_id, uid)
            return f"[鸣潮] 特征码 {self._hide_uid(uid)} 绑定成功。\n现在可尝试：ww角色面板长离 / ww长离面板"

        if text in {"查看", "查看绑定", "uid", "UID"}:
            uid = await self.binds.get(user_id)
            if not uid:
                return "[鸣潮] 你还没有绑定特征码，请发送：ww绑定123456789"
            return f"[鸣潮] 当前绑定特征码：{self._hide_uid(uid)}"

        m = re.match(r"^(?:删除绑定|删除|解绑|unbind)\s*(?:uid|UID)?\s*(\d{9})?$", text)
        if m:
            existed = await self.binds.delete(user_id)
            return "[鸣潮] 已删除当前 AstrBot 绑定。" if existed else "[鸣潮] 当前没有可删除的绑定。"
        return None

    async def _code_text(self) -> str:
        from XutheringWavesUID.wutheringwaves_code import get_code_list, invalid_code_list

        code_list = await get_code_list()
        if not code_list:
            return "[鸣潮·获取兑换码失败] 请稍后再试"
        msgs = []
        for code in code_list:
            if code.get("is_fail", "0") == "1":
                continue
            order = code.get("order", "")
            if order in invalid_code_list or not order:
                continue
            reward = code.get("reward", "")
            label = code.get("label", "")
            msgs.append(f"兑换码: {order}\n奖励: {reward}\n{label}".strip())
        return "\n\n".join(msgs) if msgs else "[鸣潮] 暂未获取到可用兑换码。"

    async def _calendar(self, event: AstrMessageEvent, text: str) -> Any:
        from XutheringWavesUID.wutheringwaves_calendar.draw_calendar_card import draw_calendar_img

        return await draw_calendar_img(self._make_ev(event, text, command="日历"), "")

    async def _pool(self, text: str) -> Any:
        from XutheringWavesUID.wutheringwaves_up.pool import get_pool_data_by_type

        query_type = "武器" if "武器" in text else "角色"
        star = 4 if ("4" in text or "四" in text) else 5
        return await get_pool_data_by_type(query_type, star)

    async def _try_alias(self, text: str) -> Optional[Any]:
        if text in {"别名", "别名列表"}:
            from XutheringWavesUID.utils.name_convert import ensure_data_loaded, char_alias_data

            ensure_data_loaded()
            if not char_alias_data:
                return "[鸣潮] 暂无别名数据，请先下载/迁移资源。"
            lines = ["[鸣潮] 角色别名列表（文本简版）："]
            for idx, (name, aliases) in enumerate(char_alias_data.items()):
                if idx >= 80:
                    lines.append("……内容较多，仅显示前 80 项。")
                    break
                other = [a for a in aliases if a != name]
                lines.append(f"{name}: {'、'.join(other[:12]) if other else '暂无'}")
            return "\n".join(lines)

        m = re.match(r"^(.{1,20})别名(?:列表)?$", text)
        if m:
            from XutheringWavesUID.wutheringwaves_alias.char_alias_ops import char_alias_list

            return await char_alias_list(m.group(1).strip())
        return None

    def _match_panel_query(self, text: str) -> Optional[str]:
        for pattern in (
            r"^(?:角色面板|查询)\s*(?P<char>.+)$",
            r"^(?P<char>.+?)(?:面板|面版|面包|🍞|mb)$",
        ):
            m = re.match(pattern, text, re.IGNORECASE)
            if not m:
                continue
            char = m.group("char").strip()
            if char and char not in {"刷新", "更新", "强制刷新"}:
                return char
        return None

    async def _panel(self, event: AstrMessageEvent, char: str) -> Any:
        uid = await self.binds.get(self._event_user_id(event))
        if not uid:
            return "[鸣潮] 角色面板查询需要先绑定特征码：ww绑定123456789"

        player_dir = GSUID_DATA_ROOT / "XutheringWavesUID" / "players" / uid
        raw_data = player_dir / "rawData.json"
        if not raw_data.exists():
            return (
                f"[鸣潮] 已绑定 {self._hide_uid(uid)}，但未找到角色面板缓存。\n"
                f"AstrBot 基础版当前先支持读取已有缓存渲染，缺少：\n{raw_data}\n"
                "可从早柚核心数据目录迁移 players/<uid>/rawData.json 与 baseInfo.json，"
                "或等待后续适配 AstrBot 登录/刷新面板。"
            )

        await self._ensure_base_info(uid, player_dir)
        from XutheringWavesUID.utils.name_resolve import resolve_char
        from XutheringWavesUID.wutheringwaves_charinfo.draw_char_card import draw_char_detail_img

        res = resolve_char(char)
        if not res.ok:
            return res.fail_msg()
        matched = res.matched or char
        ev = self._make_ev(event, f"角色面板{matched}", command="角色面板", text=matched)
        im = await draw_char_detail_img(ev, uid, matched, ev.user_id)
        if isinstance(im, str):
            return res.with_tip(im, f"ww角色面板{matched}")
        return res.wrap(im, f"ww角色面板{matched}")

    async def _ensure_base_info(self, uid: str, player_dir: Path) -> None:
        base_info = player_dir / "baseInfo.json"
        if base_info.exists():
            return
        player_dir.mkdir(parents=True, exist_ok=True)
        base_info.write_text(
            json.dumps(
                {"name": f"漂泊者{uid[-4:]}", "id": int(uid), "level": 0, "worldLevel": 0, "roleNum": 0},
                ensure_ascii=False,
            ),
            "utf-8",
        )

    async def _try_wiki(self, event: AstrMessageEvent, text: str) -> Optional[Any]:
        if re.match(r"^(?:(?:长刃|迅刀|讯刀|佩枪|臂铠|臂甲|音感仪)(?:武器(?:列表)?|列表|wq(?:lb)?)|武器(?:列表)?|wq(?:lb)?)$", text):
            from XutheringWavesUID.wutheringwaves_wiki.draw_list import draw_weapon_list

            weapon_type = ""
            for t in ("长刃", "迅刀", "讯刀", "佩枪", "臂铠", "臂甲", "音感仪"):
                if text.startswith(t):
                    weapon_type = t
                    break
            return await draw_weapon_list(weapon_type)

        m = re.match(r"^(?:(?P<pre>\d+\.\d+))?(?:套装|套裝)(?:列表)?(?:(?P<post>\d+\.\d+))?$", text)
        if m:
            from XutheringWavesUID.wutheringwaves_wiki.draw_list import draw_sonata_list

            return await draw_sonata_list(m.group("pre") or m.group("post") or "")

        m = re.match(r"^(?P<char>.+?)(?:攻略|gl)$", text, re.IGNORECASE)
        if m:
            from XutheringWavesUID.wutheringwaves_wiki.guide import get_guide

            bot = _CollectBot()
            await get_guide(bot, self._make_ev(event, text), m.group("char").strip())
            return bot.payloads or ["[鸣潮] 暂无攻略。"]

        m = re.match(
            r"^(?P<name>.+?)(?P<typ>共鸣链|共鳴鏈|gml|命座|天赋|天賦|技能|jn|图鉴|圖鑑|专武|武器|專武|wiki|介绍|介紹|回路|操作|机制|機制|jz)$",
            text,
            re.IGNORECASE,
        )
        if not m:
            return None

        name = m.group("name").strip()
        typ = m.group("typ")
        from XutheringWavesUID.utils import name_convert
        from XutheringWavesUID.utils.fuzzy_match import fuzzy_suggest, fuzzy_suggest_multi
        from XutheringWavesUID.utils.name_convert import char_name_to_char_id, ensure_data_loaded
        from XutheringWavesUID.wutheringwaves_wiki.draw_char import draw_char_wiki
        from XutheringWavesUID.wutheringwaves_wiki.draw_echo import draw_wiki_echo
        from XutheringWavesUID.wutheringwaves_wiki.draw_weapon import draw_wiki_weapon

        if typ in ("共鸣链", "共鳴鏈", "gml", "命座", "天赋", "天賦", "技能", "jn", "回路", "操作", "机制", "機制", "jz"):
            query_type = "技能" if typ in ("技能", "天赋", "天賦", "jn") else "共鸣链" if typ in ("共鸣链", "共鳴鏈", "命座", "gml") else "机制"
            char_id = char_name_to_char_id(name)
            if char_id:
                img = await draw_char_wiki(char_id, query_type)
                if not isinstance(img, str):
                    return img
            ensure_data_loaded()
            suggestions = fuzzy_suggest(name, name_convert.char_alias_data, top_n=3)
            if suggestions:
                return f"[鸣潮] 未找到指定角色。你可能想找: {'、'.join(n for n, _ in suggestions)}"
            return "[鸣潮] 未找到指定角色, 请先检查输入是否正确！"

        if typ in ("专武", "專武", "武器"):
            name = name + "专武"
        img = await draw_wiki_weapon(name)
        if isinstance(img, str) or not img:
            img = await draw_wiki_echo(name)
        if not (isinstance(img, str) or not img):
            return img
        ensure_data_loaded()
        suggestions = fuzzy_suggest_multi(name, [("武器", name_convert.weapon_alias_data), ("共鸣", name_convert.echo_alias_data)], top_n=3)
        if suggestions:
            return f"[鸣潮] wiki 未找到指定内容。你可能想找: {'、'.join(n for _, n, _ in suggestions)}"
        return "[鸣潮] wiki 未找到指定内容, 请先检查输入是否正确！"

    def _make_ev(
        self,
        event: AstrMessageEvent,
        raw_text: str,
        *,
        command: str = "",
        text: Optional[str] = None,
        regex_dict: Optional[dict[str, str]] = None,
    ) -> Event:
        return Event(
            bot_id="astrbot",
            bot_self_id="astrbot",
            user_id=self._event_user_id(event),
            group_id=self._event_group_id(event),
            user_type="group" if self._event_group_id(event) else "direct",
            raw_text=raw_text,
            text=raw_text if text is None else text,
            command=command,
            regex_dict=regex_dict or {},
            user_pm=6,
            sender={},
        )

    def _event_text(self, event: AstrMessageEvent) -> str:
        for attr in ("message_str", "text", "raw_message"):
            value = getattr(event, attr, None)
            if isinstance(value, str):
                return value.strip()
        for method in ("get_message_str", "get_plain_text"):
            func = getattr(event, method, None)
            if callable(func):
                try:
                    value = func()
                    if isinstance(value, str):
                        return value.strip()
                except Exception:
                    pass
        return ""

    def _strip_prefix(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"^/", "", text)
        return re.sub(r"^(?:ww|xw|鸣潮)\s*", "", text, flags=re.IGNORECASE).strip()

    def _event_user_id(self, event: AstrMessageEvent) -> str:
        for method in ("get_sender_id", "get_user_id"):
            func = getattr(event, method, None)
            if callable(func):
                try:
                    value = func()
                    if value:
                        return str(value)
                except Exception:
                    pass
        for attr in ("sender_id", "user_id"):
            value = getattr(event, attr, None)
            if value:
                return str(value)
        msg_obj = getattr(event, "message_obj", None)
        for attr in ("sender_id", "user_id"):
            value = getattr(msg_obj, attr, None)
            if value:
                return str(value)
        return "astrbot_user"

    def _event_group_id(self, event: AstrMessageEvent) -> Optional[str]:
        func = getattr(event, "get_group_id", None)
        if callable(func):
            try:
                value = func()
                if value:
                    return str(value)
            except Exception:
                pass
        value = getattr(event, "group_id", None)
        if value:
            return str(value)
        msg_obj = getattr(event, "message_obj", None)
        value = getattr(msg_obj, "group_id", None)
        return str(value) if value else None

    async def _payload_to_results(self, event: AstrMessageEvent, payload: Any) -> AsyncGenerator[Any, None]:
        if payload is None:
            return
        if isinstance(payload, ImageSegment):
            async for result in self._payload_to_results(event, payload.data):
                yield result
            return
        if isinstance(payload, (list, tuple)):
            for item in payload:
                async for result in self._payload_to_results(event, item):
                    yield result
            return
        if isinstance(payload, str) and payload.startswith("base64://"):
            try:
                data = base64.b64decode(payload[len("base64://") :])
                yield self._image_result(event, data)
            except Exception:
                yield self._plain_result(event, payload)
            return
        if isinstance(payload, (bytes, bytearray)):
            yield self._image_result(event, bytes(payload))
            return
        try:
            from PIL import Image

            if isinstance(payload, Image.Image):
                buf = BytesIO()
                payload.save(buf, "PNG")
                yield self._image_result(event, buf.getvalue())
                return
        except Exception:
            pass
        yield self._plain_result(event, str(payload))

    def _plain_result(self, event: AstrMessageEvent, text: str) -> Any:
        return event.plain_result(text) if hasattr(event, "plain_result") else text

    def _image_result(self, event: AstrMessageEvent, data: bytes) -> Any:
        suffix = ".jpg" if data[:3] == b"\xff\xd8\xff" else ".png"
        name = hashlib.sha256(data).hexdigest()[:24] + suffix
        path = CACHE_DIR / name
        if not path.exists():
            path.write_bytes(data)
        return event.image_result(str(path)) if hasattr(event, "image_result") else self._plain_result(event, f"[鸣潮] 图片已生成：{path}")

    def _hide_uid(self, uid: str) -> str:
        uid = str(uid)
        return uid[:2] + "****" + uid[-2:] if len(uid) >= 4 else uid

    def _help_text(self) -> str:
        return (
            "XutheringWavesUID AstrBot 基础版\n"
            "前缀：ww / xw / 鸣潮\n\n"
            "基础查询：\n"
            "- ww兑换码 / wwcode\n"
            "- ww日历\n"
            "- ww卡池倒计时 / ww未复刻角色 / ww未复刻武器4\n\n"
            "Wiki / 攻略 / 别名：\n"
            "- ww长离技能 / ww长离共鸣链 / ww长离机制\n"
            "- ww长离攻略\n"
            "- ww武器列表 / ww音感仪武器列表 / ww套装列表\n"
            "- ww长离别名 / ww别名列表\n\n"
            "角色面板缓存查询：\n"
            "- ww绑定123456789\n"
            "- ww查看\n"
            "- ww角色面板长离 / ww长离面板 / ww查询长离\n\n"
            "说明：当前基础版的角色面板先读取本地缓存 "
            "data/gsuid_data/XutheringWavesUID/players/<uid>/rawData.json；"
            "登录与刷新面板属于后续完整账号功能。"
        )
