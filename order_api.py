from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Order API", version="1.0")

class CancelRequest(BaseModel):
    order_number: str
    reason: str

@app.post("/cancel", status_code=204)
async def cancel_order(req: CancelRequest):
    # Parametreleri console'a logla
    print("📦 Order Cancel Request Received")
    print(f"   ➡️ Order Number: {req.order_number}")
    print(f"   ➡️ Reason      : {req.reason}")
    print("✅ Order cancellation processed.\n")

    # 204 No Content → body dönmez
    return