from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(title="Grand Stay Hotel Management System")

# --- DATA MODELS ---

# Initial Room Data
rooms = [
    {"id": 1, "room_number": "101", "type": "Single", "price_per_night": 1200, "floor": 1, "is_available": True},
    {"id": 2, "room_number": "102", "type": "Double", "price_per_night": 2000, "floor": 1, "is_available": True},
    {"id": 3, "room_number": "201", "type": "Suite", "price_per_night": 5000, "floor": 2, "is_available": True},
    {"id": 4, "room_number": "202", "type": "Deluxe", "price_per_night": 3500, "floor": 2, "is_available": False},
    {"id": 5, "room_number": "301", "type": "Single", "price_per_night": 1100, "floor": 3, "is_available": True},
    {"id": 6, "room_number": "302", "type": "Suite", "price_per_night": 5500, "floor": 3, "is_available": True},
]

bookings = []
booking_counter = 1
room_counter = 7

# --- PYDANTIC MODELS ---

class BookingRequest(BaseModel):
    guest_name: str = Field(..., min_length=2)
    room_id: int = Field(..., gt=0)
    nights: int = Field(..., gt=0, le=30)
    phone: str = Field(..., min_length=10)
    meal_plan: str = Field("none", pattern="^(none|breakfast|all-inclusive)$")
    early_checkout: bool = False

class NewRoom(BaseModel):
    room_number: str = Field(..., min_length=1)
    type: str = Field(..., min_length=2)
    price_per_night: int = Field(..., gt=0)
    floor: int = Field(..., gt=0)
    is_available: bool = True

# --- HELPER FUNCTIONS ---

def find_room(room_id: int):
    return next((r for r in rooms if r["id"] == room_id), None)

def calculate_stay_cost(price: int, nights: int, meal_plan: str, early_checkout: bool):
    total = price * nights
    if meal_plan == "breakfast":
        total += (500 * nights)
    elif meal_plan == "all-inclusive":
        total += (1200 * nights)
    
    discount = 0
    if early_checkout:
        discount = total * 0.10
        total -= discount
    return total, discount

# --- ROUTES ---

# Q1: Home
@app.get("/")
def home():
    return {"message": "Welcome to Grand Stay Hotel"}

# Q5 & Q2: Room Retrieval & Summary (Fixed before Variable)
@app.get("/rooms/summary")
def get_room_summary():
    available = [r for r in rooms if r["is_available"]]
    prices = [r["price_per_night"] for r in rooms]
    types = {}
    for r in rooms:
        types[r["type"]] = types.get(r["type"], 0) + 1
    
    return {
        "total_rooms": len(rooms),
        "available_count": len(available),
        "occupied_count": len(rooms) - len(available),
        "cheapest_price": min(prices) if prices else 0,
        "most_expensive_price": max(prices) if prices else 0,
        "type_breakdown": types
    }

# Q10: Filter Rooms
@app.get("/rooms/filter")
def filter_rooms(
    type: Optional[str] = None, 
    max_price: Optional[int] = None, 
    floor: Optional[int] = None, 
    is_available: Optional[bool] = None
):
    results = rooms
    if type: results = [r for r in results if r["type"].lower() == type.lower()]
    if max_price: results = [r for r in results if r["price_per_night"] <= max_price]
    if floor: results = [r for r in results if r["floor"] == floor]
    if is_available is not None: results = [r for r in results if r["is_available"] == is_available]
    return {"results": results, "count": len(results)}

# Q16: Search Rooms
@app.get("/rooms/search")
def search_rooms(keyword: str):
    matches = [r for r in rooms if keyword.lower() in r["room_number"].lower() or keyword.lower() in r["type"].lower()]
    if not matches:
        return {"message": f"No rooms found matching '{keyword}'"}
    return {"matches": matches, "total_found": len(matches)}

# Q17: Sort Rooms
@app.get("/rooms/sort")
def sort_rooms(sort_by: str = "price_per_night", order: str = "asc"):
    if sort_by not in ["price_per_night", "floor", "type"]:
        raise HTTPException(400, "Invalid sort_by field")
    if order not in ["asc", "desc"]:
        raise HTTPException(400, "Order must be asc or desc")
    
    sorted_list = sorted(rooms, key=lambda x: x[sort_by], reverse=(order == "desc"))
    return sorted_list

