from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Recall, Capa, Complaint
from .serializers import (RecallSerializer, CapaSerializer,
                          ComplaintInputSerializer)
from agent.graph import run as agent_run
from agent.tools import assess_severity, search_recall_history, draft_capa

class RecallViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Recall.objects.select_related('product', 'product__manufacturer').all()
    serializer_class = RecallSerializer
    filterset_fields = ['source_type', 'status', 'product__category']
    search_fields = ['product__name', 'product__brand', 'defect_description']

class CapaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Capa.objects.select_related('recall').all()
    serializer_class = CapaSerializer

@api_view(['POST'])
def agent_chat(request):
    msg = request.data.get('message', '')
    thread_id = request.data.get('thread_id', 'default')
    if not msg:
        return Response({'error': 'message required'}, status=400)
    reply = agent_run(msg, thread_id=thread_id)
    return Response({'reply': reply, 'thread_id': thread_id})

@api_view(['POST'])
def complaint_analyze(request):
    s = ComplaintInputSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    text = s.validated_data['text']
    severity_info = assess_severity.invoke({'complaint_text': text})
    similar = search_recall_history.invoke({'query': text, 'top_k': 3})
    capa = draft_capa.invoke({'complaint_summary': text})
    c = Complaint.objects.create(text=text,
                                  severity_predicted=severity_info['severity'],
                                  severity_confidence=severity_info['confidence'])
    return Response({
        'complaint_id': c.id,
        'severity': severity_info,
        'similar_recalls': similar,
        'capa_draft': capa,
    })
