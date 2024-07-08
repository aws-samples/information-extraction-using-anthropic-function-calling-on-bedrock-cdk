from pydantic import BaseModel, Field
from datetime import date
from enum import Enum
from typing import List

## this genderValues class is just for illustration purposes. 
# You can define your pydantic class schema as strict as possible.
class GenderValues(str, Enum):
    "Allowable values for extracting the Gender."
    Male: str = Field("Male", description="Passport shows Gender or Sex as Male")
    Female: str = Field("Female", description="Passport shows Gender or sex as Female")
    NB: str = Field("N/A", description="Passport has Gender or Sex values other than Male and Female")

class PassportFields(BaseModel):
    """
    Extract all the passport fields from uploaded image if uploaded image is passport.
    """
    gender: GenderValues = Field(description="Gender or Sex as shown on the passport.", default="N/A")
    passport_number: str = Field(description="Passport number as shown on the passport.", default="N/A")
    issuing_country: str = Field(description="Country that issued the passport.", default="N/A")
    first_name: str = Field(description="First Name or Given Name as shown on the passport.", default="N/A")
    last_name: str = Field(description="Last Name or Family Name as shown on the passport.", default="N/A")
    date_of_birth: date = Field(description="Date of birth in YYYY-MM-DD format.", default="N/A")
    place_of_birth: str = Field(description="Place of birth as shown on the passport.", default="N/A")
    nationality: str = Field(description="Nationality as shown on the passport.", default="N/A")
    date_of_issue: date = Field(description="Date of issue in YYYY-MM-DD format.", default="N/A")
    date_of_expiry: date = Field(description="Date of expiry in YYYY-MM-DD format.", default="N/A")
    issuing_authority: str = Field(description="Authority that issued the passport.", default="N/A")
