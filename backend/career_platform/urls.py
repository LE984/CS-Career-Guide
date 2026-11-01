from django.urls import path
from .views import catalog as c, evaluation as e, resume as r, rag, records as p

urlpatterns = [
    path('catalog/companies/', c.Companies.as_view()), path('catalog/jobs/', c.Jobs.as_view()),
    path('catalog/questions/', c.Questions.as_view()), path('catalog/imports/', c.Imports.as_view()),
    path('resume-analyses/', r.ResumeAnalyses.as_view()), path('resume-analyses/<uuid:pk>/', r.ResumeDetail.as_view()),
    path('resume-analyses/<uuid:pk>/apply/', r.ResumeApply.as_view()),
    path('questions/retrieve/', rag.Retrieve.as_view()),
    path('practice-sessions/', p.PracticeSessions.as_view()), path('practice-sessions/<uuid:pk>/', p.PracticeDetail.as_view()),
    path('practice-sessions/<uuid:pk>/answers/', rag.Answers.as_view()), path('practice-sessions/<uuid:pk>/finish/', p.PracticeFinish.as_view()),
    path('evaluation-runs/', e.EvaluationRuns.as_view()), path('evaluation-runs/<uuid:pk>/', e.EvaluationDetail.as_view()),
    path('evaluation-runs/<uuid:pk>/export/', e.EvaluationExport.as_view()),
]
