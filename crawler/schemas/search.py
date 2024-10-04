from pydantic import BaseModel


class SearchPlan(BaseModel):
    category: str
    queries: list[str]


class SearchPlans(BaseModel):
    plans: list[SearchPlan]


class SearchCategories(BaseModel):
    categories: list[str]


def update_search_plans(x: SearchPlans, y: SearchPlans) -> SearchPlans:
    return y if y else x


def increment_search_iterations(x: int, y: int) -> int:
    return x + y


def update_search_categories(x: list[str], y: list[str]) -> list[str]:
    return y if y else x
