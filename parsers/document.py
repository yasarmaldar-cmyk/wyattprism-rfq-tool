from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    raw_text: str
    pages: list[str] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    filename: str = ""
    page_count: int = 0
    file_type: str = ""
    char_count: int = 0
    estimated_tokens: int = 0

    def __post_init__(self):
        self.char_count = len(self.raw_text)
        self.estimated_tokens = self.char_count // 4
