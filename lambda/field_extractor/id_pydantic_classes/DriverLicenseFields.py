from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
import re

class DriverLicenseFields(BaseModel):
    """
    Extract all the driver's license fields from an uploaded image if the uploaded image is a driver's license.
    """
    gender: Optional[str] = Field(None, description="Gender or Sex as shown on the driver's license. (e.g. M, F)", pattern=r'^[MF]$')
    license_number: Optional[str] = Field(None, description="License number as shown on the driver's license.", pattern=r'^[A-Z0-9]+$')
    full_name: Optional[str] = Field(None, description="Full name as shown on the driver's license.")
    date_of_birth: Optional[date] = Field(None, description="Date of birth in YYYY-MM-DD format.")
    address: Optional[str] = Field(None, description="Address as shown on the driver's license.")
    city_state_zip: Optional[str] = Field(None, description="City, state, and zip code as shown on the driver's license.")
    eye_color: Optional[str] = Field(None, description="Eye color as shown on the driver's license.")
    height: Optional[str] = Field(None, description="Height as shown on the driver's license.")
    issue_date: Optional[date] = Field(None, description="Date of issue in YYYY-MM-DD format.")
    expiration_date: Optional[date] = Field(None, description="Date of expiration in YYYY-MM-DD format.")
    endorsements: Optional[str] = Field(None, description="Endorsements or restrictions as shown on the driver's license.")
    nationality: Optional[str] = Field(None, description="Nationality as shown on the driver's license.")
