# DAX 度量值

在 Power BI Desktop 中创建以下度量值（Modeling → New Measure）：

## 1. 总召回数
```dax
Total Recalls = COUNTROWS(fact_recall)
```

## 2. 影响产品数（数量合计）
```dax
Total Affected Qty = SUM(fact_recall[quantity])
```

## 3. 平均严重度得分
```dax
Avg Severity Score = 
VAR _high = CALCULATE(COUNTROWS(fact_recall), fact_recall[severity] = "high")
VAR _med = CALCULATE(COUNTROWS(fact_recall), fact_recall[severity] = "medium")
VAR _low = CALCULATE(COUNTROWS(fact_recall), fact_recall[severity] = "low")
RETURN DIVIDE(_high * 3 + _med * 2 + _low * 1, _high + _med + _low, 0)
```

## 4. CAPA 及时关闭率
```dax
CAPA On-Time Close Rate = 
VAR _closed = CALCULATE(
    COUNTROWS(fact_capa),
    fact_capa[status] = "closed",
    fact_capa[target_close_date] >= fact_capa[opened_date]
)
VAR _total = CALCULATE(
    COUNTROWS(fact_capa),
    fact_capa[status] = "closed"
)
RETURN DIVIDE(_closed, _total, 0)
```

## 5. 估计损失金额（万元）
```dax
Estimated Loss (Wan CNY) = SUM(fact_recall[estimated_cost_wan])
```

## 6. 上月环比（辅助）
```dax
Recall MoM Growth = 
VAR _current = [Total Recalls]
VAR _last = CALCULATE([Total Recalls], DATEADD('fact_recall'[recall_date].[Date], -1, MONTH))
RETURN DIVIDE(_current - _last, _last, 0)
```

## 6 页报告布局

### Page 1: 召回趋势总览
- 顶部：KPI Card × 4（总召回数 / 影响产品数 / 平均严重度 / 估计损失）
- 中部：Line chart（召回数按月份 + 缺陷类型）
- 底部：Slicer（省份、严重度、年度）

### Page 2: 区域分布（粤湘）
- 左侧：Map（广东省 + 湖南省 city 标注）
- 右上：Bar chart（按城市排序召回数 Top 10）
- 右下：Pie chart（缺陷类型分布）

### Page 3: CAPA 跟踪
- 左侧：Funnel（CAPA 状态从 draft → pending → effective → closed）
- 右上：Bar chart（按 responsible_engineer 关闭数）
- 右下：Scatter（target_close_date vs effectiveness_score）
