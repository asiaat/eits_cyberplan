"""Dashboard API endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
def dashboard_summary():
    """Get dashboard summary."""
    return {
        "total_measures": 0,
        "implemented": 0,
        "in_progress": 0,
        "not_started": 0,
        "overdue": 0,
        "high_risks": 0,
    }


@router.get("/imr-progress")
def imr_progress():
    """Get IMR progress."""
    return {"not_started": 0, "in_progress": 0, "implemented": 0, "not_applicable": 0}


@router.get("/risk-heatmap")
def risk_heatmap():
    """Get risk heatmap data."""
    return []