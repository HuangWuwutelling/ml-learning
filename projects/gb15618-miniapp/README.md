# GB 15618 农用地重金属评价小程序

微信云开发小程序，按 GB 15618-2018《土壤环境质量 农用地土壤污染风险管控标准（试行）》评价农用地土壤重金属污染风险。

## 功能

- **单点评价**：选土地类型（水田/旱地/果园）+ pH 滑块 + 输入 1~8 种重金属浓度 → 评价风险等级
- **批量评价**：上传 Excel（含多个点位，每行 1~8 种重金属）→ 逐点评价 + 汇总 + 错误报告
- **CSV 导出**：单点结果 + 批量汇总都能导出

## 评价标准

GB 15618-2018（2018-06-22 发布，2018-08-01 实施）
- 表 1 农用地土壤污染风险筛选值（8 金属 × 4 pH 档 × 3 土地类型）
- 表 3 农用地土壤污染风险管制值（5 金属 × 4 pH 档）

**风险等级判定**（单因子指数法）：
- max(Pi) ≤ 1 → 优先保护类（绿）
- max(Pi) > 1 且 max(实测/管制值) ≤ 1 → 安全利用类（黄）
- max(实测/管制值) > 1 → 严格管控类（红）

**注意**：Cu/Ni/Zn 没有管制值（标准未给定），因此这 3 个金属永远不会被判"严格管控类"。

## 技术栈

- 微信云开发（云函数 + 云数据库 + 云存储）
- 原生小程序前端（WXML/WXSS/JS）
- `exceljs` 解析 Excel（云函数内）

## 项目结构

```
gb15618-miniapp/
├── miniprogram/                # 小程序前端
│   ├── pages/
│   │   ├── single/             # 单点评价页
│   │   ├── batch/              # 批量上传页
│   │   └── result/             # 结果展示页
│   ├── app.js                  # 全局入口（含云开发 init）
│   ├── app.json                # pages 列表 + tabBar
│   ├── app.wxss
│   ├── sitemap.json
│   └── project.config.json
├── cloudfunctions/             # 云函数
│   ├── evaluate/               # 单点评价
│   │   ├── index.js
│   │   ├── gb15618_limits.js   # 限额表副本（与 data/ 同步）
│   │   └── package.json
│   └── parseExcel/             # Excel 批量评价
│       ├── index.js
│       ├── gb15618_limits.js
│       └── package.json
├── data/
│   ├── gb15618_limits.js       # 限额表（CommonJS）— 规范源
│   └── gb15618_limits_research.md   # 限值表研究记录 + 数据来源
├── tests/
│   ├── gen_test_xlsx.js        # 生成测试 xlsx（10 行混合风险等级）
│   ├── test_input.xlsx         # 测试用 xlsx
│   └── verify.js               # 本地集成验证
└── README.md
```

## 部署步骤（正式号）

**完整操作清单 + 已知踩坑点**：[`docs/DEPLOY.md`](./docs/DEPLOY.md)（含 3 个真机测试场景 + 4 个截图要求）。

> ⚠️ **必须用正式号，不能用测试号**：本项目用微信云开发，测试号 AppID 看不到"后端服务"选项。个人主体注册免费，10 分钟搞定，且后续可上线发布（与 W5 路线对齐）。

### 1. 申请正式号（10 分钟）

```
1. 浏览器访问 https://mp.weixin.qq.com/wxopen/waregister?action=step1
2. 选账号类型 = "小程序"
3. 填未注册过公众平台的邮箱 + 密码
4. 邮箱点激活链接
5. 主体类型选"个人"（姓名 + 身份证 + 微信扫码）
6. 后台 → 设置 → 开发设置 → 复制 AppID
7. 把 AppID 填到 miniprogram/project.config.json 的 appid 字段
```

### 2. 准备微信开发者工具

- 下载安装微信开发者工具
- 用**同一个微信号**扫码登录
- 项目设置 → 本地设置 → 勾选「不校验合法域名」（否则云函数被拦截）

### 3. 导入项目

- 微信开发者工具 → 导入项目
- 项目目录：`projects/gb15618-miniapp/miniprogram/`
- AppID：填入第 1 步获得的正式号 AppID
- 项目名称：瓦力的土壤限值速查
- 后端服务：勾选「微信云开发」

### 4. 创建云开发环境

- 工具栏点击「云开发」按钮
- 开通云开发（首次需要）
- 创建新环境，记下**环境 ID**
- 限制：每位开发者最多 2 个免费云环境

