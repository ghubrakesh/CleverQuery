import json
import os
import threading

from datetime import datetime, timedelta, timezone

import google.generativeai as genai
import markdown

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from dotenv import load_dotenv

from .constants import SessionTypeEnum
from .helpers import (
    check_identity_question,
    check_model_question,
    extensions,
    extract_text_from_pdf,
    generate_ai_response,
    generate_ai_response_stream,
    get_predefined_questions,
    get_recent_queries_context,
    handle_predefined_question,
    process_documents_with_rag,
)
from .models import Document, Query, Session
from .rag_engine import RAGEngine

load_dotenv()
genai.configure(api_key=os.getenv("GENERATIVEAI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-lite")

rag_engine = RAGEngine()


def index(request):
    return render(request, "index.html")


@login_required
def home(request):
    """
    Homepage with options to create new session
    """

    sessions = Session.objects.filter(user=request.user)
    return render(request, "home.html", {"sessions": sessions})


@login_required
def dashboard(request):
    """
    Dashboard support with recent queries and sessions
    """

    sessions = Session.objects.filter(user=request.user)
    recent_queries = Query.objects.filter(session__in=sessions).order_by("-asked_at")[:10]
    return render(
        request,
        "dashboard.html",
        {"sessions": sessions, "recent_queries": recent_queries},
    )


def login_view(request):
    """
    Login page with form to authenticate user
    """

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
    """
    Logout user and redirect to login
    """

    auth_logout(request)
    return redirect("login")


def register_view(request):
    """
    Register page with form to create new user account
    """

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})


@login_required
def create_session(request):
    """
    Create a new session without uploading a document. It's not used as of now.
    """

    if request.method == "POST":
        title = request.POST.get("title")
        session = Session.objects.create(user=request.user, title=title)
        return redirect("session_detail", session_id=session.id)
    return render(request, "create_session.html")


@login_required
def create_session_with_option(request, option):
    """
    Create a new session with a specific session type.
    """

    title_map = SessionTypeEnum.as_dict()
    title = title_map.get(option, "Custom Session")
    session = Session.objects.create(user=request.user, title=title, session_type=option)
    return redirect("upload_document", session_id=session.id)


@login_required
@require_http_methods(["DELETE"])
def delete_session(request, session_id):
    """
    Delete a session using it's session_id.
    """

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
    """
    Display the session details and handle user queries.
    """

    session = Session.objects.get(id=session_id)
    if not session.document_set.exists():
        return render(
            request,
            "error.html",
            {"session": session, "code": "no_pdf_found", "message": "No document found."},
        )

    queries = Query.objects.filter(session=session)
    predefined_questions = get_predefined_questions(session.session_type)

    try:
        context = ""
        for doc in session.document_set.all():
            context += doc.extracted_text
    except Exception as e:
        return render(request, "error.html", {"message": str(e)})

    html_response = ""
    if request.method == "POST":
        question = request.POST.get("question", "").strip(" ").lower()

        identity_response = check_identity_question(question)
        if identity_response:
            html_response = identity_response
        else:
            model_response = check_model_question(question)
            if model_response:
                html_response = model_response
            else:
                success, error_message = process_documents_with_rag(session, rag_engine)
                if not success:
                    return render(request, "error.html", {"message": error_message})

                recent_context = get_recent_queries_context(session)

                html_response = generate_ai_response(
                    question, context, session.title, rag_engine, recent_context
                )

    elif "question" in request.GET:
        question_key = request.GET["question"]
        question, html_response = handle_predefined_question(
            question_key, context, session.session_type
        )
    else:
        question = None

    if len(html_response) > 0:
        session.updated_at = datetime.now()
        Query.objects.create(
            session=session, question=question, answer=html_response, asked_at=timezone.now()
        )
        return redirect("session_detail", session_id=session.id)
    elif question:
        question, html_response = handle_predefined_question(
            question, context, session.session_type
        )
        Query.objects.create(
            session=session, question=question, answer=html_response, asked_at=timezone.now()
        )
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
    """"
    Upload a PDF document to a session.
    """

    if request.method == "POST":
        session = Session.objects.get(id=session_id)
        file = request.FILES["pdf_file"]
        extracted_text = extract_text_from_pdf(file)
        Document.objects.create(session=session, extracted_text=extracted_text)
        return redirect("session_detail", session_id=session.id)
    return render(request, "upload_document.html", {"session_id": session_id})


