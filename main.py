import os
from groq import Groq
from typing import Annotated
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, WebSocket
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse


load_dotenv()

app = FastAPI(title="ChatBot")
templates = Jinja2Templates(directory="templates")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

chat_responses = []
chat_log = [{'role' : 'system', 'content' : 'You are a python tutor AI '}]


# endpoints
@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()
        chat_log.append({"role": "user", "content": user_input})
        chat_responses.append(user_input)
        try:
            completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=chat_log,
                temperature=1,
                stream=True
            )

            ai_response = ""
            for chunk in completion:
                if (data := chunk.choices[0].delta.content) is not None:
                    ai_response += data
                    await websocket.send_text(data)

            # chat_log.append({"role": "assistant", "content": bot_response})
            chat_responses.append(ai_response) 

        except Exception as e:
            await websocket.send_text(f"Error: {str(e)}")
            break


@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):  
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    chat_log.append({"role": "user", "content": user_input})
    chat_responses.append(user_input)

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=chat_log,
        temperature=1
    )

    bot_response = completion.choices[0].message.content
    chat_log.append({"role": "assistant", "content": bot_response})
    chat_responses.append(bot_response)
    print(chat_responses)
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


@app.get("/image", response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse("image.html", {"request": request})


# @app.post("/image", response_class=HTMLResponse)
# async def create_image(request: Request, user_input: Annotated[str, Form()]):

#     response = openai.images.generate(
#         prompt=user_input,
#         n=1,
#         size="256x256"
#     )

#     image_url = response.data[0].url
#     return templates.TemplateResponse("image.html", {"request": request, "image_url": image_url})

