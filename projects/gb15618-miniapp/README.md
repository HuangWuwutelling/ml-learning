# GB 15618 农用地重金属评价小程序

微信云开发小程序，按 GB 15618-2018《土壤环境质量 农用地土壤污染风险管控标准（试行）》评价农用地土壤重金属污染风险。

## 功能

- **单点评价**：选作物（水田/旱地/果园）+ pH 滑块 + 输入 8 种重金属浓度 → 评价风险等级
- **批量评价**：上传 Excel（含多个点位）→ 逐点评价 + 汇总 + 错误报告
- **CSV 导出**：单点结果 + 批量汇总都能导出

## 评价标准

GB 15618-2018（2018-06-22 发布，2018-08-01 实施）
- 表 1 农用地土壤污染风险筛选值（8 金属 × 4 pH 档 × 多作物分类）
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

## 部署步骤（测试号）

### 1. 准备微信开发者工具

- 下载安装微信开发者工具
- 用微信扫码登录

### 2. 创建测试项目

- 微信开发者工具 → 新建小程序
- 项目目录：`projects/gb15618-miniapp/miniprogram/`
- AppID：选「测试号」（无需注册）
- 后端服务：勾选「微信云开发」

### 3. 创建云开发环境

- 工具栏点击「云开发」按钮
- 开通云开发（首次需要）
- 创建新环境，记下**环境 ID**

### 4. 配置 app.js

修改 `miniprogram/app.js`：

```javascript
wx.cloud.init({
  env: '你的环境ID',  // 替换 your-env-id
  traceUser: true,
});
```

### 5. 上传云函数

在 `cloudfunctions/evaluate` 目录右键 → 「上传并部署：云端安装依赖」
（首次上传会让云端安装 wx-server-sdk）

同样上传 `cloudfunctions/parseExcel`（会安装 exceljs）

### 6. 真机调试

- 工具栏 → 预览 → 扫码
- 真机点开小程序
- 单点页：填一组数据（参考测试样例）→ 看结果
- 批量页：先下载模板（需先在云存储上传 template.xlsx），再上传一个 xlsx → 看汇总

### 7. 截图

3 个页面各截 1-2 张图，存到 `docs/screenshots/`（自己创建）：
- `single.png`：单点评价填表 + 结果
- `batch.png`：批量上传文件 + 汇总卡片
- `result.png`：风险等级大字 + Pi 列表

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