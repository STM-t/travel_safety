from fastapi import APIRouter, HTTPException

from ..schemas import AnalyzeRequest, AnalyzeResponse
from ..services.orchestrator import analyze_trip

router = APIRouter(prefix="/api/v1", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """Агрегирует климат (10 лет), геополитику, ЧС, праздники и выдаёт вердикт."""
    try:
        return await analyze_trip(req)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
