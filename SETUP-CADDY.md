# Caddy 反向代理安裝指南

## 架構說明

```
使用者
  ↓ HTTPS (kevinl-ai.com)
Cloudflare Tunnel (cloudflared)
  ↓ HTTP
Windows Caddy (:80 / :443)
  ├→ kevinl-ai.com         → 靜態 HTML (Hub)
  ├→ idoctor.kevinl-ai.com → localhost:8080 (Defect iDoctor / WSL)
  └→ openclaw.kevinl-ai.com → localhost:9000 (OpenClaw / WSL)
```

## Step 1：把 Hub 靜態頁放到 Windows 主機

在 Windows 主機建立資料夾：
```
C:\caddy\hub\
```

把 Hub 的靜態 HTML 檔案放進去：
- `C:\caddy\hub\index.html`
- 其他子目錄（`openclaw/`、`defect-idoctor/` 等）

## Step 2：安裝 Caddy

### Windows（建議）

1. 下載：https://caddyserver.com/download
   - 選擇平台：Windows (amd64)
   - 外掛：不需要（全用內建功能）

2. 解壓縮，把 `caddy.exe` 放到 `C:\caddy\`

3. 把這個 repo 裡的 `Caddyfile` 複製到 `C:\caddy\`

4. 建立資料夾：
   ```
   C:\caddy\hub\
   C:\caddy\logs\
   ```

5. 測試執行：
   ```
   cd C:\caddy
   .\caddy run
   ```

6. 看到 `{"level":"info","msg":"serving initial configuration"}` 表示成功

### 設定開機自動啟動

建議用 **NSSM**（Non-Sucking Service Manager）：

1. 下載 NSSM：https://nssm.cc/download
2. 解壓縮到 `C:\nssm\`
3. 以系統管理員身份開 PowerShell：
   ```
   C:\nssm\win64\nssm.exe install Caddy "C:\caddy\caddy.exe" "run --config C:\caddy\Caddyfile"
   ```
4. 啟動服務：
   ```
   net start Caddy
   ```

## Step 3：修改 Cloudflare Tunnel 目的地

現在的 Tunnel 直接打到 WSL 的 port，需要改成打到 Windows Caddy。

### 方法：在 Cloudflare Zero Trust 設定

1. 前往 https://one.dash.cloudflare.com
2. Networks → Tunnels → 點選 `kevinl-ai` tunnel
3. Edit → Public Hostname

把目前的路由刪除，改成：

| Subdomain | Service | URL |
|---|---|---|
| (root) | HTTP | http://localhost:80 |
| idoctor | HTTP | http://localhost:80 |
| openclaw | HTTP | http://localhost:80 |

**注意：** 路由全部打到 `localhost:80`（Caddy 的 HTTP port），由 Caddy 根據 subdomain 路由分發。

或者用指令更新 Tunnel：

```bash
# 在 WSL 執行
cloudflared tunnel update 9beac328-b15b-49ef-973a-933ea3904ec8 \
  --ingress-rules="
    - hostname: kevinl-ai.com
      service: http://localhost:80
    - hostname: '*.kevinl-ai.com'
      service: http://localhost:80
    - service: http_status:404
  "
cloudflared tunnel run 9beac328-b15b-49ef-973a-933ea3904ec8
```

## Step 4：在 Cloudflare DNS 加入子網域

1. 前往 https://dash.cloudflare.com → kevinl-ai.com
2. DNS → Records → 新增：

| Type | Name | Target | Proxy |
|---|---|---|---|
| CNAME | idoctor | kevinl-ai.com | 橙色（已代理）|
| CNAME | openclaw | kevinl-ai.com | 橙色（已代理）|

## Step 5：確認 OpenClaw port

```bash
# 在 WSL 執行，把 OpenClaw 改成 port 9000
openclaw config set gateway.port 9000
openclaw gateway restart
```

確認有起來：
```bash
openclaw gateway status
```

## Step 6：啟動 Hub HTTP 服務

Hub 的靜態 HTML 需要一個 HTTP 服務（不是 Caddy 自己服務，而是單獨的 HTTP server）：

```powershell
# 在 Windows PowerShell
cd C:\caddy\hub
python -m http.server 5000
```

或用 Caddy 的 `file_server` 但需要把 Hub 當成一個「服務」——建議直接用 Python simple HTTP server 或把 Hub 的 index.html 放到 Caddy 的 root。

## 驗證

全部完成後測試：

```
idoctor.kevinl-ai.com     → Defect iDoctor
openclaw.kevinl-ai.com   → OpenClaw Control UI
kevinl-ai.com            → Hub 入口
```

## 常見問題

**Q：Caddy 不知道 subdomain？**
Caddy 會根據 Host header 自動路由，不需要另外設定 TLS cert。

**Q：Cloudflare Tunnel 怎麼選 HTTP vs TCP？**
選擇 HTTP 模式，讓 Cloudflare 處理 HTTPS 終止，Caddy 只需要收 HTTP。

**Q：Hub 的靜態頁一直要另外啟 HTTP server？**
可以。把 Hub 改成 Caddy 直接服務（把 `C:\caddy\hub` 設成 Caddy 的 root），不需要額外的 HTTP server。Caddy 的 `file_server` 會直接服務靜態檔案。
