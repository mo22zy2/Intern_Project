from fastapi import APIRouter

router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"]
)

@router.get("/")
async def my_reservations():
    pass


@router.post("/new")
async def make_reservation():
    pass


@router.put("/{reservation_id}/edit")
async def edit_reservation(reservation_id: int):
    pass


@router.delete("/{reservation_id}/cancel")
async def cancel_reservation(reservation_id: int):
    pass