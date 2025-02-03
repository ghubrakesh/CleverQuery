import json

import google.generativeai as genai
import markdown

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .helpers import extract_text_from_pdf
from .models import Document, Query, Session

genai.configure(api_key="AIzaSyATfo_IfCEy9iuwTn1vZVjvFOwytJYz2W0")
model = genai.GenerativeModel("gemini-pro")


@login_required
def home(request):
    sessions = Session.objects.filter(user=request.user)
    return render(request, "home.html", {"sessions": sessions})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})


@login_required
def create_session(request):
    if request.method == "POST":
        title = request.POST.get("title")
        session = Session.objects.create(user=request.user, title=title)
        return redirect("session_detail", session_id=session.id)
    return render(request, "create_session.html")


@login_required
def create_session_with_option(request, option):
    title_map = {
        "exam-preparation": "Exam Preparation Guide",
        "research-assistant": "Research Assistant",
        "legal-analysis": "Legal Document Analysis",
        "nutritional-label": "Nutritional Label Interpreter",
    }
    title = title_map.get(option, "Custom Session")
    session = Session.objects.create(user=request.user, title=title)
    return redirect("upload_document", session_id=session.id)



@login_required
@require_http_methods(["DELETE"])
def delete_session(request, session_id):
    try:
        session = Session.objects.get(id=session_id, user=request.user)
        session.delete()
        return JsonResponse({"success": True})
    except Session.DoesNotExist:
        return JsonResponse({"success": False, "error": "Session not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def session_detail(request, session_id):
    session = Session.objects.get(id=session_id)
    queries = Query.objects.filter(session=session)
    identity_keywords = ["who are you", "what are you", "your name", "your identity"]
    model_keywords = ["which model are you", "what model are you", "powered by", "based on"]

    # Define predefined questions based on session title
    predefined_questions_map = {
        "Exam Preparation Guide": {
            "summarize": "Summarize the key concepts in this study material.",
            "keywords": "Extract important terms and definitions.",
            "details": "Provide a detailed explanation of the topics covered.",
        },
        "Research Assistant": {
            "summarize": "Summarize the main findings of this research paper.",
            "keywords": "Extract key terms and methodologies.",
            "details": "Explain the research objectives and conclusions.",
        },
        "Legal Document Analysis": {
            "summarize": "Summarize the key clauses and terms in this legal document.",
            "keywords": "Extract important legal terms and conditions.",
            "details": "Analyze the implications of specific clauses.",
        },
        "Nutritional Label Interpreter": {
            "summarize": "Summarize the nutritional information in this label.",
            "keywords": "Extract key ingredients and allergens.",
            "details": "Provide a detailed analysis of the nutritional content.",
        },
    }

    predefined_questions = predefined_questions_map.get(session.title, {})

    try:
        context = ""
        for doc in session.document_set.all():
            file_path = doc.file.path
            context += extract_text_from_pdf(file_path)
        if not context.strip():
            raise ValueError("No text could be extracted from the uploaded document.")
    except Exception as e:
        return render(request, "error.html", {"message": str(e)})
    html_response = ""
    if request.method == "POST":
        question = request.POST.get("question", "").strip(" ").lower()

        # Check if the question contains identity-related keywords
        if any(keyword in question for keyword in identity_keywords):
            html_response = markdown.markdown(
                "I am CleverQuery, your personal assistant designed to help you interact with documents and answer your questions.",
                extensions=["extra"],
            )
        # Check if the question contains model-related keywords
        elif any(keyword in question for keyword in model_keywords):
            html_response = markdown.markdown(
                "I am powered by advanced AI models, but my purpose is to serve as your friendly assistant within CleverQuery.",
                extensions=["extra"],
            )
        else:
            # Generate response using the LLM
            context = ""
            for doc in session.document_set.all():
                file_path = doc.file.path
                extracted_text = extract_text_from_pdf(file_path)
                if not extracted_text:
                    return render(
                        request,
                        "error.html",
                        {"message": "No text could be extracted from the uploaded document."},
                    )
                context += extracted_text

            response = model.generate_content(f"{context}\nQuestion: {question}")
            html_response = markdown.markdown(response.text, extensions=["extra"])
    elif "question" in request.GET:
        question_key = request.GET["question"]
        question = predefined_questions.get(question_key, "Invalid question.")
    else:
        question = None

    if len(html_response) > 0:
        Query.objects.create(session=session, question=question, answer=html_response)
        return redirect("session_detail", session_id=session.id)
    elif question:
        response = model.generate_content(f"{context}\nQuestion: {question}")
        html_response = markdown.markdown(response.text, extensions=["extra"])
        Query.objects.create(session=session, question=question, answer=html_response)
        return redirect("session_detail", session_id=session.id)

    return render(
        request,
        "session_detail.html",
        {"session": session, "queries": queries, "predefined_questions": predefined_questions},
    )


@login_required
def upload_document(request, session_id):
    session = Session.objects.get(id=session_id)
    if request.method == "POST":
        file = request.FILES["pdf_file"]
        Document.objects.create(session=session, file=file)
        return redirect("session_detail", session_id=session.id)
    return render(request, "upload_document.html", {"session": session})


@csrf_exempt
@login_required
def update_session_title(request, session_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_title = data.get("title")
            session = Session.objects.get(id=session_id, user=request.user)
            session.title = new_title
            session.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request method."})
