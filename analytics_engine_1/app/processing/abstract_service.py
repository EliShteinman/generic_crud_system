from abc import ABC, abstractmethod
from typing import Any

class AbstractAnalysisService(ABC):
    """
    מגדיר את הממשק המשותף לכל שירותי העיבוד והניתוח.
    """
    FETCH_DATA_FIRST: bool = True

    @abstractmethod
    async def process(self, data: Any, **kwargs) -> Any:
        """
        המתודה הראשית שתבצע את העיבוד.
        'data' יכול להיות DataFrame, רשימת מילונים, או None.
        """
        pass