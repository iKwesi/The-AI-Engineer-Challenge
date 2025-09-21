"""
Excel and CSV loading utilities.

This module provides utilities for loading Excel (.xlsx, .xls) and CSV files
with enhanced error handling, metadata extraction, and data formatting.
"""

from pathlib import Path
from typing import List, Union, Optional, Iterable
import pandas as pd
import openpyxl
from openpyxl import load_workbook

from .base import FileBasedLoader
from ..models import Document, DocumentType, DocumentProcessingError


class ExcelLoader(FileBasedLoader):
    """
    Load Excel and CSV documents (.xlsx, .xls, .csv files).
    
    Extracts data from all sheets, handles multiple formats,
    and converts tabular data to readable text format.
    """

    def __init__(
        self, 
        path: Union[str, Path], 
        include_all_sheets: bool = True,
        max_rows_per_sheet: int = 1000,
        include_formulas: bool = False
    ):
        """
        Initialize the Excel loader.
        
        Args:
            path: Path to Excel/CSV file or directory
            include_all_sheets: Whether to process all sheets in Excel files
            max_rows_per_sheet: Maximum rows to process per sheet
            include_formulas: Whether to include formula text (Excel only)
        """
        super().__init__(path)
        self.include_all_sheets = include_all_sheets
        self.max_rows_per_sheet = max_rows_per_sheet
        self.include_formulas = include_formulas

    def can_load(self, source: Union[Path, str]) -> bool:
        """
        Check if this loader can handle the given source.
        
        Args:
            source: File path to check
            
        Returns:
            True if the source is an Excel/CSV file or directory, False otherwise
        """
        path = Path(source)
        if path.is_dir():
            return True
        return path.suffix.lower() in [".xlsx", ".xls", ".csv"]

    def load_documents(self, source: Union[Path, str]) -> List[Document]:
        """
        Load documents from the given source.
        
        Args:
            source: File path or directory to load from
            
        Returns:
            List of loaded Document objects
            
        Raises:
            DocumentProcessingError: If loading fails
        """
        path = Path(source)
        
        if path.is_dir():
            return self._load_directory_documents(path)
        elif path.is_file() and path.suffix.lower() in [".xlsx", ".xls", ".csv"]:
            return [self._load_single_file(path)]
        else:
            raise DocumentProcessingError(
                f"Provided path must be a directory or an Excel/CSV file: {path}"
            )

    def _load_directory_documents(self, directory: Path) -> List[Document]:
        """
        Load all Excel/CSV files from a directory.
        
        Args:
            directory: Directory to load from
            
        Returns:
            List of Document objects
        """
        documents = []
        for file_path in self._iter_directory_files(directory):
            try:
                document = self._load_single_file(file_path)
                documents.append(document)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")
                # Continue processing other files
        
        return documents

    def _load_single_file(self, file_path: Path) -> Document:
        """
        Load a single Excel/CSV file and return a Document object.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            A Document object containing the file content
            
        Raises:
            DocumentProcessingError: If the file cannot be loaded
        """
        # Validate file
        self.validate_file_size(file_path)
        self.validate_file_extension(file_path)
        
        try:
            if file_path.suffix.lower() == ".csv":
                content, metadata = self._read_csv_file(file_path)
            else:
                content, metadata = self._read_excel_file(file_path)
            
            return self.create_document(
                content=content,
                source_path=file_path,
                document_type=DocumentType.EXCEL,
                metadata=metadata
            )
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to load Excel/CSV file {file_path}: {e}")

    def _iter_directory_files(self, directory: Path) -> Iterable[Path]:
        """
        Iterate over Excel/CSV files in a directory.
        
        Args:
            directory: Directory to iterate over
            
        Yields:
            Path objects for Excel and CSV files
        """
        for pattern in ["*.xlsx", "*.xls", "*.csv"]:
            for entry in sorted(directory.rglob(pattern)):
                if entry.is_file():
                    yield entry

    def _read_csv_file(self, file_path: Path) -> tuple[str, dict]:
        """
        Read a CSV file and extract content and metadata.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            A tuple of (extracted_text, metadata_dict)
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None
            encoding_used = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, nrows=self.max_rows_per_sheet)
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise DocumentProcessingError(f"Could not read CSV file with any encoding: {file_path}")
            
            # Convert DataFrame to readable text
            content = self._dataframe_to_text(df, "CSV Data")
            
            # Extract metadata
            metadata = {
                "sheet_count": 1,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "column_names": list(df.columns),
                "encoding_used": encoding_used,
                "has_header": True,  # Assume CSV has header
                "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            }
            
            return content, metadata
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to read CSV file {file_path}: {e}")

    def _read_excel_file(self, file_path: Path) -> tuple[str, dict]:
        """
        Read an Excel file and extract content and metadata.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            A tuple of (extracted_text, metadata_dict)
        """
        try:
            # Load workbook for metadata
            workbook = load_workbook(file_path, read_only=True, data_only=not self.include_formulas)
            
            content_parts = []
            sheet_metadata = {}
            total_rows = 0
            total_columns = 0
            
            # Process sheets
            sheets_to_process = workbook.sheetnames if self.include_all_sheets else [workbook.sheetnames[0]]
            
            for sheet_name in sheets_to_process:
                try:
                    # Read sheet with pandas
                    df = pd.read_excel(
                        file_path, 
                        sheet_name=sheet_name, 
                        nrows=self.max_rows_per_sheet
                    )
                    
                    if not df.empty:
                        sheet_text = self._dataframe_to_text(df, f"Sheet: {sheet_name}")
                        content_parts.append(sheet_text)
                        
                        sheet_metadata[sheet_name] = {
                            "rows": len(df),
                            "columns": len(df.columns),
                            "column_names": list(df.columns),
                            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
                        }
                        
                        total_rows += len(df)
                        total_columns = max(total_columns, len(df.columns))
                
                except Exception as e:
                    print(f"Warning: Failed to process sheet '{sheet_name}': {e}")
                    continue
            
            # Combine all content
            content = "\n\n".join(content_parts) if content_parts else ""
            
            # Extract workbook metadata
            metadata = {
                "sheet_count": len(workbook.sheetnames),
                "sheets_processed": len(content_parts),
                "sheet_names": workbook.sheetnames,
                "total_rows": total_rows,
                "total_columns": total_columns,
                "sheet_metadata": sheet_metadata,
                "workbook_properties": self._extract_excel_properties(workbook),
            }
            
            workbook.close()
            return content, metadata
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to read Excel file {file_path}: {e}")

    def _dataframe_to_text(self, df: pd.DataFrame, title: str) -> str:
        """
        Convert a pandas DataFrame to readable text format.
        
        Args:
            df: DataFrame to convert
            title: Title for this data section
            
        Returns:
            Formatted text representation
        """
        if df.empty:
            return f"=== {title} ===\n[Empty dataset]"
        
        text_parts = [f"=== {title} ==="]
        
        # Add basic info
        text_parts.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
        text_parts.append(f"Columns: {', '.join(df.columns)}")
        text_parts.append("")
        
        # Convert to string representation
        # Use a reasonable number of rows for display
        display_rows = min(100, len(df))
        df_display = df.head(display_rows)
        
        # Format as table-like text
        text_parts.append("Data:")
        
        # Add column headers
        headers = " | ".join(str(col) for col in df_display.columns)
        text_parts.append(headers)
        text_parts.append("-" * len(headers))
        
        # Add data rows
        for _, row in df_display.iterrows():
            row_text = " | ".join(str(value) if pd.notna(value) else "" for value in row)
            text_parts.append(row_text)
        
        if len(df) > display_rows:
            text_parts.append(f"... and {len(df) - display_rows} more rows")
        
        return "\n".join(text_parts)

    def _extract_excel_properties(self, workbook) -> dict:
        """
        Extract properties from Excel workbook.
        
        Args:
            workbook: openpyxl Workbook object
            
        Returns:
            Dictionary containing workbook properties
        """
        properties = {}
        
        try:
            props = workbook.properties
            if props:
                properties.update({
                    "title": props.title or "",
                    "creator": props.creator or "",
                    "subject": props.subject or "",
                    "description": props.description or "",
                    "keywords": props.keywords or "",
                    "category": props.category or "",
                    "created": props.created.isoformat() if props.created else "",
                    "modified": props.modified.isoformat() if props.modified else "",
                    "last_modified_by": props.lastModifiedBy or "",
                })
        except Exception as e:
            print(f"Warning: Failed to extract Excel properties: {e}")
        
        return properties

    # Convenience methods for backward compatibility
    def load(self) -> None:
        """
        Populate self.documents from the configured path.
        """
        self.documents = self.load_documents(self.path)

    def load_file(self) -> None:
        """
        Load a single file specified by self.path.
        """
        super().load_file()

    def load_directory(self) -> None:
        """
        Load all Excel/CSV files contained within self.path.
        """
        super().load_directory()
