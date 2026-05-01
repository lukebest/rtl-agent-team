> **English**: [README.md](./README.md) · **한국어**: [README_kr.md](./README_kr.md)

# RTL Agent Team（简体中文）

面向 **SystemVerilog / Verilog RTL** 设计与验证的自动化插件：97 个专职 Agent 与 97 个 Skill，覆盖六阶段流水线（Research → Architecture → μArch → RTL → Verify → Design Note）。

本仓库同时提供 **Claude Code** 插件（`.claude-plugin/`）与 **Cursor** 插件包（`cursor-pack/`，由脚本生成）。

![](./rat_logo.jpg)

## Cursor 插件说明

可安装的 Cursor 插件根目录为 **`cursor-pack/`**：内含 `.cursor-plugin/plugin.json`、`hooks/hooks.json`（Cursor 事件名与 Claude 不同）、以及与仓库同步的 `skills/`、`agents/`、`hooks` 运行时脚本副本（`runtime/hooks/`）。

重新生成该目录（需要 **python3**，以及 **rsync**）：

```bash
sh scripts/sync_cursor_pack.sh
```

将 Cursor 规则模板部署到**用户 RTL 工程**（仅复制尚不存在的 `.mdc` 文件，不覆盖已有规则）：

```bash
sh scripts/rat-init-cursor-project.sh /你的工程路径
```

设计说明（英文，面向维护者）：[`plugin_docs/specs/2026-05-01-cursor-marketplace-plugin-design.md`](./plugin_docs/specs/2026-05-01-cursor-marketplace-plugin-design.md)。

---

## 从 Cursor Marketplace 安装（上架后）

官方上架完成后，在 Cursor 内打开 **Settings → Plugins（或扩展/插件，名称以当前 Cursor 版本为准）**，在 Marketplace 中搜索 **rtl-agent-team**，选择安装。

安装完成后可能需要 **Reload Window**。若插件加载成功，在已安装插件列表中应能看到 **rtl-agent-team**。

---

## 手动安装（Git 克隆）

适用于 Marketplace 未上架或需要固定某一提交的开发者安装方式。

1. **克隆本仓库**  
   `git clone https://github.com/babyworm/rtl-agent-team.git`

2. **生成最新的 `cursor-pack/`（推荐）**  
   在仓库根目录执行：`sh scripts/sync_cursor_pack.sh`

3. **在 Cursor 中添加本地插件**  
   打开 **Settings → Plugins**，选择 **Install from folder**（或“从文件夹安装”等同级菜单项；具体文案随 Cursor 版本变化）。  
   **请选择文件夹：`rtl-agent-team/cursor-pack`**（该目录下必须存在 `.cursor-plugin/plugin.json`）。  
   **不要**选择仓库根目录（根目录是 Claude Marketplace 布局，不是 Cursor 单插件根）。

4. **信任工作区**  
   若 Cursor 提示工作区信任（Trusted Workspace），加载项目级 hooks 前需信任该工程目录。

5. **（可选）仅部署规则到当前工程**  
   `sh scripts/rat-init-cursor-project.sh /你的 rtl 工程根路径`

---

## 手动卸载

1. 打开 **Settings → Plugins**，在已安装列表中找到 **rtl-agent-team**（或 manifest 中的插件 id）。
2. 选择 **Disable（禁用）**、**Remove（移除）** 或 **Uninstall（卸载）**（以当前界面为准）。
3. **卸载插件不会删除**你工程里的 RTL 产物（例如 `rtl/`、`docs/`、`.rat/` 等）；仅移除 Cursor 侧的插件与缓存行为。
4. 若曾运行 `rat-init-cursor-project.sh`，工程内 `.cursor/rules/*.mdc` 可选择手动删除；不影响卸载插件本身。

---

## 本地验证 Stop 门控脚本（可选）

仓库提供与 Stop hook 语义一致的本地脚本（用于在用户工程根目录手动检查）：

```bash
sh cursor-pack/gates/cursor-verify-stop.sh
```

---

## 与 Claude Code 工作流的对应关系

在 Cursor 中使用插件时，文档与状态中仍会出现 **`/rtl-agent-team:…`** 形式的技能引用（来源自 Skill 文案）；在 Cursor 中请通过 **命令面板 / Skills / Agent** 等你所使用的入口触发等价工作流（具体名称以 Cursor 客户端为准）。

---

## 故障排除

| 现象 | 建议 |
|------|------|
| `sync_cursor_pack.sh` 报错缺少 python3/rsync | 安装依赖后重试 |
| 插件加载后无 SessionStart 路由上下文 | 确认用户工程根下存在 `.rat/` 或 `.rtl-agent-team/` 标记目录 |
| hooks 未触发 | 确认工作区已信任；检查 Cursor 版本是否支持 Plugins/hooks |

---

## 许可与更多信息

与主 README 相同：MIT License。完整英文文档见 [README.md](./README.md)。
