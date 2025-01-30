from typing import Dict, List

from pydantic import BaseModel


class PostData(BaseModel):
    post_data: Dict[str, str] = {}
    headers_values: List[str] = []
    queries_keys: List[str] = []
    queries_values: List[str] = []
    client_id: str = ""
    post_data_type: str = 'application/json'


class RequestDataModel:
    class Result(BaseModel):
        UrRequestData: str

    class RequestData(BaseModel):
        result: 'RequestDataModel.Result'
        execution_time: float
