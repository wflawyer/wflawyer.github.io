# wflawyery.github.io

## 裁判文书网每日爬取脚本

在 `scripts/wenshu_daily_crawler.py` 中提供了一个可配置的每日爬取程序，用于拉取中国裁判文书网最新案例并保存为 JSON。由于该站点有反爬策略，需要你在配置文件中补充 Cookie、查询参数或其他鉴权信息。

### 使用方式

1. 安装依赖：
   ```bash
   pip install requests
   ```
2. 生成配置并运行一次：
   ```bash
   python scripts/wenshu_daily_crawler.py --once
   ```
   首次运行会生成 `crawler_config.json`，请根据实际情况更新请求参数。
3. 按每日定时运行（默认 02:00）：
   ```bash
   python scripts/wenshu_daily_crawler.py --time 02:00
   ```

### 输出说明

爬取结果会写入 `data/cases-YYYY-MM-DD.json`，同时更新 `data/state.json` 记录最近一次执行情况。