@csrf_exempt
@login_required
def update_session_title(request, session_id):
    """"
    Update the title of a session.
    """
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
    """
    Edit a query message. Not yet supported
    """
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
    """
    Delete a query message. Not yet supported
    """
    try:
        query = Query.objects.get(id=query_id, session__user=request.user)
        query.delete()
        return JsonResponse({"success": True})
    except Query.DoesNotExist:
        return JsonResponse({"success": False, "error": "Query not found."}, status=404)


@login_required
def stream_response(request, session_id):
    """
    Stream response (realtime generation) for a given question instead of waiting to load
    the entire response.
    """

    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    session = Session.objects.get(id=session_id)
    question = request.POST.get("question", "").strip()

    stream_position = request.POST.get("stream_position", 0)
    try:
        stream_position = int(stream_position)
    except (TypeError, ValueError):
        stream_position = 0

    if stream_position > 0:
        recent_time = datetime.now() - timedelta(minutes=10)
        existing_query = (
            Query.objects.filter(session=session, question=question, asked_at__gte=recent_time)
            .order_by("-asked_at")
            .first()
        )

        if existing_query and existing_query.answer:
            full_response = existing_query.answer

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(full_response, "html.parser")
            plain_text = soup.get_text()

            if len(plain_text) > stream_position:
                remaining_text = plain_text[stream_position:]
                return StreamingHttpResponse(
                    streaming_content=[remaining_text, "\n<!-- STREAM_COMPLETE -->"],
                    content_type="text/plain",
                )

    success, error_message = process_documents_with_rag(session, rag_engine)
    if not success:
        return JsonResponse({"error": error_message}, status=500)

    recent_context = get_recent_queries_context(session)

    context_text = ""
    for doc in session.document_set.all():
        context_text += doc.extracted_text

    response_buffer = []

    def generate_chunks():
        full_response = ""
        last_chunk_sent = False
        chunk_count = 0

        try:
            identity_response = check_identity_question(question.lower())
            if identity_response:
                plain_response = identity_response.replace("<p>", "").replace("</p>", "")
                yield plain_response
                response_buffer.append(plain_response)
                full_response = plain_response
            elif model_response := check_model_question(question.lower()):
                plain_response = model_response.replace("<p>", "").replace("</p>", "")
                yield plain_response
                response_buffer.append(plain_response)
                full_response = plain_response
            else:
                actual_question = question
                try:
                    stream = generate_ai_response_stream(
                        actual_question,
                        context_text,
                        session.session_type,
                        rag_engine,
                        recent_context,
                    )

                    for chunk in stream:
                        chunk_count += 1
                        if hasattr(chunk, "text") and chunk.text:
                            text_chunk = chunk.text
                            yield text_chunk
                            response_buffer.append(text_chunk)
                            full_response += text_chunk

                            if chunk_count >= 1000:
                                break
                except Exception as e:
                    error_info = f"\nStreaming was interrupted: {str(e)}"
                    yield error_info
                    full_response += error_info
                    response_buffer.append(error_info)

            yield "\n<!-- STREAM_COMPLETE -->"
            last_chunk_sent = True

            def save_response():
                try:
                    if not full_response.strip():
                        return

                    html_response = markdown.markdown(full_response, extensions=extensions)

                    recent_time = datetime.now() - timedelta(minutes=10)
                    existing_query = (
                        Query.objects.filter(
                            session=session, question=question, asked_at__gte=recent_time
                        )
                        .order_by("-asked_at")
                        .first()
                    )

                    if existing_query:
                        existing_query.answer = html_response
                        existing_query.save()
                    else:
                        session.updated_at = datetime.now()
                        Query.objects.create(
                            session=session, question=question, answer=html_response
                        )
                except Exception as e:
                    print(f"Error saving response: {e}")

            thread = threading.Thread(target=save_response)
            thread.daemon = True
            thread.start()

        except Exception as e:
            print(f"Error in stream_response: {e}")
            if not last_chunk_sent:
                error_msg = f"\nError occurred: {str(e)}"
                yield error_msg
                yield "\n<!-- STREAM_COMPLETE -->"

    response = StreamingHttpResponse(
        streaming_content=generate_chunks(), content_type="text/plain"
    )

    response["Cache-Control"] = "no-cache, no-transform"
    response["X-Accel-Buffering"] = "no"

    return response
