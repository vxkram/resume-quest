from django.urls import include, path, re_path

from analyzer import views

api = [
    path("config/", views.ConfigView.as_view(), name="config"),
    path("providers/", views.ProvidersView.as_view(), name="providers"),
    path("providers/<str:provider_id>/models/", views.ProviderModelsView.as_view(), name="provider-models"),
    path("analyses/", views.AnalysisListView.as_view(), name="analyses"),
    path("analyses/<uuid:pk>/", views.AnalysisDetailView.as_view(), name="analysis"),
    path("analyses/<uuid:pk>/quiz/", views.QuizCreateView.as_view(), name="quiz-create"),
    path("analyses/<uuid:pk>/interview/", views.InterviewView.as_view(), name="interview"),
    path("quizzes/<uuid:pk>/", views.QuizDetailView.as_view(), name="quiz"),
    path("quizzes/<uuid:pk>/submit/", views.QuizSubmitView.as_view(), name="quiz-submit"),
]

urlpatterns = [
    path("api/", include(api)),
    re_path(r"^(?!api/)(?P<path>.*)$", views.frontend, name="frontend"),
]
