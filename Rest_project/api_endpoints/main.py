from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    auth, home, menu, cart, order, reservation, profile, review, payment
)

app = FastAPI(title="Rest API Endpoints")

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
