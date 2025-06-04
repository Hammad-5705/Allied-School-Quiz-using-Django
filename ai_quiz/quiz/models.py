from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    image = models.ImageField(upload_to='question_images/')
    is_ai = models.BooleanField()  # True if AI-generated
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"Question {self.id}"

class StudentAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.BooleanField()  # True = answered AI
    is_correct = models.BooleanField()

class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)