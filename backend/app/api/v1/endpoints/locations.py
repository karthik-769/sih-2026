from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.location import Location
from app.schemas.location import LocationResponse

router = APIRouter()


@router.get(
    "/locations",
    response_model=List[LocationResponse],
    summary="List Plant Locations",
    description="Retrieve all operational plant sites and units configured in the system.",
)
def get_locations(db: Session = Depends(get_db)) -> List[LocationResponse]:
    """
    Returns list of all active plant units/locations.
    """
    locations = db.query(Location).order_by(Location.name.asc()).all()
    return locations
