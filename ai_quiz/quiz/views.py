from django.shortcuts import render, redirect
from .models import Question, StudentAnswer, Score
from .forms import AnswerForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django import forms
from django.shortcuts import render, redirect, get_object_or_404





@login_required
def start_quiz(request):
    # If student already took quiz, show result
    if Score.objects.filter(user=request.user).exists():
        return redirect('results')

    # AI-based question generation if no existing questions
    if Question.objects.count() < 10:
        generate_ai_questions()  # we'll write this next

    # Pick 10 questions at random
    questions = Question.objects.all().order_by('?')[:10]
    request.session['quiz_ids'] = [q.id for q in questions]
    request.session['user_answers'] = {}
    return redirect('question', index=0)



@login_required
def question_view(request, index):
    quiz_ids = request.session.get('quiz_ids', [])
    user_answers = request.session.get('user_answers', {})

    if index >= len(quiz_ids):
        return redirect('results')  # all questions answered

    question = get_object_or_404(Question, id=quiz_ids[index])

    if request.method == 'POST':
        user_answers[str(index)] = request.POST.get('answer')
        request.session['user_answers'] = user_answers

        # go to next question
        return redirect('question', index=index+1)

    return render(request, 'quiz/question.html', {
        'question': question,
        'index': index
    })

@login_required
def results_view(request):
    answers = StudentAnswer.objects.filter(user=request.user).order_by('-id')[:10]
    score = sum(a.is_correct for a in answers)
    Score.objects.create(user=request.user, score=score)
    return render(request, 'quiz/results.html', {'answers': answers, 'score': score})

@login_required
def leaderboard(request):
    scores = Score.objects.order_by('-score')
    return render(request, 'quiz/leaderboard.html', {'scores': scores})





# Form for creating student accounts
class StudentCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

# Only superusers can access
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
            return redirect('leaderboard')  # or any page you prefer
    else:
        form = StudentCreationForm()
    return render(request, 'quiz/create_student.html', {'form': form})


import random
from .models import Question
import os
from django.conf import settings
import urllib.request

def generate_ai_questions():
    if Question.objects.exists():
        return

    # Sample tech-themed images (mix of AI and real)
    sample_data = [
        ("https://generated.photos/vue-static/home/face-generator/landing/hero/1.jpg", True),
        ("https://images.unsplash.com/photo-1581093588401-9c01c4f0922d", False),
        ("https://image.pollinations.ai/prompt/AI%20generated%20drone%20city%20view", True),
        ("https://images.unsplash.com/photo-1581091215367-59e2a6f4db8c", False),
        ("https://image.pollinations.ai/prompt/AI%20generated%20robot%20factory", True),
        ("https://images.unsplash.com/photo-1581091870622-8f6e5c0fa93e", False),
        ("https://image.pollinations.ai/prompt/Futuristic%20cyberpunk%20server%20room", True),
        ("https://images.unsplash.com/photo-1573166364081-c411b1923bdb", False),
        ("https://image.pollinations.ai/prompt/AI%20generated%20smartphone%20chipset", True),
        ("https://images.unsplash.com/photo-1581092334557-e42e26b81007", False),
    ]

    media_path = os.path.join(settings.MEDIA_ROOT, 'questions')
    os.makedirs(media_path, exist_ok=True)

    for i, (url, is_ai) in enumerate(sample_data):
        filename = f"tech_question_{i}.jpg"
        local_path = os.path.join('questions', filename)
        full_path = os.path.join(settings.MEDIA_ROOT, local_path)

        try:
            urllib.request.urlretrieve(url, full_path)
        except:
            continue

        Question.objects.create(image=local_path, is_ai=is_ai)
