from django.urls import path
from api.resume_upload_view import ResumeUploadView
from api.summary_view import SummaryView
from api.questions_view import QuestionsView 
from api.answers_view import SaveAnswersView

urlpatterns = [
    path('upload/', ResumeUploadView.as_view(), name='resume-upload'),
    path('upload/summary/<str:file_name>/', SummaryView.as_view(), name='summary'),
    path('upload/questions/<str:file_name>/', QuestionsView.as_view(), name='questions'),
    path('upload/save-answers/<str:file_name>/', SaveAnswersView.as_view(), name='save-answers'),
]
