import streamlit as st
import pandas as pd
import plotly.express as px
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qms_project.settings')
django.setup()
from qms_app.models import Recall, Capa, Complaint

st.set_page_config(page_title='QMS Dashboard', layout='wide')
st.title('QMS 质量管理 Dashboard')

tab1, tab2, tab3, tab4 = st.tabs(['总览', '召回趋势', '投诉分析', 'CAPA 跟踪'])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('总召回数', Recall.objects.count())
    c2.metric('执行中', Recall.objects.filter(status='active').count())
    c3.metric('总投诉数', Complaint.objects.count())
    c4.metric('CAPA 待审', Capa.objects.filter(status='pending').count())
    df = pd.DataFrame(Recall.objects.values('source_type', 'status'))
    if not df.empty:
        st.plotly_chart(px.histogram(df, x='source_type', color='status', barmode='group'),
                        use_container_width=True)

with tab2:
    df = pd.DataFrame(Recall.objects.values('recall_date', 'source_type', 'quantity'))
    if not df.empty:
        df['recall_date'] = pd.to_datetime(df['recall_date'])
        st.plotly_chart(px.line(df.groupby([df['recall_date'].dt.to_period('M'), 'source_type']).size().reset_index(name='count'),
                                x='recall_date', y='count', color='source_type'),
                        use_container_width=True)

with tab3:
    df = pd.DataFrame(Complaint.objects.values('severity_predicted', 'created_at'))
    if not df.empty:
        st.plotly_chart(px.pie(df, names='severity_predicted', title='投诉严重度分布'),
                        use_container_width=True)
        st.dataframe(Complaint.objects.all()[:50].values('text', 'severity_predicted', 'severity_confidence'))

with tab4:
    df = pd.DataFrame(Capa.objects.values('status', 'action_who'))
    if not df.empty:
        st.plotly_chart(px.histogram(df, x='status', color='action_who'),
                        use_container_width=True)