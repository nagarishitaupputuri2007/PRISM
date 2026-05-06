from fastapi import APIRouter
from models.schemas import AnalyzeRequest

router = APIRouter()

@router.post("/analyze")
async def analyze_product(request: AnalyzeRequest):
    return {
        "status": "success",
        "data": {
            "product_name": request.product_name,
            "message": "Analysis coming soon 🚀"
        }
    }