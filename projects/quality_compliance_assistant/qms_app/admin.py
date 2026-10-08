from django.contrib import admin
from .models import Manufacturer, Product, DefectType, Recall, Capa, Complaint, AuditLog

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'uscc_code', 'created_at')
    search_fields = ('name', 'uscc_code')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'model', 'manufacturer', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'brand', 'model')

@admin.register(DefectType)
class DefectTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

@admin.register(Recall)
class RecallAdmin(admin.ModelAdmin):
    list_display = ('product', 'defect_type', 'source_type', 'recall_date', 'quantity', 'status')
    list_filter = ('source_type', 'status', 'recall_date')
    search_fields = ('product__name', 'product__brand', 'defect_description')
    date_hierarchy = 'recall_date'

@admin.register(Capa)
class CapaAdmin(admin.ModelAdmin):
    list_display = ('recall', 'status', 'action_who', 'target_date_when')
    list_filter = ('status',)

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'severity_predicted', 'severity_confidence', 'similar_recall', 'created_at')
    list_filter = ('severity_predicted',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'target_model', 'target_id')
    list_filter = ('action', 'target_model')
    readonly_fields = ('created_at', 'user', 'action', 'target_model', 'target_id', 'before_json', 'after_json')
