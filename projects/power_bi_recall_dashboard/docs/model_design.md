# Power BI 数据模型

## 星型 Schema
```
fact_recall (recall_events.csv)        dim_mfg (manufacturers.csv)
├── recall_id (PK)                     ├── mfg_id (PK)
├── recall_date                        ├── name
├── mfg_id ──────────────────────►     ├── province
├── product_name                       ├── city
├── product_brand                      ├── uscc_code
├── product_category                   └── registered_capital_wan
├── defect_type
├── severity                           fact_capa (capa_actions.csv)
├── quantity                           ├── capa_id (PK)
├── remedy                             ├── recall_id ──► fact_recall
├── estimated_cost_wan                 ├── opened_date
└── source_type                        ├── target_close_date
                                       ├── status
                                       ├── effectiveness_score
                                       └── responsible_engineer
```

## 关系
- dim_mfg[1] ──< fact_recall[*]   单向（dim_mfg → fact_recall）
- fact_recall[1] ──< fact_capa[*]  单向（fact_recall → fact_capa）
- 两关系均激活「交叉筛选方向：单向」

## 时间维度
- 不建 dim_date 表；用 Power BI 内建「自动日期/时间」功能
- 启用：File → Options → Time intelligence → 勾选
