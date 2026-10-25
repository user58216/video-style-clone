# 部署为软件启动动画（boot-deploy）

将产出的 MP4 接入 DragonCodexBoot 类启动器（播放启动视频后无缝衔接真实软件窗口）。

## 目录
1. [前提与文件布局](#前提与文件布局)
2. [launcher.json 参数语义](#launcherjson-参数语义)
3. [时间轴适配公式](#时间轴适配公式)
4. [部署与验证步骤](#部署与验证步骤)
5. [入口接管与回滚](#入口接管与回滚)

## 前提与文件布局

启动器目录（示例 `D:\TeleAgent输出\TeleAgent启动器\`）：

```
TeleAgentBoot.exe          # 启动器主程序（支持 --self-test）
launcher.json              # 配置
media/startup.mp4          # 启动视频（部署目标）
src/TeleAgentBoot.cs       # 源码（几何按 1920x1080 硬编码 fit，产出视频须为 1920x1080）
```

## launcher.json 参数语义

| 参数 | 含义 |
|---|---|
| `Video` | 视频相对路径（`media/startup.mp4`） |
| `AppLaunch` | 动画结束后要启动/前置的真实软件 exe |
| `HoldAt` | 播放到该秒数时若目标软件窗口未就绪，暂停视频等待（显示"正在启动… Esc跳过"）；窗口就绪后续播 |
| `TransitionStart/End` | 窗口就绪后，真实窗口缩略图从视频中对应矩形位置淡入放大到全屏的时间段 |
| `ScreenFrames` | 过渡矩形的比例坐标轨迹（Time/X/Y/Width/Height，0~1），起点应对准视频结尾主体图形的位置 |
| `PlayerWidth/Height` | 全屏播放窗口物理像素（如 2560x1440） |
| `MaxWaitSeconds` | 等待软件窗口的最长秒数（校验要求 >=10） |
| `Volume` | 音量（无声视频保留 1 即可） |

校验规则（源码内建）：`HoldAt > 0`、`TransitionStart > HoldAt`、`TransitionEnd > TransitionStart`、`MaxWaitSeconds >= 10`。

## 时间轴适配公式

设视频总时长 `T`（如 20.0s），结尾主体图形（如神经网络球）中心比例坐标 `(cx, cy)`、占比 `(w, h)`：

```
HoldAt          ≈ T - 3.0        （画面稳定适合定格的阶段）
TransitionStart ≈ T - 1.3
TransitionEnd   ≈ T - 0.3
ScreenFrames:
  [T-1.35]  主体矩形略放大（如 cx=0.5 → X=cx-w/2, Y=cy-h/2）
  [T-0.95]  中间过渡（约 70% 屏幅）
  [T-0.45]  全屏 (0,0,1,1)
  [T-0.30]  全屏 (0,0,1,1)
```

20s 案例（球心 960,470 → 比例 cx=0.5, cy=0.435）：
`HoldAt=17.0, TS=18.7, TE=19.7`；ScreenFrames `(18.65, 0.30,0.21,0.40,0.48) → (19.05, 0.15,0.11,0.70,0.78) → (19.55, 全屏) → (19.7, 全屏)`。

## 部署与验证步骤

```powershell
# 1. 部署视频
Copy-Item "<成品.mp4>" "<启动器目录>\media\startup.mp4" -Force

# 2. 修改 launcher.json（HoldAt/TransitionStart/TransitionEnd/ScreenFrames）

# 3. 无界面自检（校验配置+视频存在+几何用例，不打开任何窗口）
Start-Process "<启动器目录>\TeleAgentBoot.exe" -ArgumentList "--self-test" `
  -WorkingDirectory "<启动器目录>" -WindowStyle Hidden -PassThru -Wait
Get-Content "<启动器目录>\qa\self-test.json"   # 期望 {"ok":true,...}
```

注意：不要为验证而实际运行启动器主程序——它会全屏播放 20 秒并前置目标软件，干扰当前会话。

## 入口接管与回滚

接管（以开始菜单 + 桌面快捷方式为例，WScript.Shell）：

```powershell
$sh = New-Object -ComObject WScript.Shell
$lnk = $sh.CreateShortcut("$env:USERPROFILE\Desktop\TeleAgent.lnk")
$lnk.TargetPath = "<启动器目录>\TeleAgentBoot.exe"
$lnk.WorkingDirectory = "<启动器目录>"
$lnk.IconLocation = "<真实软件exe>,0"    # 保留官方图标外观
$lnk.Save()
```

回滚：把快捷方式 TargetPath 改回真实软件 exe；配置层面修改前先备份 `launcher.json` 为 `launcher.json.bak-<日期>`。
