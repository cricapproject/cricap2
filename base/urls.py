from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='root'),  # ← Tambahkan ini
    path('home/', views.home, name='home'), 
    path('index.html', views.home, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('news/', views.news_view, name='news'),
    path('survey/', views.survey_views, name='survey'),
    path('dashboard-home/', views.dashboard_home_view, name='dashboard-home'),
    path('report/', views.report_views, name='report'),
    path('dashboard/user/', views.dashboard_home_user_view, name='dashboard-home-user'),
    path('report/user/', views.report_user_view, name='report_user'),
    path('map/', views.map_views, name='map'),
    path('survey-user/', views.survey_user_view, name='survey_user'),
    path('survey/survey_1/', views.survey_1_views, name='survey_1'),
    path('survey/survey_2/', views.survey_2_views, name='survey_2'),
    path('survey/survey_3/', views.survey_3_views, name='survey_3'),
    path("get-desa/<int:kecamatan_id>/", views.get_desa_by_kecamatan, name="get_desa_by_kecamatan"),
    path('survey/survey_4/', views.survey_4_views, name='survey_4'),
    path('rata-rata/', views.rata_rata_views, name='rata_rata_copy'),
    path('thankyou/', views.thankyou, name='thankyou'),
]