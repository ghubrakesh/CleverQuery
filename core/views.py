import json
import os

from datetime import datetime

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
from dotenv import load_dotenv

from .helpers import extract_text_from_pdf
from .models import Document, Query, Session

extensions = [
    "markdown.extensions.extra",  # Includes several commonly used extensions
    "markdown.extensions.abbr",  # Abbreviations
    "markdown.extensions.attr_list",  # Attribute Lists
    "markdown.extensions.def_list",  # Definition Lists
    "markdown.extensions.fenced_code",  # Fenced Code Blocks
    "markdown.extensions.footnotes",  # Footnotes
    "markdown.extensions.md_in_html",  # Markdown within HTML
    "markdown.extensions.tables",  # Tables
    "markdown.extensions.admonition",  # Admonition (e.g., notes, warnings)
    "markdown.extensions.codehilite",  # Syntax highlighting for code blocks
    "markdown.extensions.legacy_attrs",  # Legacy Attributes
    "markdown.extensions.legacy_em",  # Legacy Emphasis
    "markdown.extensions.meta",  # Meta-Data
    "markdown.extensions.nl2br",  # New Line to Break
    "markdown.extensions.sane_lists",  # Sane Lists
    "markdown.extensions.smarty",  # SmartyPants (smart quotes, dashes, etc.)
    "markdown.extensions.toc",  # Table of Contents
    "markdown.extensions.wikilinks",  # WikiLinks
]

load_dotenv()
genai.configure(api_key=os.getenv("GENERATIVEAI_API_KEY"))
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
            user = form.save()
            auth_login(request, user)
            return redirect("/")
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
        "technical-manual": "Technical Manual Interpreter",
        "legal-document": "Legal Document Analysis",
        "nutritional-label": "Nutritional Label Interpreter",
        "financial-report": "Financial Report Analysis",
        "contract-review": "Contract Review Assistant",
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
        return JsonResponse({"success": False, "error": "Session not found."})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def session_detail(request, session_id):
    session = Session.objects.get(id=session_id)
    if not session.document_set.exists():
        return render(
            request,
            "error.html",
            {"session": session, "code": "no_pdf_found", "message": "No document found."},
        )

    queries = Query.objects.filter(session=session)
    identity_keywords = ["who are you", "what are you", "your name", "your identity"]
    model_keywords = ["which model are you", "what model are you", "powered by", "based on"]

    # Define predefined questions based on session title
    predefined_questions_map = {
        "Exam Preparation Guide": {
            "summarize": "Summarize the key concepts in this study material.",
            "keywords": "Extract important terms and definitions.",
            "details": "Provide a detailed explanation of the topics covered.",
            "fixed_prompt": "You are a smart exam preparation guide bound to clear the doubts of students and provide neat answers which can help them ace their exams.",
        },
        "Technical Manual Interpreter": {
            "summarize": "Summarize the main points of this technical manual.",
            "keywords": "Extract key technical terms and instructions.",
            "details": "Provide a detailed explanation of the procedures and guidelines.",
            "fixed_prompt": "You are a technical manual interpreter providing clear and concise explanations of technical documents.",
        },
        "Legal Document Analysis": {
            "summarize": "Summarize the key clauses and terms in this legal document.",
            "keywords": "Extract important legal terms and conditions.",
            "details": "Analyze the implications of specific clauses.",
            "fixed_prompt": "You are a legal document analyst providing detailed analysis and summaries of legal documents.",
        },
        "Nutritional Label Interpreter": {
            "summarize": "Summarize the nutritional information in this label.",
            "keywords": "Extract key ingredients and allergens.",
            "details": "Provide a detailed analysis of the nutritional content.",
            "fixed_prompt": "You are a nutritional label interpreter providing clear and detailed information about nutritional content.",
        },
        "Financial Report Analysis": {
            "summarize": "Summarize the key financial metrics in this report.",
            "keywords": "Extract important financial terms and figures.",
            "details": "Provide a detailed analysis of the financial data.",
            "fixed_prompt": "You are a financial report analyst providing detailed summaries and analysis of financial reports.",
        },
        "Contract Review Assistant": {
            "summarize": "Summarize the main points of this contract.",
            "keywords": "Extract key terms and obligations.",
            "details": "Analyze the implications of specific contract clauses.",
            "fixed_prompt": "You are a contract review assistant providing detailed summaries and analysis of various contract reports.",
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
                extensions=extensions,
            )
        # Check if the question contains model-related keywords
        elif any(keyword in question for keyword in model_keywords):
            html_response = markdown.markdown(
                "I am powered by advanced AI models, but my purpose is to serve as your friendly assistant within CleverQuery.",
                extensions=["extra"],
            )
        else:
            # Generate response using the LLM
            fixed_prompt = predefined_questions_map.get(session.title, {}).get("fixed_prompt", "")
            pdf_context = "\n\nCONTEXT: "
            for doc in session.document_set.all():
                extracted_text = doc.extracted_text
                if not extracted_text:
                    file_path = doc.file.path
                    extracted_text = extract_text_from_pdf(file_path)
                    if not extracted_text:
                        return render(
                            request,
                            "error.html",
                            {"message": "No text could be extracted from the uploaded document."},
                        )
                pdf_context += extracted_text
            recent_queries = Query.objects.filter(session=session).order_by("-asked_at")[:3]
            if recent_queries:
                pdf_context += (
                    "\n\n And here are my most recent queries for your better understanding: "
                )
                for query in recent_queries:
                    pdf_context += f"Question: {query.question}\nAnswer: {query.answer}\n\n"

            combined_prompt = f"{fixed_prompt} \n Here is your question: {question} \n Here is Context: {pdf_context}"
            response = model.generate_content(combined_prompt)
            html_response = markdown.markdown(response.text, extensions=["extra"])
    elif "question" in request.GET:
        question_key = request.GET["question"]
        question = predefined_questions.get(question_key, "Invalid question.")
    else:
        question = None

    if len(html_response) > 0:
        session.updated_at = datetime.now()
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
        {
            "session": session,
            "queries": queries,
            "predefined_questions": predefined_questions,
            "selected_session": session,
        },
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
            session.updated_at = datetime.now()
            session.title = new_title
            session.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request method."})


@login_required
@require_http_methods(["POST"])
def edit_message(request, query_id):
    try:
        query = Query.objects.get(id=query_id, session__user=request.user)
        new_text = request.POST.get("text")
        if new_text:
            query.question = new_text
            query.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "Invalid input."}, status=400)
    except Query.DoesNotExist:
        return JsonResponse({"success": False, "error": "Query not found."}, status=404)


@login_required
@require_http_methods(["DELETE"])
def delete_message(request, query_id):
    try:
        query = Query.objects.get(id=query_id, session__user=request.user)
        query.delete()
        return JsonResponse({"success": True})
    except Query.DoesNotExist:
        return JsonResponse({"success": False, "error": "Query not found."}, status=404)