# Q18: Paginate Rooms
@app.get("/rooms/page")
def paginate_rooms(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit
    total_pages = (len(rooms) + limit - 1) // limit
    return {
        "page": page,
        "limit": limit,
        "total_rooms": len(rooms),
        "total_pages": total_pages,
        "results": rooms[start:end]
    }

# Q20: Combined Browse
@app.get("/rooms/browse")
def browse_rooms(
    keyword: Optional[str] = None,
    sort_by: str = "price_per_night",
    order: str = "asc",
    page: int = 1,
    limit: int = 3
):
    data = rooms
    if keyword:
        data = [r for r in data if keyword.lower() in r["type"].lower()]
    
    data = sorted(data, key=lambda x: x[sort_by], reverse=(order == "desc"))
    
    start = (page - 1) * limit
    return data[start : start + limit]

@app.get("/rooms")
def get_all_rooms():
    return {
        "rooms": rooms,
        "total": len(rooms),
        "available_count": len([r for r in rooms if r["is_available"]])
    }

# Q3: Get Room by ID
@app.get("/rooms/{room_id}")
def get_room(room_id: int):
    room = find_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

# --- BOOKING ROUTES ---

# Q15: Active Bookings (Fixed before Variable)
@app.get("/bookings/active")
def get_active_bookings():
    active = [b for b in bookings if b["status"] in ["confirmed", "checked_in"]]
    return active

# Q19: Search & Sort Bookings
@app.get("/bookings/search")
def search_bookings(guest_name: str):
    return [b for b in bookings if guest_name.lower() in b["guest_name"].lower()]

@app.get("/bookings/sort")
def sort_bookings(sort_by: str = "total_cost"):
    if sort_by not in ["total_cost", "nights"]:
        raise HTTPException(400, "Sort by total_cost or nights")
    return sorted(bookings, key=lambda x: x[sort_by])

@app.get("/bookings")
def get_all_bookings():
    return {"bookings": bookings, "total": len(bookings)}

# Q8 & Q9: Create Booking
@app.post("/bookings")
def create_booking(request: BookingRequest):
    global booking_counter
    room = find_room(request.room_id)
    if not room:
        raise HTTPException(404, "Room not found")
    if not room["is_available"]:
        raise HTTPException(400, "Room is already occupied")
    
    total_cost, discount = calculate_stay_cost(
        room["price_per_night"], request.nights, request.meal_plan, request.early_checkout
    )
    
    room["is_available"] = False
    new_booking = {
        "booking_id": booking_counter,
        "guest_name": request.guest_name,
        "room_details": room,
        "nights": request.nights,
        "meal_plan": request.meal_plan,
        "total_cost": total_cost,
        "discount_applied": discount,
        "status": "confirmed"
    }
    bookings.append(new_booking)
    booking_counter += 1
    return new_booking

# Q11: Add New Room
@app.post("/rooms", status_code=201)
def add_room(room_data: NewRoom):
    global room_counter
    if any(r["room_number"] == room_data.room_number for r in rooms):
        raise HTTPException(400, "Room number already exists")
    
    new_r = room_data.model_dump()
    new_r["id"] = room_counter
    rooms.append(new_r)
    room_counter += 1
    return new_r

# Q12: Update Room
@app.put("/rooms/{room_id}")
def update_room(room_id: int, price: Optional[int] = None, available: Optional[bool] = None):
    room = find_room(room_id)
    if not room: raise HTTPException(404, "Room not found")
    if price is not None: room["price_per_night"] = price
    if available is not None: room["is_available"] = available
    return room

# Q13: Delete Room
@app.delete("/rooms/{room_id}")
def delete_room(room_id: int):
    room = find_room(room_id)
    if not room: raise HTTPException(404, "Room not found")
    if not room["is_available"]:
        raise HTTPException(400, "Cannot delete an occupied room")
    rooms.remove(room)
    return {"message": "Room deleted successfully"}

# Q14: Check-in
@app.post("/checkin/{booking_id}")
def check_in(booking_id: int):
    booking = next((b for b in bookings if b["booking_id"] == booking_id), None)
    if not booking: raise HTTPException(404, "Booking not found")
    booking["status"] = "checked_in"
    return booking

# Q15: Check-out
@app.post("/checkout/{booking_id}")
def check_out(booking_id: int):
    booking = next((b for b in bookings if b["booking_id"] == booking_id), None)
    if not booking: raise HTTPException(404, "Booking not found")
    
    booking["status"] = "checked_out"
    room = find_room(booking["room_details"]["id"])
    if room:
        room["is_available"] = True
    return {"message": "Checked out successfully", "booking": booking}