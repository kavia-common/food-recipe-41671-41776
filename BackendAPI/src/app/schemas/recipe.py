from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RecipeBase(BaseModel):
    title: str = Field(..., description="Recipe title")
    description: Optional[str] = Field(None, description="Recipe description")
    ingredients: List[str] = Field(..., description="List of ingredients")
    steps: List[str] = Field(..., description="List of preparation steps")
    cuisine: Optional[str] = Field(None, description="Cuisine")
    diet: Optional[str] = Field(None, description="Dietary preference")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    prepTime: Optional[int] = Field(None, description="Preparation time (minutes)")
    cookTime: Optional[int] = Field(None, description="Cooking time (minutes)")
    nutrition: Optional[Dict[str, Any]] = Field(None, description="Nutrition info")
    rating: Optional[float] = Field(None, description="Average rating")
    imageUrl: Optional[str] = Field(None, description="Image URL")


class RecipeOut(RecipeBase):
    id: int = Field(..., description="Recipe ID")

    class Config:
        from_attributes = True
