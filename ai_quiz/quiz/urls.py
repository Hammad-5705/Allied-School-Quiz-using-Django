from django.urls import path
from . import views

urlpatterns = [
    path('', views.start_quiz, name='start_quiz'),
    path('question/<int:index>/', views.question_view, name='question'),
    path('results/', views.results_view, name='results'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('create-student/', views.create_student, name='create_student'),

]