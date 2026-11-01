from django.urls import path, include

urlpatterns = [path('api/career-platform/', include('career_platform.urls')),
               path('api/resumes/', include('resumes.urls')),
               path('api/company-reviews/', include('company_reviews.urls'))]