### 5. 配置 app.js

修改 `miniprogram/app.js`：

```javascript
wx.cloud.init({
  env: '你的环境ID',  // 替换 your-env-id
  traceUser: true,
});
```

### 6. 上传云函数

在 `cloudfunctions/evaluate` 目录右键 → 「上传并部署：云端安装依赖」
（首次上传会让云端安装 wx-server-sdk）

同样上传 `cloudfunctions/parseExcel`（会安装 exceljs）

### 7. 真机调试

- 工具栏 → 预览 → 扫码
- 真机点开小程序（微信右上角 ··· → 打开调试，跳过域名校验）
- 单点页：填一组数据（参考测试样例）→ 看结果
- 批量页：先下载模板（需先在云存储上传 template.xlsx），再上传一个 xlsx → 看汇总

### 8. 截图 + 提交审核（截图后立即可发文章）

3 个页面各截 1-2 张图，存到 `docs/screenshots/`（自己创建）：
- `single.png`：单点评价填表 + 结果
- `batch.png`：批量上传文件 + 汇总卡片
- `result.png`：风险等级大字 + Pi 列表

**截图完成后** → 工具栏"上传"按钮 → 后台版本管理 → 提交审核（1～7 天）→ 审核通过后手动"发布"。

文章 14/15/16 不需要等审核，截图后立即可发。

## 本地验证

```bash
cd projects/gb15618-miniapp
node tests/gen_test_xlsx.js   # 生成测试 xlsx
node tests/verify.js          # 跑集成验证
```

预期输出：10 行成功（4 优先保护 / 4 安全利用 / 2 严格管控）+ 2 行错误。

## 部署状态

- [x] 单点评价
- [x] 批量评价
- [x] Excel 上传
- [x] CSV 导出
- [ ] 地图可视化（规划中，env/16 第 6 节扩展方向）
- [ ] GB 36600（建设用地标准）

## 数据来源

GB 15618-2018 表 1（风险筛选值）+ 表 3（风险管制值）
详细记录：`data/gb15618_limits_research.md`
数值文件：`articles/env/GB15618-2018重金属标准限值.xlsx`

## 配套文章

发完后会在以下文章中引用本项目：
- env/14《一块农用地到底算不算污染？GB 15618-2018 的判定逻辑》
- env/15《把 GB 15618 装进口袋：微信云开发做一个农用地评价小程序》
- env/16《从一块农用地到一份报表：GB 15618 评价小程序使用指南》

## 更新日志

### 2026-07-31

**字段重命名：**
- `crop` → `landType`（更符合 GB 15618-2018 原文"土地利用分类"术语）
- 涉及 8 个文件：数据规范源、两个云函数、3 个前端页面、`lib/csv.js`、3 个测试
- 数据规范源保留 `CROPS` 别名（向后兼容）
- **部署影响**：重新部署云函数 + 用新版 `gen_test_xlsx.js` 重新生成上传到云存储的 Excel 模板

**支持 1+ 种重金属评价（之前必须填 8 种）：**

- **前端**（`single.js`）：跳过空值，0 金属提示"请至少输入 1 种重金属"
- **云函数**（`evaluate`）：拒绝未知金属 key（`{ Ag: 0.1 }` → `unknown metal: Ag`），至少 1 种金属，返回新增 `providedCount` 字段
- **云函数**（`parseExcel`）：Excel 批量同样支持 1+ 金属，拒绝未识别列
- **结果页**（`result.js`）：保护 `maxPi` undefined（单金属时无 max 含义）
- **evaluate 函数**：单金属时返回不含 `maxPi`/`maxPiControl` 字段（避免歧义）

**测试**（`tests/`）：
- `verify.js`（集成验证）：✅ 7/7 断言通过
- `test_evaluate_validate.js`（云函数校验）：✅ 17/17 通过
- `test_csv_format.js`（CSV 序列化）：✅ 34/34 通过
- 新增覆盖场景：单 Cd 评价、单 Cu 评价、未知金属 key 拒绝、空 metals 拒绝

**踩坑提醒**：
- 旧的 `tests/test_input.xlsx` 含 `crop` 列头，已重新生成
- 旧的云存储 `gb15618_template.xlsx` 需替换为新版（否则用户下载后表头是 `crop`，上传会全部报"landType 缺失或非法"）
- 重新部署 `cloudfunctions/evaluate` 和 `cloudfunctions/parseExcel` 两个云函数