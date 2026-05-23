# XutheringWavesUID AstrBot 基础适配版

这是在原早柚核心插件 `XutheringWavesUID` 基础上新增的 AstrBot 适配入口，目标是先让常用基础功能在 AstrBot 中可加载、可使用。

## 已适配功能

- `ww帮助`
- `ww兑换码` / `wwcode`
- `ww日历`
- `ww卡池倒计时` / `ww未复刻角色` / `ww未复刻武器4`
- `ww长离技能` / `ww长离共鸣链` / `ww长离机制`
- `ww长离攻略`
- `ww武器列表` / `ww音感仪武器列表` / `ww套装列表`
- `ww长离别名` / `ww别名列表`
- `ww绑定123456789` / `ww查看` / `ww删除绑定`
- `ww角色面板长离` / `ww长离面板` / `ww查询长离`

## 依赖安装

AstrBot 环境需要安装仓库根目录 `requirements.txt` 中的依赖。基础功能主要依赖：

- `httpx` / `aiohttp` / `aiofiles`
- `pydantic>=2` / `msgspec`
- `pillow` / `jinja2`
- `pypinyin` / `rapidfuzz`

`playwright`、`opencv-python` 属于增强功能依赖；如需 HTML 渲染或图片查重再启用。

## 角色面板查询说明

当前基础版先支持**读取已有本地面板缓存并渲染**，不会主动执行库街区登录或刷新面板。

缓存目录为：

```text
astrbot_plugin_xutheringwavesuid/data/gsuid_data/XutheringWavesUID/players/<uid>/rawData.json
astrbot_plugin_xutheringwavesuid/data/gsuid_data/XutheringWavesUID/players/<uid>/baseInfo.json
```

如果你已有早柚核心版数据，可以把对应 UID 的 `players/<uid>` 目录迁移到上面的目录。

如果没有 `baseInfo.json`，适配层会自动生成一个最小基础信息文件；但必须存在 `rawData.json` 才能渲染角色面板。

## 资源目录

原插件的大部分图片/Wiki/攻略/角色资源仍使用：

```text
astrbot_plugin_xutheringwavesuid/data/gsuid_data/XutheringWavesUID/resource
```

也可以通过环境变量指定数据根目录：

```bash
XUTHERINGWAVESUID_DATA=/path/to/gsuid_core/data
```

此时适配层会读取：

```text
$XUTHERINGWAVESUID_DATA/XutheringWavesUID
```

## 未完成 / 后续计划

- AstrBot 原生登录流程
- AstrBot 原生刷新面板
- 体力、抽卡、排行、订阅、定时推送等完整账号功能
- 更完整的权限体系与数据库迁移
