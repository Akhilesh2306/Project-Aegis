"""File for document parsing service"""

# Import External Libraries
import re
import logging
from pathlib import Path

# Import Internal Packages
from agent.state import Clause

# Setup logging
logger = logging.getLogger(__name__)


class DocumentParser:
    """
    Parses contract documents into structured clauses.
    Supports: Markdown (.md), PDF (.pdf), plain text (.txt)
    """

    def parse(self, filename: str, text: str) -> list[Clause]:
        """
        Main entry point -> detects format and delegate to appropriate parser.
        """

        file_suffix = Path(filename).suffix.lower()

        logging.info(f"Parsing document: {filename} (format: {file_suffix})")

        if file_suffix in (".md", ".txt", ""):
            clauses = self._parse_markdown(text)

        elif file_suffix == ".pdf":
            clauses = self._parse_plain_text(text)

        else:
            logger.warning(
                f"Unknown format {file_suffix}, falling back to markdown parser"
            )
            clauses = self._parse_markdown(text)

        logger.info(f"Parsed {len(clauses)} clauses from {filename}")
        return clauses

    def _parse_markdown(self, text: str) -> list[Clause]:
        """
        Parses markdown-formatted contracts.
        """
        clauses = []

        # Split on ## headings (level 2 markdown headers)
        sections = re.split(r"\n(?=#{2,}\s)", text)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Extract heading and content
            lines = section.split("\n")
            heading = lines[0].strip()
            content = "\n".join(lines[1:]).strip()

            # Must start with ## or deeper — skip single # titles
            if not re.match(r"^#{2,}\s", heading):
                continue

            # Skip empty sections
            if not content:
                continue

            # Parse section number and title from heading
            # Handles: "## 1. Services", "## 2. Term and Termination"
            heading_clean = re.sub(r"^#{1,}\s+", "", heading).strip()
            number, title = self._extract_number_and_title(heading_clean)

            clause: Clause = {
                "clause_id": f"section_{number}",
                "section_number": number,
                "title": title,
                "content": content,
            }
            clauses.append(clause)

        return clauses

    def _parse_plain_text(self, text: str) -> list[Clause]:
        """
        Fallback parser for plain text contracts.
        Splits on numbered section patterns like:
          1. Services
          2. TERM AND TERMINATION
          SECTION 1 -
        """
        clauses = []

        # Match common section number patterns
        pattern = r"\n(?=\d+[\.\)]\s+[A-Z])"
        sections = re.split(pattern, text)

        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            lines = section.split("\n")
            heading = lines[0].strip()
            content = "\n".join(lines[1:]).strip()

            if not content:
                continue

            number, title = self._extract_number_and_title(heading)

            clause: Clause = {
                "clause_id": f"section_{number}",
                "section_number": number,
                "title": title,
                "content": content,
            }
            clauses.append(clause)

        return clauses

    def _extract_number_and_title(self, heading: str) -> tuple[str, str]:
        """
        Extracts section number and clean title from a heading string.

        Examples:
          "1. Services"           → ("1", "Services")
          "2. Term and Termination" → ("2", "Term and Termination")
          "Introduction"          → ("0", "Introduction")
        """
        # Pattern: optional number + separator + title
        match = re.match(r"^(\d+)[\.\)\-\s]+(.+)$", heading)
        if match:
            number = match.group(1)
            title = match.group(2).strip()
            return number, title

        # No number found — use "0" as default
        return "0", heading.strip()
