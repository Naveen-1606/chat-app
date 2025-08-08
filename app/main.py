from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Chat API is up and running!"}
