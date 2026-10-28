---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '2b445792-d0f8-4333-a722-6f720fc4527a'
  PropagateID: '2b445792-d0f8-4333-a722-6f720fc4527a'
  ReservedCode1: 'af801971-23ed-4c3f-9748-135100302369'
  ReservedCode2: 'af801971-23ed-4c3f-9748-135100302369'
---

# 部署为软件启动动画（boot-deploy，通用指南）

将产出的 MP4 接入"播放启动视频 → 无缝衔接到真实软件窗口"的启动动画系统。本文先讲通用原理（适用于任何此类启动器/自研程序），再以 Windows 启动器为例给完整案例，最后给出其他技术栈的思路。

## 目录
1. [通用原理：启动动画系统三要素](#通用原理)
2. [时间轴适配公式](#时间轴适配公式)
3. [完整案例：Windows 启动器](#完整案例windows-启动器)
4. [其他技术栈思路](#其他技术栈思路)
5. [回滚](#回滚)

## 通用原理

任何"启动动画"系统由三要素构成，部署就是为你的视频定制这三要素：

1. **全屏视频播放器**：以物理像素全屏（如 2560×1440）等比播放视频（推荐视频规格 1920×1080，16:9，H.264/yuv420p）；
2. **衔接参数**：定义"视频何时等待软件就绪、何时开始过渡到真实窗口"；
   - `HoldAt`：播放到该秒数时若软件窗口未就绪，暂停等待（此时画面应是适合定格的稳定帧）；
   - `TransitionStart/End`：真实窗口从视频中某个矩形区域淡入放大到全屏的时间段；
3. **窗口过渡轨迹**：过渡期间真实窗口的位置矩形序列（比例坐标 0~1），起点应**对准视频结尾主体图形的位置**——视觉上就像"视频里的图形绽放成软件界面"。

## 时间轴适配公式

设视频总时长 `T`，结尾主体图形（如 logo/图标）中心比例坐标 `(cx, cy)`、约占屏比例 `(w, h)`：

```
HoldAt          ≈ T - 3.5        （选画面稳定的段落；若该处画面过暗可前移）
TransitionStart ≈ T - 1.3
TransitionEnd   ≈ T - 0.3
ScreenFrames（比例矩形，中心始终对准主体图形）:
  [T-1.33]  X=cx-w/2-0.06, Y=cy-h/2-0.04, W=w+0.12, H=h+0.08   （略大于主体）
  [T-0.93]  中间过渡（约 70% 屏幅，中心不变）
  [T-0.43]  全屏 (0, 0, 1, 1)
  [T-0.30]  全屏 (0, 0, 1, 1)
```

约束：`HoldAt > 0`、`TransitionStart > HoldAt`、`TransitionEnd > TransitionStart`。

## 完整案例：Windows 启动器

以开源的 DragonCodexBoot 类 Windows 启动器为例（播放 MP4 后经 DWM 缩略图把真实软件窗口从视频矩形位置放大到全屏）。

目录布局：

```
launcher/
├── LauncherBoot.exe     # 启动器主程序（支持 --self-test 无界面自检）
├── launcher.json        # 配置
├── media/startup.mp4    # 启动视频（部署目标）
└── src/LauncherBoot.cs  # 源码（几何按 1920x1080 硬编码 fit）
```

`launcher.json` 关键字段：

| 字段 | 含义 |
|---|---|
| `Video` | 视频相对路径 |
| `AppLaunch` | 动画结束后启动/前置的真实软件 exe |
| `ProcessPathContains` / `ProcessNames` | 目标软件进程识别 |
| `HoldAt` / `TransitionStart` / `TransitionEnd` | 衔接参数（秒） |
| `ScreenFrames` | 过渡矩形轨迹 `[{Time,X,Y,Width,Height}, ...]`（比例 0~1） |
| `PlayerWidth/Height` | 全屏播放窗口物理像素 |
| `MaxWaitSeconds` | 等待软件窗口上限（≥10） |
| `Volume` | 音量（无声视频保留 1） |

部署步骤：

```powershell
# 1. 部署视频
Copy-Item "final.mp4" "launcher\media\startup.mp4" -Force

# 2. 按公式修改 launcher.json 的 HoldAt/TransitionStart/TransitionEnd/ScreenFrames
#    （修改前备份：Copy-Item launcher.json launcher.json.bak-<日期>）

# 3. 无界面自检（校验配置+视频存在+几何用例，不打开任何窗口）
Start-Process "launcher\LauncherBoot.exe" -ArgumentList "--self-test" `
  -WorkingDirectory "launcher" -WindowStyle Hidden -PassThru -Wait
Get-Content "launcher\qa\self-test.json"   # 期望 {"ok":true,...}

# 4. 接管入口：把桌面/开始菜单快捷方式指向启动器，图标保留官方外观
$sh = New-Object -ComObject WScript.Shell
$lnk = $sh.CreateShortcut("$env:USERPROFILE\Desktop\MyApp.lnk")
$lnk.TargetPath = "launcher\LauncherBoot.exe"
$lnk.WorkingDirectory = "launcher"
$lnk.IconLocation = "真实软件.exe,0"
$lnk.Save()
```

> 提示：不要为验证而实际运行启动器主程序——它会全屏播放并前置目标软件，干扰当前会话。

20 秒实战案例（结尾主体为画面中心图标，cx=0.5, cy=0.435）：
`HoldAt=17.0, TS=18.7, TE=19.7`；ScreenFrames `(18.65, .30,.21,.40,.48) → (19.05, .15,.11,.70,.78) → (19.55, 全屏) → (19.7, 全屏)`。

12.33 秒实战案例（原片 10.33s + 图标段 2s，画面中心偏上 cx=0.5, cy=0.46）：
`HoldAt=8.6（选原片对立构图帧，避免全黑等待）, TS=11.0, TE=12.0`；ScreenFrames `(11.0, .28,.20,.44,.52) → (11.4, .13,.10,.74,.80) → (11.9, 全屏) → (12.0, 全屏)`。

## 其他技术栈思路

| 技术栈 | 实现思路 |
|---|---|
| Electron 应用 | 主窗口先加载全屏 `<video>` 播放启动动画，`timeupdate` 监听到过渡点后创建/显示主窗口并做 CSS transform 从主体矩形放大到全屏，结束后移除视频层 |
| Web / 活动页 | 同上思路：video 播放 + getBoundingClientRect 驱动主容器 scale 过渡 |
| Unity / 游戏引擎 | Splash Scene 播放 VideoPlayer，协程控制过渡 UI Rect 到目标分辨率 |
| macOS | 无全局登录动画钩子，退而求其次做应用内 Launch/Splash 窗口（NSWindow + AVPlayer，同三要素） |
| 自研 Win32/WPF | 参考案例源码思路：DWM 缩略图（DwmRegisterThumbnail）把真实窗口映射到播放器内矩形，逐帧更新 Destination 属性 |

通用检查清单：视频规格统一（1080p/30fps/yuv420p）→ 主体图形位置确认 → 三参数按公式计算 → 自检/试跑 → 入口接管 + 回滚备份。

## 回滚

- 配置：还原 `launcher.json.bak-<日期>`；
- 入口：把快捷方式 TargetPath 改回真实软件 exe；
- 视频：保留上一版 `startup.mp4` 副本可直接替换回退。
