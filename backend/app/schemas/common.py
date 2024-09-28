# -*- coding: utf-8 -*-
from caseconverter import camelcase
from pydantic import BaseModel


class CamelCaseModel(BaseModel):
    """
    Pydantic configuration that allows the model to be populated by snake case (Python)
    and camel case (JS). Facilitates smooth interaction with the frontend.
    """

    class Config:
        populate_by_name = True

        @staticmethod
        def alias_generator(
            s: str,
        ) -> str:
            return camelcase(s)
