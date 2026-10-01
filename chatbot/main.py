import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from chatbot.database import init_db, pool
from chatbot.graph import create_agent_graph
from chatbot.router import router


BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
	if not os.getenv("DB_URI"):
		raise RuntimeError("DB_URI is not configured. Add it to the .env file.")

	pool.open(wait=True)
	try:
		init_db()
		app.state.agent_app = create_agent_graph()
		yield
	finally:
		pool.close()


app = FastAPI(title="Aira", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(router)
