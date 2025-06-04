from django.shortcuts import render, redirect
from .models import Question, StudentAnswer, Score
from .forms import AnswerForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
import random
import os
from django.conf import settings
import urllib.request
from urllib.error import URLError

@login_required
def start_quiz(request):
    if Score.objects.filter(user=request.user).exists():
        return redirect('results')

    if Question.objects.count() < 10:
        generate_ai_questions()

    questions = Question.objects.all().order_by('?')[:10]
    request.session['quiz_ids'] = [q.id for q in questions]
    request.session['user_answers'] = {}
    return redirect('question', index=0)


@login_required
def question_view(request, index):
    quiz_ids = request.session.get('quiz_ids', [])
    user_answers = request.session.get('user_answers', {})

    if index >= len(quiz_ids):
        return redirect('results')

    question = get_object_or_404(Question, id=quiz_ids[index])

    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.cleaned_data['answer']
            user_answers[str(question.id)] = answer  # Store by question ID
            request.session['user_answers'] = user_answers
            
            is_correct = (answer == question.is_ai)
            StudentAnswer.objects.create(
                user=request.user,
                question=question,
                answer=answer,
                is_correct=is_correct
            )
            
            # Redirect to next question or results
            next_index = index + 1
            if next_index < len(quiz_ids):
                return redirect('question', index=next_index)
            return redirect('results')
    else:
        form = AnswerForm()

    return render(request, 'quiz/question.html', {
        'question': question,
        'index': index,
        'form': form,
        'total_questions': len(quiz_ids),
        'image_url': question.image.url if question.image else ''
    })

@login_required
def results_view(request):
    answers = StudentAnswer.objects.filter(user=request.user).order_by('-id')[:10]
    score = sum(a.is_correct for a in answers)
    
    if Score.objects.filter(user=request.user).exists():
        score_obj = Score.objects.get(user=request.user)
        score_obj.score = score
        score_obj.save()
    else:
        Score.objects.create(user=request.user, score=score)
    
    return render(request, 'quiz/results.html', {
        'answers': answers,
        'score': score,
    })

@login_required
def leaderboard(request):
    scores = Score.objects.order_by('-score')
    return render(request, 'quiz/leaderboard.html', {'scores': scores})

class StudentCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

@user_passes_test(lambda u: u.is_superuser)
def create_student(request):
    if request.method == 'POST':
        form = StudentCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff = False
            user.is_superuser = False
            user.save()
            return redirect('leaderboard')
    else:
        form = StudentCreationForm()
    return render(request, 'quiz/create_student.html', {'form': form})

import requests
from django.core.files.base import ContentFile
from PIL import Image
import io

import requests
from io import BytesIO
from django.core.files import File
from PIL import Image
import os
from django.conf import settings

def generate_ai_questions():
    # Clear existing questions
    Question.objects.all().delete()
    
    # Create media directory if it doesn't exist
    media_path = os.path.join(settings.MEDIA_ROOT, 'question_images')
    os.makedirs(media_path, exist_ok=True)

    # Create a default image
    default_img_path = os.path.join(media_path, 'default.jpg')
    if not os.path.exists(default_img_path):
        img = Image.new('RGB', (600, 400), color='gray')
        img.save(default_img_path)

    # Updated question data with more reliable sources
    questions = [
        # AI-generated images
        ("https://thispersondoesnotexist.com", True, "AI-generated face with perfect symmetry"),
        ("https://image.pollinations.ai/prompt/robot", True, "AI robot with unrealistic features"),
        ("https://image.pollinations.ai/prompt/futuristic%20city", True, "AI city with repetitive patterns"),
        ("https://image.pollinations.ai/prompt/cyberpunk%20character", True, "AI character with unnatural lighting"),
        ("https://image.pollinations.ai/prompt/digital%20art", True, "AI art with perfect textures"),
        
        # Real images - using different sources
        ("https://picsum.photos/600/400?random=1", False, "Real portrait with natural imperfections"),
        ("https://picsum.photos/600/400?random=2", False, "Real city photo with natural lighting"),
        ("https://picsum.photos/600/400?random=3", False, "Real tech photo with authentic details"),
        ("https://picsum.photos/600/400?random=4", False, "Real office environment"),
        ("https://picsum.photos/600/400?random=5", False, "Real nature scene")
    ]

    for i, (url, is_ai, explanation) in enumerate(questions):
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            img.verify()
            img = Image.open(BytesIO(response.content))
            
            filename = f"question_{i}.jpg"
            filepath = os.path.join(media_path, filename)
            
            # Convert to RGB if needed (some PNGs might have alpha channel)
            if img.mode in ('RGBA', 'LA'):
                img = img.convert('RGB')
            
            img.save(filepath, format='JPEG', quality=85)
            
            Question.objects.create(
                image=f"question_images/{filename}",
                is_ai=is_ai,
                explanation=explanation
            )
        except Exception as e:
            print(f"Error with {url}: {e}")
            Question.objects.create(
                image="question_images/default.jpg",
                is_ai=is_ai,
                explanation=explanation
            )