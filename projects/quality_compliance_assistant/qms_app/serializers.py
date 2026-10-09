from rest_framework import serializers
from .models import Manufacturer, Product, Recall, Capa, Complaint

class RecallSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model = Recall
        fields = ['id', 'product', 'product_name', 'recall_id_external', 'source_type',
                  'source_url', 'recall_date', 'quantity', 'defect_description',
                  'consequence', 'remedy_method', 'status']

class CapaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capa
        fields = '__all__'

class ComplaintInputSerializer(serializers.Serializer):
    text = serializers.CharField()

class ComplaintOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['id', 'text', 'severity_predicted', 'severity_confidence',
                  'similar_recall', 'capa_draft', 'created_at']
