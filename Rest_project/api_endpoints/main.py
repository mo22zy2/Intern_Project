from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .django_setup import setup_django
from .routers import (
    auth, home, menu, cart, order, reservation, profile, review, payment, admin
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_django()
    yield


app = FastAPI(title="Restruant API Endpoints", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(home.router)
app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(cart.router)
app.include_router(order.router)
app.include_router(reservation.router)
app.include_router(profile.router)
app.include_router(review.router)
app.include_router(payment.router)
app.include_router(admin.router)
