import os

import faiss
import google.generativeai as genai
import markdown
import numpy as np
import PyPDF2

from dotenv import load_dotenv

from .constants import IDENTITY_KEYWORDS, MODEL_KEYWORDS, PREDEFINED_QUESTIONS_MAP
from .models import Query


def extract_text_from_pdf(file):
    """
    Extract text content from a PDF file.
    This function uses PyPDF2 to read a PDF file and extract text content
    from all pages, concatenating them into a single string.
    """
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


extensions = [
    "markdown.extensions.extra",
    "markdown.extensions.abbr",
    "markdown.extensions.attr_list",
    "markdown.extensions.def_list",
    "markdown.extensions.fenced_code",
    "markdown.extensions.footnotes",
    "markdown.extensions.md_in_html",
    "markdown.extensions.tables",
    "markdown.extensions.admonition",
    "markdown.extensions.codehilite",
    "markdown.extensions.legacy_attrs",
    "markdown.extensions.legacy_em",
    "markdown.extensions.meta",
    "markdown.extensions.nl2br",
    "markdown.extensions.sane_lists",
    "markdown.extensions.smarty",
    "markdown.extensions.toc",
    "markdown.extensions.wikilinks",
]

load_dotenv()
genai.configure(api_key=os.getenv("GENERATIVEAI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-lite")


def get_predefined_questions(session_type):
    return PREDEFINED_QUESTIONS_MAP.get(session_type, {})


def check_identity_question(question):
    """
    Check if the question is about the identity of the assistant.
    """

    if any(keyword in question for keyword in IDENTITY_KEYWORDS):
        return markdown.markdown(
            "I am CleverQuery, your personal assistant designed to help you interact "
            "with documents and answer your questions.",
            extensions=extensions,
        )
    return None


def check_model_question(question):
    """
    Check if the question is about the AI model powering the assistant.
    """

    if any(keyword in question for keyword in MODEL_KEYWORDS):
        return markdown.markdown(
            "I am powered by advanced AI models, but my purpose is to serve as your "
            "friendly assistant within CleverQuery.",
            extensions=extensions,
        )
    return None


def process_documents_with_rag(session, rag_engine, file=None):
    """
    Process all documents in a session with the RAG engine.
    """
    try:
        rag_engine.reset_index()

        for doc in session.document_set.all():
            extracted_text = doc.extracted_text
            if not extracted_text:
                extracted_text = extract_text_from_pdf(file)
                if not extracted_text:
                    return False, "No text could be extracted from the uploaded document."
                doc.extracted_text = extracted_text
                doc.save()

            if not doc.embeddings.exists():
                rag_engine.process_document(extracted_text, document=doc)
            else:
                embeddings = np.array([np.array(e.embedding) for e in doc.embeddings.all()])
                if rag_engine.index is None:
                    rag_engine.index = faiss.IndexFlatL2(rag_engine.dimension)
                rag_engine.index.add(embeddings.astype("float32"))
                rag_engine.chunks.extend(doc.text_chunks)

        return True, ""
    except Exception as e:
        print(f"Error processing documents with RAG: {e}")
        return False, str(e)


def get_recent_queries_context(session, limit=3):
    """ "
    Get the context of recent queries in the session.
    """

    recent_queries = Query.objects.filter(session=session).order_by("-asked_at")[:limit]
    recent_context = ""
    if recent_queries:
        recent_context = "\n\nRecent relevant interactions:\n"
        for query in recent_queries:
            recent_context += f"Q: {query.question}\nA: {query.answer}\n\n"
    return recent_context


def generate_ai_response_stream(
    question, context, session_type, rag_engine=None, recent_context=""
):
    """
    Generate a response stream from the AI model based on the input question and context.
    """

    try:
        if rag_engine:
            relevant_context = rag_engine.get_context_for_query(question, k=3)
        else:
            relevant_context = context

        fixed_prompt = PREDEFINED_QUESTIONS_MAP.get(session_type, {}).get("fixed_prompt", "")

        combined_prompt = (
            f"{fixed_prompt}\nQuestion: {question}\n\n"
            f"Please provide a response between 1 and 300 words.\n\n"
            f"Relevant Context:\n{relevant_context}{recent_context}"
        )

        chat = model.start_chat()
        response_stream = chat.send_message(combined_prompt, stream=True)

        # Ensure the stream is properly consumed
        try:
            for chunk in response_stream:
                yield chunk
        except Exception as stream_error:
            print(f"Error in stream iteration: {stream_error}")
            yield f"Stream interrupted: {str(stream_error)}"

    except Exception as e:
        print(f"Error generating AI response stream: {e}")
        yield f"Sorry, I couldn't generate a response due to an error: {str(e)}"


def generate_ai_response(question, context, session_title, rag_engine=None, recent_context=""):
    """
    Generate a response from the AI model based on the input question and context.
    """

    stream = generate_ai_response_stream(
        question, context, session_title, rag_engine, recent_context
    )

    full_response = ""
    for chunk in stream:
        if hasattr(chunk, "text") and chunk.text:
            full_response += chunk.text

    return markdown.markdown(full_response, extensions=extensions)


def handle_predefined_question(question_key, context, session_type):
    """ "
    Handle predefined questions based on the session type and question key."
    """

    question = PREDEFINED_QUESTIONS_MAP.get(session_type, {}).get(
        question_key, "Invalid question."
    )

    stream = generate_ai_response_stream(question, context, session_type)

    full_response = ""
    for chunk in stream:
        if hasattr(chunk, "text") and chunk.text:
            full_response += chunk.text

    return question, markdown.markdown(full_response, extensions=extensions)


def format_stream_chunk(chunk):
    """
    Format a stream chunk into a text string.
    """

    if hasattr(chunk, "text") and chunk.text:
        return chunk.text
    return ""
