from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import re
import ollama

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def generate_review(code_text, file_type="code"):
    prompt = f"""
1. Detect all bugs or syntax errors in the following {file_type} code.
2. Explain the errors in detail (why they are errors, what caused them, etc.).
3. Provide a fully corrected version of the code.
4. After the corrected code, provide detailed documentation on the following:
   - What the original problem was.
   - Why the changes were necessary.
   - How the fixed code addresses the issues.
   - Any suggestions for improvement or best practices related to the problem.

CODE:
{code_text}
"""
    try:
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.get('message', {}).get('content', '') or ""
    except Exception as e:
        return f"Error generating review: {e}"


def extract_fixed_code(review_text):
    if not review_text:
        return ""
    match = re.search(r"```(.*?)```", review_text, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_sections(review_text):
    problem = solution = suggestions = "N/A"
    if not review_text:
        return problem, solution, suggestions

    problem_match = re.search(r"Problem:\s*(.*?)\s*(Solution:|$)", review_text, re.DOTALL)
    if problem_match:
        problem = problem_match.group(1).strip()

    solution_match = re.search(r"Solution:\s*(.*?)\s*(Suggestions:|$)", review_text, re.DOTALL)
    if solution_match:
        solution = solution_match.group(1).strip()

    suggestions_match = re.search(r"Suggestions:\s*(.*)", review_text, re.DOTALL)
    if suggestions_match:
        suggestions = suggestions_match.group(1).strip()

    return problem, solution, suggestions


@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/review", response_class=HTMLResponse)
async def review_code(
    request: Request,
    file: UploadFile = File(None),
    edited_code: str = Form(None)
):
    code_text = ""
    if file:
        contents = await file.read()
        code_text = contents.decode("utf-8")
    elif edited_code:
        code_text = edited_code

    if not code_text:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "No code provided!"
        })

    try:
        review = generate_review(code_text, file_type="web")
        fixed_code = extract_fixed_code(review)
        problem, solution, suggestions = extract_sections(review)
    except Exception as e:
        review = fixed_code = ""
        problem = solution = suggestions = "found"
        return templates.TemplateResponse("index.html", {
            "request": request,
            "code": code_text,
            "error": f"Error generating review: {e}"
        })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "code": code_text,
        "review": review,
        "fixed_code": fixed_code,
        "problem": problem,
        "solution": solution,
        "suggestions": suggestions
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
