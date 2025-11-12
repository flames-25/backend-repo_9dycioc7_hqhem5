import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Account, Contact, Lead, Deal, Task, Activity, Product

app = FastAPI(title="Flames CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "CRM Backend Running"}

@app.get("/schema")
def get_schema():
    # Simple export so UI tools can read the available collections
    return {
        "collections": [
            "user", "account", "contact", "lead", "deal", "task", "activity", "product"
        ]
    }

# Utility

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

# Dashboard snapshot

@app.get("/api/dashboard")
def dashboard_snapshot(team: Optional[str] = None, owner_id: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    def count(collection, query=None):
        return db[collection].count_documents(query or {})

    total_leads = count("lead")
    total_deals = count("deal")
    total_revenue = sum([d.get("value", 0) for d in db["deal"].find({"stage": {"$in": ["won", "closed-won"]}})])
    qualified = count("lead", {"status": "qualified"})
    conversion_rate = (qualified / total_leads * 100) if total_leads else 0

    stages = list(db["deal"].aggregate([
        {"$group": {"_id": "$stage", "count": {"$sum": 1}}},
        {"$project": {"stage": "$_id", "count": 1, "_id": 0}}
    ]))

    recent_activities = list(db["activity"].find({}, {"subject": 1, "type": 1, "created_at": 1}).sort("created_at", -1).limit(10))

    return {
        "cards": {
            "totalLeads": total_leads,
            "totalDeals": total_deals,
            "revenue": total_revenue,
            "conversionRate": round(conversion_rate, 2)
        },
        "pipeline": stages,
        "recentActivities": recent_activities,
    }

# Minimal CRUD endpoints for key entities

class LeadCreate(Lead):
    pass

@app.post("/api/leads")
def create_lead(payload: LeadCreate):
    lead_id = create_document("lead", payload)
    return {"_id": lead_id}

@app.get("/api/leads")
def list_leads(status: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    query = {}
    if status:
        query["status"] = status
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}},
        ]
    docs = get_documents("lead", query, limit)
    return docs

@app.patch("/api/leads/{lead_id}")
def update_lead(lead_id: str, data: dict):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    res = db["lead"].update_one({"_id": to_object_id(lead_id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"updated": True}

# Deals

@app.post("/api/deals")
def create_deal(payload: Deal):
    deal_id = create_document("deal", payload)
    return {"_id": deal_id}

@app.get("/api/deals")
def list_deals(stage: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    query = {}
    if stage:
        query["stage"] = stage
    if q:
        query["title"] = {"$regex": q, "$options": "i"}
    docs = get_documents("deal", query, limit)
    return docs

@app.patch("/api/deals/{deal_id}")
def update_deal(deal_id: str, data: dict):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    res = db["deal"].update_one({"_id": to_object_id(deal_id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"updated": True}

# Tasks (simple)

@app.post("/api/tasks")
def create_task(payload: Task):
    task_id = create_document("task", payload)
    return {"_id": task_id}

@app.get("/api/tasks")
def list_tasks(owner_id: Optional[str] = None, due: Optional[str] = None, limit: int = 50):
    query = {}
    if owner_id:
        query["owner_id"] = owner_id
    docs = get_documents("task", query, limit)
    return docs

@app.patch("/api/tasks/{task_id}")
def update_task(task_id: str, data: dict):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    res = db["task"].update_one({"_id": to_object_id(task_id)}, {"$set": data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"updated": True}

# Activities (timeline)

@app.post("/api/activities")
def create_activity(payload: Activity):
    act_id = create_document("activity", payload)
    return {"_id": act_id}

@app.get("/api/activities")
def list_activities(related_type: Optional[str] = None, related_id: Optional[str] = None, limit: int = 50):
    query = {}
    if related_type:
        query["related_type"] = related_type
    if related_id:
        query["related_id"] = related_id
    docs = get_documents("activity", query, limit)
    return docs

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            collections = db.list_collection_names()
            response["collections"] = collections[:10]
            response["database"] = "✅ Connected & Working"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
