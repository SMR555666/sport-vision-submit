## 改动范围

<!-- 只勾选实际改过的，别全勾 -->

- [ ] `participant/pingpang/participant/`（乒乓球代码区）
- [ ] `participant/basketball/participant/`（篮球代码区）
- [ ] `tools/`、`docs/`、`docker/`、README（工程侧，与评测无关）
- [ ] 其他：<!-- 说明 -->

**没有**改 `core/`、`scripts/`、`run.py`、`run.sh`、`validate.py`、`integrity.py`、`run_all.sh`、`.integrity.json` 中任何一个 ← 这条必须确认

## 改了什么

<!-- 一两句话，说清动机和做法 -->

## 自测证据

<!-- 贴关键输出，不要只说「测过了」 -->

- `python tools/check_dataset.py participant`：
  ```
  粘贴输出
  ```
- `./tools/selftest.sh quick`（两任务各一条视频）：
  ```
  粘贴输出
  ```
- 全量联合自测退出码 / 单任务耗时：
  ```
  粘贴 run_status.json 里的耗时统计，或 run_all.sh 的退出码
  ```
- 主赛题本地 F1（按 0° / 45° / 90° 分开报，没有就说没有）：
- 附加题 IDF1 / MOTA（做了才填）：

## 性能影响

- 平均推理 FPS：改动前 → 改动后
- 显存峰值：
- 输出体积：

## 备注 / 风险

<!-- 已知问题、待办、需要别人复现的地方 -->
