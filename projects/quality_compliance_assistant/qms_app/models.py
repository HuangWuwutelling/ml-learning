from django.db import models

class Manufacturer(models.Model):
    name = models.CharField(max_length=200)
    uscc_code = models.CharField('统一社会信用代码', max_length=20, unique=True)
    address = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '生产者'
        verbose_name_plural = '生产者'
    def __str__(self):
        return self.name

class Product(models.Model):
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=50, blank=True)  # 家电/电子/儿童用品/...
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '产品'
        verbose_name_plural = '产品'
    def __str__(self):
        return f'{self.brand} {self.name}'

class DefectType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = '缺陷类型'
        verbose_name_plural = '缺陷类型'
    def __str__(self):
        return self.name

class Recall(models.Model):
    SOURCE_CHOICES = [
        ('samrdprc_gg', 'samrdprc 公告'),
        ('samrdprc_news', 'samrdprc 新闻'),
        ('samr_zhdt', 'samr 主站'),
    ]
    STATUS_CHOICES = [
        ('active', '执行中'),
        ('completed', '已完成'),
        ('cancelled', '已撤销'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recalls')
    defect_type = models.ForeignKey(DefectType, on_delete=models.SET_NULL, null=True, blank=True)
    recall_id_external = models.CharField('外部公告编号', max_length=100, blank=True, db_index=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_url = models.TextField()
    raw_html_path = models.CharField(max_length=500, blank=True)
    recall_date = models.DateField()
    quantity = models.IntegerField(default=0)
    defect_description = models.TextField()
    consequence = models.TextField()
    remedy_method = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '召回事件'
        verbose_name_plural = '召回事件'
        indexes = [models.Index(fields=['source_type', 'recall_date'])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(source_type__in=['samrdprc_gg', 'samrdprc_news', 'samr_zhdt']),
                name='recall_source_type_valid',
            ),
        ]
    def __str__(self):
        return f'{self.product.name} @ {self.recall_date}'

class Capa(models.Model):
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待审'),
        ('effective', '生效'),
        ('closed', '关闭'),
    ]
    recall = models.ForeignKey(Recall, on_delete=models.CASCADE, related_name='capas')
    problem_what = models.TextField('问题描述')
    root_cause_why = models.TextField('根因分析', blank=True)
    action_who = models.CharField('负责人', max_length=100, blank=True)
    target_date_when = models.DateField('目标完成日期', null=True, blank=True)
    location_where = models.CharField('实施位置', max_length=200, blank=True)
    method_how = models.TextField('实施办法', blank=True)
    cost_howmuch = models.DecimalField('预算', max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    effectiveness_score = models.IntegerField(null=True, blank=True)  # 1-5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'CAPA 措施'
        verbose_name_plural = 'CAPA 措施'
    def __str__(self):
        return f'CAPA#{self.id} for {self.recall}'

class Complaint(models.Model):
    SEVERITY_CHOICES = [('high', '高'), ('medium', '中'), ('low', '低')]
    text = models.TextField()
    severity_predicted = models.CharField(max_length=10, choices=SEVERITY_CHOICES, blank=True)
    severity_confidence = models.FloatField(null=True, blank=True)
    similar_recall = models.ForeignKey(Recall, on_delete=models.SET_NULL, null=True, blank=True)
    capa_draft = models.ForeignKey(Capa, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_complaint')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '客户投诉'
        verbose_name_plural = '客户投诉'

class AuditLog(models.Model):
    ACTION_CHOICES = [('create', '创建'), ('update', '更新'), ('delete', '删除')]
    user = models.CharField(max_length=100, default='system')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    target_model = models.CharField(max_length=50)
    target_id = models.BigIntegerField()
    before_json = models.JSONField(null=True, blank=True)
    after_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'
        indexes = [models.Index(fields=['target_model', 'target_id'])]