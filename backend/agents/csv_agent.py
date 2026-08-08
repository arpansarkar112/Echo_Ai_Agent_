from __future__ import annotations

import base64
import json
import os
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd
from fastapi import UploadFile
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.google.google_ai import (
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion import (
    GoogleAIChatCompletion,
)
from semantic_kernel.functions import KernelArguments
from semantic_kernel.exceptions import ServiceInitializationError

from identity import identity_response, is_identity_query


_AGGREGATION_ALIASES = {
    "sum": "sum",
    "total": "sum",
    "total sum": "sum",
    "add": "sum",
    "add up": "sum",
    "combined": "sum",
    "overall total": "sum",
    "average": "mean",
    "avg": "mean",
    "mean": "mean",
    "median": "median",
    "max": "max",
    "maximum": "max",
    "highest": "max",
    "largest": "max",
    "min": "min",
    "minimum": "min",
    "lowest": "min",
    "smallest": "min",
    "count": "count",
    "row count": "count",
    "number of rows": "count",
    "entries": "count",
    "records": "count",
    "std": "std",
    "stdev": "std",
    "standard deviation": "std",
    "variance": "var",
    "var": "var",
}

_AGGREGATION_DISPLAY_NAMES = {
    "mean": "average",
    "std": "std dev",
    "var": "variance",
}


def _normalize_text(value: str) -> str:
    sanitized = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", sanitized).strip()


_ROW_MATH_SYNONYMS = {
    "sum": {
        "sum",
        "total",
        "total sum",
        "add",
        "add up",
        "addition",
        "overall total",
        "plus",
    },
    "mean": {
        "mean",
        "average",
        "avg",
    },
    "difference": {
        "difference",
        "difference between",
        "subtract",
        "subtraction",
        "minus",
        "deduct",
        "less",
        "less than",
        "subtract from",
    },
    "product": {
        "product",
        "multiply",
        "multiplication",
        "times",
        "multiplied by",
    },
    "ratio": {
        "ratio",
        "ratio of",
        "divide",
        "division",
        "divided by",
        "quotient",
    },
}

_ROW_MATH_ALIASES = {
    canonical: {
        _normalize_text(alias)
        for alias in aliases | {canonical}
        if _normalize_text(alias)
    }
    for canonical, aliases in _ROW_MATH_SYNONYMS.items()
}

_ROW_MATH_SUPPORTED_OPERATIONS = tuple(sorted(_ROW_MATH_ALIASES.keys()))


class CSVAgentError(Exception):
    """Raised when the CSV processing agent runs into a recoverable issue."""


@dataclass
class ExecutionResult:
    summary: str
    table_markdown: Optional[str] = None


class CSVAgent:
    """CSV processing agent powered by Microsoft Semantic Kernel."""

    def __init__(
        self,
        storage_dir: Path,
        *,
        model_id: Optional[str] = None,
        service_id: str = "gemini-sk",
    ) -> None:
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        preferred_model = model_id or os.getenv("SK_GOOGLE_MODEL")
        if not preferred_model:
            preferred_model = os.getenv("GOOGLE_GENAI_MODEL")
        self.model_id = preferred_model or "gemini-pro-latest"
        self.service_id = service_id
        self.plugin_name = "csv_agent"
        self.intent_function_name = "plan_csv_task"
        self.response_function_name = "compose_csv_answer"
        self.index_path = self.storage_dir / "session_index.json"
        if not self.index_path.exists():
            self.index_path.write_text("{}", encoding="utf-8")

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    async def ingest_file(
        self, upload: UploadFile, user_id: str, session_id: str
    ) -> Dict[str, Any]:
        """Persist the uploaded file, build metadata, and return a quick summary."""
        raw_bytes = await upload.read()
        if not raw_bytes:
            raise CSVAgentError("The uploaded file is empty.")

        dataset_id = uuid4().hex
        dataset_dir = self.storage_dir / dataset_id
        dataset_dir.mkdir(parents=True, exist_ok=False)
        csv_path = dataset_dir / "data.csv"

        try:
            with csv_path.open("wb") as fout:
                fout.write(raw_bytes)

            df = self._read_dataframe(BytesIO(raw_bytes))
        except Exception as exc:  # noqa: BLE001 - surface readable error upstream
            # Clean up any partially written directory
            self._safe_remove_dir(dataset_dir)
            raise CSVAgentError(f"Failed to read the CSV file: {exc}") from exc

        metadata = self._build_metadata(
            dataset_id=dataset_id,
            session_id=session_id,
            user_id=user_id,
            filename=upload.filename or "uploaded.csv",
            dataframe=df,
        )

        meta_path = dataset_dir / "meta.json"
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        self._register_dataset(session_id=session_id, dataset_id=dataset_id)

        summary_text, preview_table = self._summarize_dataset(metadata, df)

        return {
            "dataset_id": dataset_id,
            "filename": metadata["filename"],
            "rows": metadata["rows"],
            "columns": metadata["columns"],
            "summary": summary_text,
            "preview_table": preview_table,
        }

    async def analyze(
        self, dataset_id: str, question: str, *, user_id: str
    ) -> str:
        """Run the CSV agent pipeline for a natural language question."""
        if is_identity_query(question):
            return identity_response()

        metadata, df = self._load_dataset(dataset_id)

        if metadata["user_id"] != user_id:
            raise CSVAgentError("Dataset not found for this user.")

        dataset_profile = self._compose_dataset_profile(metadata, df)

        kernel = self._create_kernel()

        detection = self._detect_user_intent(question, df)
        hint_arguments = self._build_intent_hint_arguments(detection)

        if (
            detection
            and detection.get("intent")
            and detection.get("confidence") == "certain"
        ):
            plan = {
                "intent": detection["intent"],
                "parameters": detection.get("parameters", {}),
            }
            execution = self._execute_plan(plan, df, metadata, question=question)
            return await self._generate_final_message(
                kernel,
                question,
                dataset_profile,
                plan,
                execution,
            )

        plan_arguments = {
            "input": question,
            "dataset_profile": dataset_profile,
        }
        plan_arguments.update(hint_arguments)

        plan_raw = await self._invoke_kernel(
            kernel,
            function_name=self.intent_function_name,
            arguments=plan_arguments,
        )

        plan = self._parse_plan(plan_raw, hints=detection, df=df)

        if detection and detection.get("intent"):
            if (
                plan.get("intent") in {"raw_answer", "dataset_overview"}
                and detection.get("confidence") in {"medium", "certain"}
            ):
                plan = {
                    "intent": detection["intent"],
                    "parameters": detection.get("parameters", {}),
                }

        execution = self._execute_plan(plan, df, metadata, question=question)

        return await self._generate_final_message(
            kernel,
            question,
            dataset_profile,
            plan,
            execution,
        )

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _create_kernel(self) -> Kernel:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise CSVAgentError(
                "GOOGLE_API_KEY is missing. Configure it before using the CSV agent."
            )

        try:
            service = GoogleAIChatCompletion(
                service_id=self.service_id,
                gemini_model_id=self.model_id,
                api_key=api_key,
            )
        except ServiceInitializationError as exc:
            raise CSVAgentError("Failed to initialise the Google AI chat service.") from exc

        kernel = Kernel()
        kernel.add_service(service)

        planner_settings = GoogleAIChatPromptExecutionSettings(
            service_id=self.service_id,
            temperature=0.0,
            max_output_tokens=1024,
            response_mime_type="application/json",
        )

        response_settings = GoogleAIChatPromptExecutionSettings(
            service_id=self.service_id,
            temperature=0.2,
            max_output_tokens=1200,
        )

        kernel.add_function(
            plugin_name=self.plugin_name,
            function_name=self.intent_function_name,
            prompt=_INTENT_PROMPT,
            prompt_execution_settings=planner_settings,
        )

        kernel.add_function(
            plugin_name=self.plugin_name,
            function_name=self.response_function_name,
            prompt=_RESPONSE_PROMPT,
            prompt_execution_settings=response_settings,
        )

        return kernel

    async def _invoke_kernel(
        self,
        kernel: Kernel,
        *,
        function_name: str,
        arguments: Dict[str, Any],
    ) -> str:
        # Kernel.invoke is async; run in the existing event loop
        kernel_arguments = KernelArguments(**arguments)
        try:
            result = await kernel.invoke(
                function_name=function_name,
                plugin_name=self.plugin_name,
                arguments=kernel_arguments,
            )
        except Exception as exc:  # noqa: BLE001 - surface a readable agent error
            raise CSVAgentError(
                "Failed to contact the Gemini model for CSV reasoning. "
                "Please verify the configured model name and API key."
            ) from exc

        if result is None or result.value is None:
            return ""

        value = result.value
        if isinstance(value, str):
            return value

        if isinstance(value, Sequence):
            collected: List[str] = []
            for entry in value:
                text_attr = getattr(entry, "text", None)
                if text_attr:
                    collected.append(str(text_attr))
                items = getattr(entry, "items", None)
                if items:
                    for item in items:
                        item_text = getattr(item, "text", None)
                        if item_text:
                            collected.append(str(item_text))
            return "\n".join(segment for segment in collected if segment).strip()

        return str(value)

    async def _generate_final_message(
        self,
        kernel: Kernel,
        question: str,
        dataset_profile: str,
        plan: Dict[str, Any],
        execution: ExecutionResult,
    ) -> str:
        """Create the final assistant reply, using the response prompt when possible."""
        response_raw = ""
        try:
            response_raw = await self._invoke_kernel(
                kernel,
                function_name=self.response_function_name,
                arguments={
                    "input": question,
                    "dataset_profile": dataset_profile,
                    "plan_json": json.dumps(plan, ensure_ascii=False),
                    "analysis_notes": execution.summary,
                    "table_preview": execution.table_markdown
                    if execution.table_markdown
                    else "No table generated.",
                },
            )
        except CSVAgentError:
            response_raw = ""

        final_message = response_raw.strip() if response_raw else execution.summary

        if execution.table_markdown:
            final_message = f"{final_message}\n\n{execution.table_markdown}"

        return final_message
    

    def _read_dataframe(self, buffer: BytesIO) -> pd.DataFrame:
        buffer.seek(0)
        try_encodings = (None, "utf-8", "utf-8-sig", "latin-1")
        last_err: Optional[Exception] = None
        for enc in try_encodings:
            buffer.seek(0)
            try:
                return pd.read_csv(buffer, encoding=enc)
            except UnicodeDecodeError as exc:
                last_err = exc
                continue
            except Exception:
                raise
        raise CSVAgentError(f"Unable to decode CSV with supported encodings: {last_err}")

    def _build_metadata(
        self,
        *,
        dataset_id: str,
        session_id: str,
        user_id: str,
        filename: str,
        dataframe: pd.DataFrame,
    ) -> Dict[str, Any]:
        column_info: List[Dict[str, Any]] = []
        for column in dataframe.columns:
            series = dataframe[column]
            sample_values = (
                series.dropna().astype(str).head(3).tolist()
                if not series.empty
                else []
            )
            column_info.append(
                {
                    "name": column,
                    "dtype": str(series.dtype),
                    "non_null": int(series.count()),
                    "nulls": int(series.isna().sum()),
                    "sample_values": sample_values,
                }
            )

        metadata: Dict[str, Any] = {
            "dataset_id": dataset_id,
            "session_id": session_id,
            "user_id": user_id,
            "filename": filename,
            "rows": int(len(dataframe)),
            "columns": int(len(dataframe.columns)),
            "column_info": column_info,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        return metadata
    


    def _summarize_dataset(
        self, metadata: Dict[str, Any], dataframe: pd.DataFrame
    ) -> Tuple[str, str]:
        missing_columns = sum(col["nulls"] > 0 for col in metadata["column_info"])
        duplicate_rows = int(dataframe.duplicated().sum())

        summary_lines = [
            f"✅ CSV ingested: **{metadata['filename']}**",
            f"- Rows: **{metadata['rows']}**, Columns: **{metadata['columns']}**",
        ]
        if missing_columns:
            summary_lines.append(
                f"- Columns with missing values: **{missing_columns}**"
            )
        if duplicate_rows:
            summary_lines.append(f"- Duplicate rows detected: **{duplicate_rows}**")
        summary_lines.append(
            "- Columns: "
            + ", ".join(f"`{info['name']}` ({info['dtype']})" for info in metadata["column_info"])
        )

        preview_markdown = self._format_dataframe(dataframe.head(5))

        return "\n".join(summary_lines), preview_markdown

    def _load_dataset(self, dataset_id: str) -> Tuple[Dict[str, Any], pd.DataFrame]:
        dataset_dir = self.storage_dir / dataset_id
        csv_path = dataset_dir / "data.csv"

        if not csv_path.exists():
            raise CSVAgentError("CSV dataset could not be found on the server.")

        metadata = self._load_metadata(dataset_id)
        df = pd.read_csv(csv_path)
        return metadata, df

    def _compose_dataset_profile(
        self, metadata: Dict[str, Any], df: pd.DataFrame
    ) -> str:
        column_lines = []
        for info in metadata["column_info"]:
            examples = ", ".join(info["sample_values"]) if info["sample_values"] else "n/a"
            column_lines.append(
                f"- {info['name']} (dtype: {info['dtype']}, missing: {info['nulls']}) "
                f"examples: {examples}"
            )

        preview = self._format_dataframe(df.head(5))

        profile = textwrap.dedent(
            f"""
            Dataset filename: {metadata['filename']}
            Total rows: {metadata['rows']}
            Total columns: {metadata['columns']}
            Columns:
            {os.linesep.join(column_lines)}

            Preview (first rows):
            {preview}
            """
        ).strip()

        return profile

    def _parse_plan(
        self,
        raw_plan: str,
        *,
        hints: Optional[Dict[str, Any]] = None,
        df: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        if not raw_plan:
            return {"intent": "dataset_overview", "parameters": {}}

        text = raw_plan.strip()
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                candidate = parts[1].strip()
                if candidate.lower().startswith("json"):
                    candidate = candidate[4:].strip()
                text = candidate

        try:
            plan = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CSVAgentError(
                "The agent could not parse your request into a plan. Please try rephrasing."
            ) from exc

        supported_intents = {
            "dataset_overview",
            "list_columns",
            "describe_column",
            "filter_rows",
            "aggregate",
            "value_counts",
            "top_n",
            "set_cell_value",
            "add_row",
            "add_column",
            "row_math",
            "delete_row",
            "delete_rows",
            "plot_line",
            "plot_bar",
            "raw_answer",
        }

        intent = plan.get("intent")
        if intent not in supported_intents:
            # Fall back to a descriptive raw answer instead of erroring out.
            return {
                "intent": "raw_answer",
                "parameters": {
                    "reason": f"Unsupported operation requested: {intent!r}."
                },
            }

        plan.setdefault("parameters", {})
        return self._normalize_plan(plan, hints=hints, df=df)

    def _normalize_plan(
        self,
        plan: Dict[str, Any],
        *,
        hints: Optional[Dict[str, Any]],
        df: Optional[pd.DataFrame],
    ) -> Dict[str, Any]:
        intent = plan.get("intent")
        params = plan.setdefault("parameters", {})

        def coerce_int(value: Any) -> Optional[int]:
            if value is None:
                return None
            try:
                return int(str(value).strip())
            except (TypeError, ValueError):
                return None

        if intent in {"set_cell_value", "delete_row"}:
            row_number = coerce_int(
                params.get("row") or params.get("row_index") or params.get("row_number")
            )
            if row_number is not None:
                params["row"] = row_number

        if intent == "set_cell_value" and df is not None:
            column_name = params.get("column") or params.get("column_name")
            column_index = coerce_int(params.get("column_index"))
            matched_column = None
            if column_name:
                matched_column = self._match_column(column_name, df)
            if matched_column is None and column_index:
                if 1 <= column_index <= len(df.columns):
                    matched_column = df.columns[column_index - 1]
            if matched_column:
                params["column"] = matched_column
                params["column_name"] = matched_column

        if intent == "add_row":
            row_data = params.get("row_data") or params.get("values")
            normalized_row: Dict[str, Any] = {}
            if isinstance(row_data, dict) and df is not None:
                for key, value in row_data.items():
                    matched_column = self._match_column(key, df)
                    if matched_column:
                        normalized_row[matched_column] = value
            params["row_data"] = normalized_row or row_data

        if intent == "add_column":
            column_name = params.get("column") or params.get("column_name")
            if column_name and df is not None:
                matched = self._match_column(column_name, df)
                if matched and matched != column_name:
                    # If the column already exists, keep the exact match so execution can error gracefully.
                    params["column_name"] = matched
                else:
                    params["column_name"] = column_name

        if intent == "row_math" and df is not None:
            columns = params.get("source_columns")
            if isinstance(columns, str):
                columns = [columns]
            elif not isinstance(columns, list):
                columns = []
            normalized_columns: List[str] = []
            for column in columns:
                matched = self._match_column(column, df)
                if matched:
                    normalized_columns.append(matched)
            params["source_columns"] = normalized_columns

            target_column = params.get("target_column")
            if isinstance(target_column, str):
                params["target_column"] = target_column.strip()

            operation = params.get("operation")
            normalized_operation = self._normalize_row_math_operation(operation)
            if normalized_operation:
                params["operation"] = normalized_operation
            elif operation is None:
                params["operation"] = "sum"

        if intent == "aggregate" and df is not None:
            group_by = params.get("group_by")
            if isinstance(group_by, str):
                group_by = [group_by]
            elif not isinstance(group_by, list):
                group_by = []
            normalized_group_by: List[str] = []
            for column in group_by:
                matched = self._match_column(column, df)
                if matched:
                    normalized_group_by.append(matched)
            params["group_by"] = normalized_group_by

            metrics = params.get("metrics")
            if isinstance(metrics, dict):
                metrics = [metrics]
            elif not isinstance(metrics, list):
                metrics = []

            normalized_metrics: List[Dict[str, Any]] = []
            for metric in metrics:
                if not isinstance(metric, dict):
                    continue
                metric_copy: Dict[str, Any] = {}
                column_ref = metric.get("column") or metric.get("field")
                if column_ref:
                    matched_column = self._match_column(column_ref, df)
                    if matched_column:
                        metric_copy["column"] = matched_column
                operation_ref = (
                    metric.get("operation")
                    or metric.get("op")
                    or metric.get("aggregate")
                    or metric.get("metric")
                )
                normalized_operation = self._normalize_operation(operation_ref)
                if normalized_operation:
                    metric_copy["operation"] = normalized_operation
                if metric_copy:
                    normalized_metrics.append(metric_copy)
            params["metrics"] = normalized_metrics

            conditions = params.get("conditions")
            if isinstance(conditions, dict):
                conditions = [conditions]
            elif not isinstance(conditions, list):
                conditions = []
            normalized_conditions: List[Dict[str, Any]] = []
            for condition in conditions:
                if not isinstance(condition, dict):
                    continue
                normalized_condition = dict(condition)
                column_reference = (
                    normalized_condition.get("column") or normalized_condition.get("field")
                )
                if column_reference:
                    matched_column = self._match_column(column_reference, df)
                    if matched_column:
                        normalized_condition["column"] = matched_column
                operator = normalized_condition.get("operator")
                if operator:
                    normalized_condition["operator"] = str(operator).lower()
                normalized_conditions.append(normalized_condition)
            if normalized_conditions:
                params["conditions"] = normalized_conditions
            else:
                params.pop("conditions", None)


        if intent in {"filter_rows", "delete_rows"}:
            conditions = params.get("conditions")
            if isinstance(conditions, dict):
                conditions = [conditions]
            elif not isinstance(conditions, list):
                conditions = []
            normalized_conditions: List[Dict[str, Any]] = []
            for condition in conditions:
                if not isinstance(condition, dict):
                    continue
                normalized_condition = dict(condition)
                if df is not None:
                    column_reference = (
                        normalized_condition.get("column")
                        or normalized_condition.get("field")
                    )
                    if column_reference:
                        matched_column = self._match_column(column_reference, df)
                        if matched_column:
                            normalized_condition["column"] = matched_column
                    operator = normalized_condition.get("operator")
                    if operator:
                        normalized_condition["operator"] = str(operator).lower()
                normalized_conditions.append(normalized_condition)
            params["conditions"] = normalized_conditions

        if intent in {"plot_line", "plot_bar"} and df is not None:
            y_column = params.get("y_column") or params.get("column") or params.get("metric")
            x_column = params.get("x_column") or params.get("dimension") or params.get("x")
            if y_column:
                matched_y = self._match_column(y_column, df)
                if matched_y:
                    params["y_column"] = matched_y
            if x_column:
                matched_x = self._match_column(x_column, df)
                if matched_x:
                    params["x_column"] = matched_x

        if hints and hints.get("parameters"):
            for key, value in hints["parameters"].items():
                params.setdefault(key, value)

        plan["parameters"] = params
        return plan

    def _build_intent_hint_arguments(
        self, detection: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        hints = {
            "hint_intent": "",
            "hint_parameters": "",
            "hint_confidence": "",
        }
        if not detection:
            return hints
        if detection.get("intent"):
            hints["hint_intent"] = str(detection["intent"])
        if detection.get("parameters"):
            try:
                hints["hint_parameters"] = json.dumps(
                    detection["parameters"], ensure_ascii=False
                )
            except (TypeError, ValueError):
                hints["hint_parameters"] = ""
        if detection.get("confidence"):
            hints["hint_confidence"] = str(detection["confidence"])
        return hints

    def _detect_user_intent(
        self, question: str, df: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        text = question.strip()
        if not text:
            return None

        lowered = text.lower()
        candidates: List[Dict[str, Any]] = []
        confidence_rank = {"low": 0, "medium": 1, "certain": 2}

        def add_candidate(intent: str, parameters: Dict[str, Any], confidence: str) -> None:
            candidates.append(
                {
                    "intent": intent,
                    "parameters": parameters,
                    "confidence": confidence,
                }
            )

        row_match = re.search(r"row\s+(?P<row>\d+)", lowered)
        column_number_match = re.search(r"column\s+(?P<column>\d+)", lowered)

        quoted_column_match = re.search(
            r"column(?:\s+named)?\s+['\"]([^'\"]+)['\"]", question, re.IGNORECASE
        )

        detected_columns: List[str] = []
        if quoted_column_match:
            matched = self._match_column(quoted_column_match.group(1), df)
            if matched:
                detected_columns.append(matched)

        normalized_text = self._normalize_phrase(text)
        for column in df.columns:
            normalized_column = self._normalize_phrase(column)
            if normalized_column and normalized_column in normalized_text:
                if column not in detected_columns:
                    detected_columns.append(column)

        detected_column_name = detected_columns[0] if detected_columns else None

        value_match = re.search(
            r"\b(?:to|as)\s+['\"]?([^'\"\n\r]+?)['\"]?(?:\s|$)", question, re.IGNORECASE
        )
        equality_match = re.search(r"=\s*['\"]?([^'\"\n\r]+?)['\"]?(?:\s|$)", question)

        resolved_value = None
        if value_match:
            resolved_value = value_match.group(1).strip().rstrip(".")
        elif equality_match:
            resolved_value = equality_match.group(1).strip().rstrip(".")

        clear_keywords = {"clear", "blank", "empty", "remove value"}
        is_clear_request = any(keyword in lowered for keyword in clear_keywords)
        set_keywords = {"set", "update", "change", "replace", "overwrite", "modify"}
        is_set_request = any(keyword in lowered for keyword in set_keywords)

        if row_match and (is_set_request or is_clear_request):
            params: Dict[str, Any] = {"row": int(row_match.group("row"))}
            if column_number_match:
                params["column_index"] = int(column_number_match.group("column"))
            if detected_column_name:
                params["column_name"] = detected_column_name
            if resolved_value is not None:
                params["value"] = resolved_value
            elif is_clear_request:
                params["value"] = ""

            if ("column_index" in params or "column_name" in params) and "value" in params:
                add_candidate("set_cell_value", params, "certain")
            elif ("column_index" in params or "column_name" in params):
                add_candidate("set_cell_value", params, "medium")

        if row_match and any(keyword in lowered for keyword in ("delete", "remove")):
            params = {"row": int(row_match.group("row"))}
            add_candidate("delete_row", params, "certain")

        add_row_keywords = (
            "add row",
            "insert row",
            "add record",
            "new record",
            "new entry",
            "add entry",
            "add user",
            "create row",
        )
        if any(keyword in lowered for keyword in add_row_keywords):
            inferred_conditions = self._infer_conditions_from_text(question, df)
            params: Dict[str, Any] = {}
            if inferred_conditions:
                # Treat inferred values as potential row data hints for the planner.
                params["row_data"] = {
                    condition.get("column", ""): condition.get("value")
                    for condition in inferred_conditions
                    if condition.get("column") and condition.get("value") is not None
                }
            add_candidate("add_row", params, "medium")

        add_column_keywords = (
            "add column",
            "create column",
            "new column",
            "insert column",
        )
        if any(keyword in lowered for keyword in add_column_keywords):
            params: Dict[str, Any] = {}
            if detected_column_name:
                params["column_name"] = detected_column_name
            add_candidate("add_column", params, "medium")

        aggregate_patterns = [
            ("sum", ["sum", "total", "add up", "overall total"]),
            ("mean", ["average", "avg", "mean"]),
            ("median", ["median"]),
            ("max", ["maximum", "highest", "largest", "max"]),
            ("min", ["minimum", "lowest", "smallest", "min"]),
            ("count", ["count", "how many", "number of", "total rows"]),
            ("std", ["standard deviation", "stdev", "std"]),
            ("var", ["variance", "var"]),
        ]
        grouping_candidates: List[str] = []
        for group_match in re.findall(r"\bby\s+([A-Za-z0-9 _\-]+)", question, re.IGNORECASE):
            matched_group = self._match_column(group_match, df)
            if matched_group and matched_group not in grouping_candidates:
                grouping_candidates.append(matched_group)

        candidate_columns = list(dict.fromkeys(detected_columns))
        if not candidate_columns:
            possible_columns = []
            for column in df.columns:
                normalized_column = self._normalize_phrase(column)
                if normalized_column and normalized_column in lowered:
                    possible_columns.append(column)
            candidate_columns = list(dict.fromkeys(possible_columns))
        if len(candidate_columns) < 2:
            inferred_columns: List[str] = []
            for match in re.findall(r"([A-Za-z0-9 _]+score)", question, re.IGNORECASE):
                matched_column = self._match_column(match, df)
                if matched_column and matched_column not in inferred_columns:
                    inferred_columns.append(matched_column)
            if len(inferred_columns) > len(candidate_columns):
                candidate_columns = inferred_columns

        row_context_keywords = (
            "per row",
            "each row",
            "for each row",
            "for every row",
            "row-wise",
            "for all the row",
            "for all rows",
            "row by row",
        )
        row_context = any(keyword in lowered for keyword in row_context_keywords)
        create_new_column = bool(
            "new column" in lowered
            or "add the data to" in lowered
            or re.search(
                r"\b(add|create|make|insert|generate)\b(?:\s+\w+){0,4}\s+column",
                lowered,
            )
        )

        target_column_match = re.search(
            r"(?:new\s+column\s+(?:named|called)|column\s+named|call\s+it)\s+['\"]?([A-Za-z0-9 _\-]+)['\"]?",
            question,
            re.IGNORECASE,
        )
        target_column_name = (
            target_column_match.group(1).strip() if target_column_match else None
        )
        if not target_column_name:
            add_column_pattern = re.search(
                r"\b(?:add|create|make|insert|generate)\s+(?:a|an|the|new)?\s*([A-Za-z0-9 _\-]+?)\s+column\b",
                question,
                re.IGNORECASE,
            )
            if add_column_pattern:
                target_column_name = add_column_pattern.group(1).strip()

        simple_filter_conditions = self._extract_simple_filter_conditions(question, df)
        trailing_clause_pattern = re.compile(
            r"\b(only|where|with|for|by|if|when|excluding|except)\b",
            re.IGNORECASE,
        )

        row_math_operation = None
        row_math_priority = ["difference", "product", "ratio", "sum", "mean"]
        for canonical in row_math_priority:
            aliases = _ROW_MATH_ALIASES.get(canonical, set())
            if any(alias in normalized_text for alias in aliases):
                row_math_operation = canonical
                break

        if row_math_operation:
            source_columns = candidate_columns
            if row_math_operation == "ratio" and len(source_columns) >= 2:
                source_columns = source_columns[:2]
            if len(source_columns) >= 2 and (
                row_math_operation in {"difference", "product", "ratio"}
                or row_context
                or create_new_column
            ):
                params: Dict[str, Any] = {
                    "operation": row_math_operation,
                    "source_columns": source_columns,
                }
                if target_column_name:
                    params["target_column"] = target_column_name
                confidence = (
                    "certain"
                    if row_context or row_math_operation in {"difference", "product", "ratio"}
                    else "medium"
                )
                add_candidate("row_math", params, confidence)

        for operation, keywords in aggregate_patterns:
            if not any(keyword in lowered for keyword in keywords):
                continue

            matched_column = detected_column_name
            numeric_required = operation in {
                "sum",
                "mean",
                "median",
                "max",
                "min",
                "std",
                "var",
            }
            if matched_column and numeric_required and not is_numeric_dtype(df[matched_column]):
                matched_column = None
            if not matched_column:
                for keyword in keywords:
                    pattern = re.compile(
                        rf"{re.escape(keyword)}(?:\s+of|\s+for|\s+the|\s+all)?\s+([A-Za-z0-9 _\-]+)",
                        re.IGNORECASE,
                    )
                    match = pattern.search(question)
                    if match:
                        candidate_column = match.group(1)
                        candidate_column = trailing_clause_pattern.split(candidate_column)[
                            0
                        ]
                        candidate_column = candidate_column.strip(" '\".")
                        matched = self._match_column(candidate_column, df)
                        if matched:
                            matched_column = matched
                            break

            if matched_column is None and numeric_required:
                for column in candidate_columns:
                    if is_numeric_dtype(df[column]):
                        matched_column = column
                        break

            if matched_column is None and operation != "count":
                continue

            params: Dict[str, Any] = {
                "metrics": [
                    {
                        "column": matched_column,
                        "operation": operation,
                    }
                ]
            }
            if grouping_candidates:
                params["group_by"] = grouping_candidates
            if simple_filter_conditions:
                params["conditions"] = simple_filter_conditions
            confidence = "certain" if matched_column else "medium"
            add_candidate("aggregate", params, confidence)
            break

        bulk_delete_keywords = (
            "delete all",
            "remove all",
            "delete rows",
            "remove rows",
            "delete records",
            "remove records",
            "delete entries",
            "remove entries",
            "drop all",
        )
        if any(keyword in lowered for keyword in bulk_delete_keywords):
            inferred_conditions = self._infer_conditions_from_text(question, df)
            if (
                not inferred_conditions
                and detected_column_name
                and resolved_value is not None
            ):
                inferred_conditions = [
                    {
                        "column": detected_column_name,
                        "operator": "=",
                        "value": resolved_value,
                    }
                ]
            if inferred_conditions:
                add_candidate(
                    "delete_rows",
                    {"conditions": inferred_conditions},
                    "certain",
                )

        if any(
            keyword in lowered for keyword in ("plot", "chart", "graph", "visualize")
        ):
            plot_type = "plot_line"
            if any(keyword in lowered for keyword in ("bar", "histogram", "hist")):
                plot_type = "plot_bar"

            plot_pattern = re.search(
                r"(?:plot|graph|chart|visualize)\s+(?:a\s+)?"
                r"(?P<type>line|bar|histogram)?\s*(?:chart|graph)?"
                r"(?:\s+of)?\s+(?P<y>[A-Za-z0-9 _\-.%']+?)"
                r"(?:\s+(?:over|against|versus|vs|by)\s+(?P<x>[A-Za-z0-9 _\-.%']+))?",
                question,
                re.IGNORECASE,
            )

            y_column_text = None
            x_column_text = None
            if plot_pattern:
                if plot_pattern.group("type"):
                    pt = plot_pattern.group("type").lower()
                    if "bar" in pt or "hist" in pt:
                        plot_type = "plot_bar"
                y_column_text = plot_pattern.group("y")
                x_column_text = plot_pattern.group("x")

            if not y_column_text and detected_column_name:
                y_column_text = detected_column_name

            y_column = (
                self._match_column(y_column_text, df) if y_column_text else None
            )
            x_column = self._match_column(x_column_text, df) if x_column_text else None

            if not y_column:
                y_column = self._find_first_numeric_column(df)

            if y_column:
                params = {"y_column": y_column}
                if x_column:
                    params["x_column"] = x_column
                params.setdefault(
                    "title",
                    f"{y_column} {'by ' + x_column if x_column else 'trend'}",
                )
                confidence = "certain" if x_column else "medium"
                add_candidate(plot_type, params, confidence)

        if not candidates:
            return None

        candidates.sort(
            key=lambda candidate: confidence_rank.get(candidate["confidence"], 0),
            reverse=True,
        )
        return candidates[0]

    def _infer_conditions_from_text(
        self, question: str, df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        candidate_values: List[str] = []

        quoted_matches = re.findall(r"'([^']+)'|\"([^\"]+)\"", question)
        for first, second in quoted_matches:
            value = first or second
            if value:
                candidate_values.append(value.strip())

        numeric_matches = re.findall(r"\b\d+(?:\.\d+)?\b", question)
        for match in numeric_matches:
            candidate_values.append(match.strip())

        # Deduplicate while preserving order.
        seen: set[str] = set()
        ordered_values: List[str] = []
        for value in candidate_values:
            cleaned = value.strip().strip(",.")
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                ordered_values.append(cleaned)

        conditions: List[Dict[str, Any]] = []
        for raw_value in ordered_values:
            matched_column = None
            for column in df.columns:
                series = df[column]
                typed_value = self._coerce_value(raw_value, series)
                if pd.isna(typed_value):
                    typed_value = raw_value
                try:
                    mask = self._apply_condition(series, "=", typed_value)
                except Exception:
                    continue
                if mask.any():
                    matched_column = column
                    break
            if matched_column:
                conditions.append(
                    {
                        "column": matched_column,
                        "operator": "=",
                        "value": raw_value,
                    }
                )
        return conditions

    def _normalize_phrase(self, value: str) -> str:
        sanitized = re.sub(r"[^a-z0-9]+", " ", value.lower())
        return re.sub(r"\s+", " ", sanitized).strip()

    def _normalize_operation(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        normalized_text = self._normalize_phrase(str(value))
        if not normalized_text:
            return None
        if normalized_text in _AGGREGATION_ALIASES:
            return _AGGREGATION_ALIASES[normalized_text]
        # If the normalized_text already matches a canonical operation, keep it.
        if normalized_text in _AGGREGATION_ALIASES.values():
            return normalized_text
        return None

    def _extract_simple_filter_conditions(
        self, question: str, df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        normalized_question = self._normalize_phrase(question)
        conditions: List[Dict[str, Any]] = []

        for column in df.columns:
            normalized_column = self._normalize_phrase(column)
            if not normalized_column:
                continue

            pattern = re.compile(
                rf"(?:only\s+for|just\s+for|for|where)\s+(?:the\s+)?(?P<value>[a-z0-9 _\-]+?)\s+{re.escape(normalized_column)}(?:\b|$)"
            )
            matches = list(pattern.finditer(normalized_question))
            if not matches:
                continue
            value_candidate = matches[-1].group("value").strip(" ,.")
            if not value_candidate:
                continue
            conditions.append(
                {
                    "column": column,
                    "operator": "=",
                    "value": value_candidate,
                }
            )
        return conditions

    def _normalize_row_math_operation(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        normalized_text = self._normalize_phrase(str(value))
        if not normalized_text:
            return None
        for canonical, aliases in _ROW_MATH_ALIASES.items():
            if normalized_text in aliases:
                return canonical
        return None

    def _match_column(self, reference: Any, df: pd.DataFrame) -> Optional[str]:
        if reference is None:
            return None
        reference_text = self._normalize_phrase(str(reference))
        if not reference_text:
            return None

        for column in df.columns:
            if reference_text == self._normalize_phrase(column):
                return column

        for column in df.columns:
            normalized_column = self._normalize_phrase(column)
            if normalized_column and (
                normalized_column in reference_text or reference_text in normalized_column
            ):
                return column
        return None

    def _find_first_numeric_column(self, df: pd.DataFrame) -> Optional[str]:
        for column in df.columns:
            series = df[column]
            if is_numeric_dtype(series):
                return column
        return None

    def _execute_plan(
        self,
        plan: Dict[str, Any],
        df: pd.DataFrame,
        metadata: Dict[str, Any],
        *,
        question: str,
    ) -> ExecutionResult:
        intent = plan["intent"]
        params = plan.get("parameters", {})

        if intent == "dataset_overview":
            summary, table = self._summarize_dataset(metadata, df)
            return ExecutionResult(summary=summary, table_markdown=table)

        if intent == "list_columns":
            lines = [
                f"- `{info['name']}` — dtype: {info['dtype']}, missing values: {info['nulls']}"
                for info in metadata["column_info"]
            ]
            summary = "Columns detected:\n" + "\n".join(lines)
            return ExecutionResult(summary=summary)

        if intent == "describe_column":
            column = params.get("column")
            if not column:
                raise CSVAgentError("The agent did not specify which column to describe.")
            if column not in df.columns:
                raise CSVAgentError(f"Column '{column}' does not exist in the dataset.")
            series = df[column]
            description_lines = self._describe_series(series, column)
            return ExecutionResult(summary="\n".join(description_lines))

        if intent == "filter_rows":
            return self._execute_filter(df, params)

        if intent == "aggregate":
            return self._execute_aggregate(df, params)

        if intent == "value_counts":
            column = params.get("column")
            limit = int(params.get("limit") or 10)
            if not column:
                raise CSVAgentError("The agent did not specify a column for value counts.")
            if column not in df.columns:
                raise CSVAgentError(f"Column '{column}' does not exist in the dataset.")
            series = df[column]
            value_counts = series.value_counts(dropna=False).head(limit).rename("count")
            table = self._format_dataframe(value_counts.reset_index(names=[column]))
            summary = (
                f"Top {min(limit, len(value_counts))} value counts for `{column}`."
            )
            return ExecutionResult(summary=summary, table_markdown=table)

        if intent == "top_n":
            column = params.get("column")
            limit = int(params.get("limit") or 5)
            ascending = bool(params.get("ascending", False))
            if not column:
                raise CSVAgentError("The agent did not specify a column for ranking.")
            if column not in df.columns:
                raise CSVAgentError(f"Column '{column}' does not exist in the dataset.")
            series = df[column]
            if not is_numeric_dtype(series):
                raise CSVAgentError(
                    f"Column '{column}' must be numeric to compute rankings."
                )
            if ascending:
                ranked = df.nsmallest(limit, column)
                summary = f"Smallest {limit} rows by `{column}`."
            else:
                ranked = df.nlargest(limit, column)
                summary = f"Largest {limit} rows by `{column}`."
            table = self._format_dataframe(ranked)
            return ExecutionResult(summary=summary, table_markdown=table)

        if intent == "set_cell_value":
            return self._execute_set_cell_value(df, metadata, params)

        if intent == "add_row":
            return self._execute_add_row(df, metadata, params)

        if intent == "add_column":
            return self._execute_add_column(df, metadata, params)

        if intent == "row_math":
            return self._execute_row_math(df, metadata, params)

        if intent == "delete_row":
            return self._execute_delete_row(df, metadata, params)

        if intent == "delete_rows":
            return self._execute_delete_rows(df, metadata, params)

        if intent in {"plot_line", "plot_bar"}:
            return self._execute_plot(df, metadata, params, plot_type=intent)

        if intent == "raw_answer":
            params = plan.get("parameters", {})
            reason = params.get("reason")
            summary, table = self._summarize_dataset(metadata, df)
            base_message = (
                "I could not map the request to a supported structured operation."
            )
            if reason:
                base_message += f" {reason}"
            base_message += " Here's a refreshed dataset overview."
            return ExecutionResult(
                summary=base_message,
                table_markdown=table,
            )

        raise CSVAgentError(f"Unsupported intent: {intent}")

    def _execute_set_cell_value(
        self, df: pd.DataFrame, metadata: Dict[str, Any], params: Dict[str, Any]
    ) -> ExecutionResult:
        row_number = params.get("row") or params.get("row_index") or params.get("row_number")
        column_name = params.get("column") or params.get("column_name")
        column_index = params.get("column_index")
        value = params.get("value") if "value" in params else params.get("new_value")

        if row_number is None:
            raise CSVAgentError("The agent did not specify which row to update.")
        try:
            row_number = int(row_number)
        except ValueError as exc:
            raise CSVAgentError("Row numbers must be integers.") from exc

        if row_number < 1 or row_number > len(df):
            raise CSVAgentError(
                f"Row {row_number} is out of range for this dataset (total rows: {len(df)})."
            )

        if column_name is None and column_index is None:
            raise CSVAgentError("The agent did not specify which column to update.")

        df_copy = df.copy()

        if column_name is not None:
            column_name = str(column_name)
            if column_name not in df_copy.columns:
                matched = self._match_column(column_name, df_copy)
                if matched:
                    column_name = matched
                else:
                    raise CSVAgentError(f"Column '{column_name}' does not exist in this dataset.")
        else:
            try:
                column_index = int(column_index)
            except (TypeError, ValueError) as exc:
                raise CSVAgentError("Column index must be an integer.") from exc
            if column_index < 1 or column_index > df_copy.shape[1]:
                raise CSVAgentError(
                    f"Column {column_index} is out of range for this dataset (total columns: {df_copy.shape[1]})."
                )
            column_name = df_copy.columns[column_index - 1]

        row_index = row_number - 1
        series = df_copy[column_name]
        typed_value = self._coerce_value(value, series) if value not in (None, "") else None
        df_copy.iat[row_index, df_copy.columns.get_loc(column_name)] = typed_value

        self._persist_dataframe(df_copy, metadata)
        preview = self._format_dataframe(df_copy)

        display_value = "blank" if typed_value in (None, "") or pd.isna(typed_value) else str(typed_value)
        summary = (
            f"Updated row {row_number}, column `{column_name}` to `{display_value}`. "
            "The dataset has been saved with this change. Use the Download CSV button to grab the latest file."
        )
        return ExecutionResult(summary=summary, table_markdown=preview)

    def _execute_add_row(
        self, df: pd.DataFrame, metadata: Dict[str, Any], params: Dict[str, Any]
    ) -> ExecutionResult:
        row_data = params.get("row_data") or params.get("values")
        if isinstance(row_data, list):
            row_data = dict(zip(df.columns, row_data))

        if not isinstance(row_data, dict) or not row_data:
            raise CSVAgentError("The agent did not specify any column values for the new row.")

        df_copy = df.copy()
        new_row: Dict[str, Any] = {}
        provided_columns = set()

        for key, value in row_data.items():
            column = key
            if column not in df_copy.columns:
                matched = self._match_column(column, df_copy)
                if matched:
                    column = matched
            if column in df_copy.columns:
                series = df_copy[column]
                typed_value = self._coerce_value(value, series)
                if pd.isna(typed_value):
                    typed_value = value
                new_row[column] = typed_value
                provided_columns.add(column)

        if not new_row:
            raise CSVAgentError(
                "None of the provided fields matched existing columns. Please specify valid column names."
            )

        for column in df_copy.columns:
            if column not in provided_columns:
                new_row[column] = pd.NA

        df_copy = pd.concat([df_copy, pd.DataFrame([new_row])], ignore_index=True)
        self._persist_dataframe(df_copy, metadata)
        preview = self._format_dataframe(df_copy)
        download_link = self._build_download_link(metadata)
        summary = (
            f"Added a new row to `{metadata.get('filename')}`. "
            f"The dataset now has {len(df_copy)} rows. "
            f"[Download updated CSV]({download_link})."
        )
        return ExecutionResult(summary=summary, table_markdown=preview)

    def _execute_add_column(
        self, df: pd.DataFrame, metadata: Dict[str, Any], params: Dict[str, Any]
    ) -> ExecutionResult:
        column_name = params.get("column_name") or params.get("column")
        if not column_name:
            raise CSVAgentError("The agent did not specify a column name to add.")

        normalized_name = column_name.strip()
        if not normalized_name:
            raise CSVAgentError("Column name cannot be blank.")

        df_copy = df.copy()
        if normalized_name in df_copy.columns:
            raise CSVAgentError(f"Column `{normalized_name}` already exists.")

        values = params.get("values")
        default_value = params.get("default_value")

        if values is not None:
            if not isinstance(values, (list, tuple)):
                raise CSVAgentError("Column values must be provided as a list.")
            if len(values) not in {len(df_copy), 0}:
                raise CSVAgentError(
                    f"Expected {len(df_copy)} values for the new column but received {len(values)}."
                )
            series = pd.Series(values, dtype="object")
        else:
            fill_value = default_value if default_value is not None else pd.NA
            series = pd.Series([fill_value] * len(df_copy), dtype="object")

        df_copy[normalized_name] = series.tolist()
        self._persist_dataframe(df_copy, metadata)
        preview = self._format_dataframe(df_copy)
        download_link = self._build_download_link(metadata)
        summary = (
            f"Added column `{normalized_name}` to `{metadata.get('filename')}`. "
            f"[Download updated CSV]({download_link})."
        )
        return ExecutionResult(summary=summary, table_markdown=preview)

    def _execute_row_math(
        self, df: pd.DataFrame, metadata: Dict[str, Any], params: Dict[str, Any]
    ) -> ExecutionResult:
        requested_operation = params.get("operation") or "sum"
        operation = self._normalize_row_math_operation(requested_operation)
        if operation is None:
            supported = ", ".join(_ROW_MATH_SUPPORTED_OPERATIONS)
            raise CSVAgentError(
                f"Unsupported row-wise operation '{requested_operation}'. "
                f"Supported operations are: {supported}."
            )

        source_columns_raw = params.get("source_columns") or []
        if isinstance(source_columns_raw, str):
            source_columns = [source_columns_raw]
        else:
            source_columns = list(source_columns_raw)
        source_columns = list(dict.fromkeys(source_columns))

        if len(source_columns) < 2:
            raise CSVAgentError("Row calculations require at least two source columns.")

        missing = [column for column in source_columns if column not in df.columns]
        if missing:
            raise CSVAgentError(
                f"These columns do not exist in the dataset: {', '.join(missing)}"
            )

        numeric_columns = [
            column for column in source_columns if is_numeric_dtype(df[column])
        ]
        if len(numeric_columns) != len(source_columns):
            raise CSVAgentError(
                "Row calculations can only be performed on numeric columns."
            )

        if operation == "ratio" and len(source_columns) != 2:
            raise CSVAgentError(
                "Ratio calculations require exactly two source columns "
                "(numerator and denominator)."
            )

        target_column = params.get("target_column") or ""
        normalized_target = target_column.strip() or f"{operation}_" + "_".join(
            source_columns
        )
        if normalized_target in df.columns:
            raise CSVAgentError(
                f"Column `{normalized_target}` already exists. Choose a different name."
            )

        df_copy = df.copy()
        numeric_frame = df_copy[source_columns].apply(pd.to_numeric, errors="coerce")

        if operation == "sum":
            result_series = numeric_frame.sum(axis=1, skipna=True)
        elif operation == "mean":
            result_series = numeric_frame.mean(axis=1, skipna=True)
        elif operation == "difference":
            operands = numeric_frame.fillna(0)
            result_series = operands.iloc[:, 0].copy()
            for column in operands.columns[1:]:
                result_series = result_series - operands[column]
        elif operation == "product":
            result_series = numeric_frame.prod(axis=1, skipna=True)
        elif operation == "ratio":
            numerator = numeric_frame.iloc[:, 0]
            denominator = numeric_frame.iloc[:, 1]
            with np.errstate(divide="ignore", invalid="ignore"):
                result_series = numerator / denominator
            result_series = result_series.replace([np.inf, -np.inf], np.nan)
        else:
            supported = ", ".join(_ROW_MATH_SUPPORTED_OPERATIONS)
            raise CSVAgentError(
                f"Unsupported row-wise operation '{operation}'. "
                f"Supported operations are: {supported}."
            )

        df_copy[normalized_target] = result_series
        self._persist_dataframe(df_copy, metadata)
        preview = self._format_dataframe(df_copy)
        download_link = self._build_download_link(metadata)

        formatted_sources = ", ".join(f"`{col}`" for col in source_columns)
        if operation == "sum":
            description = f"row-wise sum of {formatted_sources}"
        elif operation == "mean":
            description = f"row-wise average of {formatted_sources}"
        elif operation == "difference":
            if len(source_columns) == 2:
                description = (
                    f"row-wise difference (`{source_columns[0]}` minus `{source_columns[1]}`)"
                )
            else:
                remaining = ", ".join(f"`{col}`" for col in source_columns[1:])
                description = (
                    f"row-wise difference starting from `{source_columns[0]}` "
                    f"minus {remaining}"
                )
        elif operation == "product":
            description = f"row-wise product of {formatted_sources}"
        else:  # ratio
            description = (
                f"row-wise ratio of `{source_columns[0]}` divided by `{source_columns[1]}`"
            )

        summary = (
            f"Added column `{normalized_target}` containing the {description}. "
            f"[Download updated CSV]({download_link})."
        )
        return ExecutionResult(summary=summary, table_markdown=preview)

    def _build_download_link(self, metadata: Dict[str, Any]) -> str:
        base_url = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000").rstrip("/")
        dataset_id = metadata.get("dataset_id")
        if not dataset_id:
            return base_url
        return f"{base_url}/agent/csv/export/{dataset_id}"

    def _execute_delete_rows(
        self, df: pd.DataFrame, metadata: Dict[str, Any], params: Dict[str, Any]
    ) -> ExecutionResult:
        conditions = params.get("conditions") or []
        if not isinstance(conditions, list) or not conditions:
            raise CSVAgentError("The agent did not specify which rows to delete.")

        mask = pd.Series([True] * len(df))
        readable_conditions: List[str] = []
        supported_ops = {
            "=",
            "!=",
            ">",
            "<",
            ">=",
            "<=",
            "contains",
            "not_contains",
        }

        for condition in conditions:
            if not isinstance(condition, dict):
                continue
            column = condition.get("column")
            operator = str(condition.get("operator") or "=").lower()
            value = condition.get("value")
            if not column:
                continue
            if column not in df.columns:
                matched = self._match_column(column, df)
                if not matched:
                    continue
                column = matched
            if operator not in supported_ops:
                continue

            series = df[column]
            typed_value = self._coerce_value(value, series)
            if pd.isna(typed_value):
                typed_value = value

            try:
                condition_mask = self._apply_condition(series, operator, typed_value)
            except Exception as exc:
                raise CSVAgentError(
                    f"Unable to apply delete condition on column '{column}': {exc}"
                ) from exc

            mask &= condition_mask.fillna(False)
            readable_operator = {
                "=": "=",
                "!=": "≠",
                ">": ">",
                "<": "<",
                ">=": "≥",
                "<=": "≤",
                "contains": "contains",
                "not_contains": "does not contain",
            }.get(operator, operator)
            readable_conditions.append(f"`{column}` {readable_operator} `{value}`")

        matches = mask.sum()
        if matches == 0:
            preview = self._format_dataframe(df)
            summary = (
                "No rows matched the delete conditions; the dataset remains unchanged."
            )
            return ExecutionResult(summary=summary, table_markdown=preview)

        df_copy = df.loc[~mask].reset_index(drop=True)
        self._persist_dataframe(df_copy, metadata)
        preview = self._format_dataframe(df_copy)
        download_link = self._build_download_link(metadata)
        summary = (
            f"Deleted {int(matches)} row{'s' if matches != 1 else ''} where "
            f"{', '.join(readable_conditions)}. "
            f"The dataset now has {len(df_copy)} rows. "
            f"[Download updated CSV]({download_link})."
        )
        return ExecutionResult(summary=summary, table_markdown=preview)

    def _execute_delete_row(
        self, df: pd.DataFrame, metadata: Dict[str, Any], params: Dict[str, Any]
    ) -> ExecutionResult:
        row_number = params.get("row") or params.get("row_index") or params.get("row_number")
        if row_number is None:
            raise CSVAgentError("The agent did not specify which row to delete.")
        try:
            row_number = int(row_number)
        except ValueError as exc:
            raise CSVAgentError("Row numbers must be integers.") from exc

        if row_number < 1 or row_number > len(df):
            raise CSVAgentError(
                f"Row {row_number} is out of range for this dataset (total rows: {len(df)})."
            )

        df_copy = df.drop(df.index[row_number - 1]).reset_index(drop=True)
        self._persist_dataframe(df_copy, metadata)
        preview = self._format_dataframe(df_copy)
        summary = (
            f"Deleted row {row_number} from the dataset. "
            f"The file now contains {len(df_copy)} rows. Use the Download CSV button to grab the latest file."
        )
        return ExecutionResult(summary=summary, table_markdown=preview)

    def _execute_plot(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any],
        params: Dict[str, Any],
        *,
        plot_type: str,
    ) -> ExecutionResult:
        y_column = params.get("y_column") or params.get("column") or params.get("metric")
        if not y_column:
            raise CSVAgentError("The agent did not specify a column to plot on the y-axis.")
        if y_column not in df.columns:
            raise CSVAgentError(f"Column '{y_column}' does not exist in the dataset.")

        x_column = params.get("x_column") or params.get("dimension") or params.get("x")
        if x_column and x_column not in df.columns:
            raise CSVAgentError(f"Column '{x_column}' does not exist in the dataset.")

        title = params.get("title") or (
            f"{y_column} by {x_column}" if x_column else f"{y_column} Trend"
        )

        data = df.copy()
        if x_column is None:
            data = data.reset_index().rename(columns={"index": "Index"})
            x_column = "Index"

        plot_data = data[[x_column, y_column]].dropna()
        if plot_data.empty:
            raise CSVAgentError("There is no data available to plot after removing missing values.")

        fig, ax = plt.subplots(figsize=(7, 4))
        if plot_type == "plot_line":
            ax.plot(plot_data[x_column], plot_data[y_column], marker="o")
        else:
            ax.bar(plot_data[x_column], plot_data[y_column])
        ax.set_title(title)
        ax.set_xlabel(x_column)
        ax.set_ylabel(y_column)
        ax.grid(True, linestyle="--", alpha=0.3)

        fig.tight_layout()

        dataset_id = metadata.get("dataset_id")
        if not dataset_id:
            raise CSVAgentError("Dataset metadata is missing the dataset identifier.")
        assets_dir = (self.storage_dir / dataset_id) / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        filename = f"plot_{uuid4().hex}.png"
        file_path = assets_dir / filename
        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        plt.close(fig)
        image_bytes = buffer.getvalue()
        file_path.write_bytes(image_bytes)
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        markdown_image = f"![{title}](data:image/png;base64,{encoded})"
        summary = (
            f"Generated a {'line' if plot_type == 'plot_line' else 'bar'} chart for `{y_column}`"
            f"{' by `' + x_column + '`' if x_column else ''}. "
            "The visualization is embedded below and saved to the session assets for later download."
        )
        return ExecutionResult(summary=summary, table_markdown=markdown_image)

    def _persist_dataframe(self, dataframe: pd.DataFrame, metadata: Dict[str, Any]) -> None:
        dataset_id = metadata.get("dataset_id")
        if not dataset_id:
            raise CSVAgentError("Dataset metadata is incomplete; missing dataset identifier.")

        dataset_dir = self.storage_dir / dataset_id
        csv_path = dataset_dir / "data.csv"
        dataframe.to_csv(csv_path, index=False)

        updated_meta = self._build_metadata(
            dataset_id=dataset_id,
            session_id=metadata.get("session_id"),
            user_id=metadata.get("user_id"),
            filename=metadata.get("filename", "dataset.csv"),
            dataframe=dataframe,
        )
        # Preserve the original creation timestamp if available and add an updated timestamp.
        if "created_at" in metadata:
            updated_meta["created_at"] = metadata["created_at"]
        updated_meta["updated_at"] = datetime.utcnow().isoformat() + "Z"

        meta_path = dataset_dir / "meta.json"
        meta_path.write_text(json.dumps(updated_meta, indent=2), encoding="utf-8")
        metadata.clear()
        metadata.update(updated_meta)

    def _describe_series(self, series: pd.Series, column: str) -> List[str]:
        lines = [f"Column `{column}` summary:"]
        lines.append(f"- Data type: {series.dtype}")
        lines.append(f"- Non-null values: {series.count()} (missing: {series.isna().sum()})")

        if is_numeric_dtype(series):
            desc = series.describe().to_dict()
            lines.extend(
                f"- {key.capitalize()}: {value:.4f}" for key, value in desc.items()
            )
        elif is_datetime64_any_dtype(series):
            converted = pd.to_datetime(series, errors="coerce")
            lines.append(f"- Earliest: {converted.min()}")
            lines.append(f"- Latest: {converted.max()}")
        else:
            most_common = series.value_counts(dropna=True).head(5)
            if not most_common.empty:
                lines.append("- Most frequent values:")
                for index, count in most_common.items():
                    lines.append(f"  - {index} ({count} occurrences)")

        examples = series.dropna().astype(str).head(5).tolist()
        if examples:
            lines.append("- Sample values: " + ", ".join(examples))
        return lines

    def _execute_filter(self, df: pd.DataFrame, params: Dict[str, Any]) -> ExecutionResult:
        conditions = params.get("conditions")
        limit = int(params.get("limit") or 20)
        if not conditions:
            raise CSVAgentError("The agent did not provide any filter conditions.")

        mask = pd.Series([True] * len(df))
        summaries: List[str] = []

        for condition in conditions:
            column = condition.get("column")
            operator = condition.get("operator")
            value = condition.get("value")

            if column not in df.columns:
                raise CSVAgentError(f"Column '{column}' does not exist in the dataset.")
            if operator not in {
                "=",
                "!=",
                ">",
                "<",
                ">=",
                "<=",
                "contains",
                "not_contains",
            }:
                raise CSVAgentError(f"Unsupported operator '{operator}'.")

            column_series = df[column]
            typed_value = self._coerce_value(value, column_series)
            summaries.append(f"{column} {operator} {typed_value}")
            mask = mask & self._apply_condition(column_series, operator, typed_value)

        filtered = df[mask]
        summary_text = (
            f"Filtered dataset using conditions: {', '.join(summaries)}. "
            f"Matched {len(filtered)} rows."
        )
        table = self._format_dataframe(filtered.head(limit))
        return ExecutionResult(summary=summary_text, table_markdown=table)

    def _execute_aggregate(
        self, df: pd.DataFrame, params: Dict[str, Any]
    ) -> ExecutionResult:
        group_by = params.get("group_by") or []
        if isinstance(group_by, str):
            group_by = [group_by]
        metrics = params.get("metrics") or []
        if isinstance(metrics, dict):
            metrics = [metrics]

        conditions = params.get("conditions") or []
        if isinstance(conditions, dict):
            conditions = [conditions]

        if not metrics:
            raise CSVAgentError("Aggregation metrics were not provided.")
        for column in group_by:
            if column not in df.columns:
                raise CSVAgentError(f"Group-by column '{column}' does not exist.")

        filter_summaries: List[str] = []
        working_df = df
        if conditions:
            working_df = df.copy()
            mask = pd.Series([True] * len(working_df))
            supported_filter_ops = {
                "=",
                "!=",
                ">",
                "<",
                ">=",
                "<=",
                "contains",
                "not_contains",
            }
            for condition in conditions:
                if not isinstance(condition, dict):
                    continue
                column = condition.get("column")
                operator = str(condition.get("operator") or "=").lower()
                value = condition.get("value")
                if not column or column not in working_df.columns:
                    raise CSVAgentError(f"Column '{column}' does not exist for filtering.")
                if operator not in supported_filter_ops:
                    raise CSVAgentError(f"Unsupported filter operator '{operator}'.")
                series = working_df[column]
                typed_value = self._coerce_value(value, series)
                if pd.isna(typed_value):
                    typed_value = value
                try:
                    condition_mask = self._apply_condition(series, operator, typed_value)
                except Exception as exc:  # noqa: BLE001
                    raise CSVAgentError(
                        f"Unable to apply filter on column '{column}': {exc}"
                    ) from exc
                mask &= condition_mask.fillna(False)
                filter_summaries.append(f"{column} {operator} {typed_value}")
            working_df = working_df[mask]

        supported_ops = {"sum", "mean", "max", "min", "count", "median", "std", "var"}
        numeric_ops = {"sum", "mean", "max", "min", "median", "std", "var"}
        agg_dict: Dict[str, List[str]] = {}
        readable_metrics: List[str] = []
        row_count_requested = False

        for metric in metrics:
            operation = metric.get("operation")
            column = metric.get("column")
            if not operation:
                continue
            operation = operation.lower()
            if operation not in supported_ops:
                raise CSVAgentError(f"Unsupported aggregation '{operation}'.")

            if column:
                if column not in working_df.columns:
                    raise CSVAgentError(f"Metric column '{column}' does not exist.")
                if operation in numeric_ops and not is_numeric_dtype(working_df[column]):
                    raise CSVAgentError(
                        f"Column '{column}' must be numeric to apply '{operation}'."
                    )
                agg_dict.setdefault(column, [])
                if operation not in agg_dict[column]:
                    agg_dict[column].append(operation)
                display_op = _AGGREGATION_DISPLAY_NAMES.get(operation, operation)
                readable_metrics.append(f"{display_op}({column})")
            else:
                if operation == "count":
                    row_count_requested = True
                    readable_metrics.append("row count")
                else:
                    raise CSVAgentError(
                        f"The '{operation}' aggregation requires a column to operate on."
                    )

        if not agg_dict and not row_count_requested:
            raise CSVAgentError("No valid aggregation metrics were provided.")

        try:
            if group_by:
                grouped = working_df.groupby(group_by, dropna=False)
                aggregated = pd.DataFrame()
                if agg_dict:
                    aggregated = grouped.agg(agg_dict)
                    if isinstance(aggregated.columns, pd.MultiIndex):
                        aggregated.columns = [
                            "_".join([str(level) for level in col if level != ""])
                            for col in aggregated.columns
                        ]
                    aggregated = aggregated.reset_index()
                if row_count_requested:
                    counts = grouped.size().reset_index(name="row_count")
                    if aggregated.empty:
                        aggregated = counts
                    else:
                        if "row_count" in aggregated.columns:
                            aggregated = aggregated.drop(columns=["row_count"])
                        aggregated = aggregated.merge(counts, on=group_by, how="left")
            else:
                aggregated = pd.DataFrame()
                if agg_dict:
                    aggregated = working_df.agg(agg_dict)
                    aggregated = aggregated.reset_index().rename(
                        columns={"index": "metric"}
                    )
                if row_count_requested:
                    count_df = pd.DataFrame(
                        {"metric": ["row_count"], "value": [len(working_df)]}
                    )
                    if aggregated.empty:
                        aggregated = count_df
                    else:
                        if "metric" not in aggregated.columns:
                            aggregated.insert(0, "metric", aggregated.index)
                            aggregated.reset_index(drop=True, inplace=True)
                        aggregated = pd.concat(
                            [aggregated, count_df], ignore_index=True
                        )
        except Exception as exc:  # noqa: BLE001
            raise CSVAgentError(f"Failed to execute aggregation: {exc}") from exc

        readable_metrics = list(dict.fromkeys(readable_metrics))
        table = self._format_dataframe(aggregated)
        summary_parts = ["Aggregated dataset"]
        if group_by:
            summary_parts.append(f"grouped by {', '.join(group_by)}")
        if readable_metrics:
            summary_parts.append(f"applying {', '.join(readable_metrics)}")
        if filter_summaries:
            summary_parts.append(f"after filtering on {', '.join(filter_summaries)}")
        summary = " ".join(summary_parts).strip() + "."

        return ExecutionResult(summary=summary, table_markdown=table)

    def _coerce_value(self, value: Any, series: pd.Series) -> Any:
        if value is None:
            return None
        if is_numeric_dtype(series):
            try:
                if isinstance(value, str) and "." in value:
                    return float(value)
                return float(value)
            except ValueError:
                return pd.NA
        if is_datetime64_any_dtype(series):
            try:
                return pd.to_datetime(value)
            except Exception:  # noqa: BLE001
                return value
        return value

    def _apply_condition(
        self, series: pd.Series, operator: str, value: Any
    ) -> pd.Series:
        if operator == "=":
            return series == value
        if operator == "!=":
            return series != value
        if operator == ">":
            return series > value
        if operator == "<":
            return series < value
        if operator == ">=":
            return series >= value
        if operator == "<=":
            return series <= value
        if operator == "contains":
            return series.astype(str).str.contains(str(value), case=False, na=False)
        if operator == "not_contains":
            return ~series.astype(str).str.contains(str(value), case=False, na=False)
        return pd.Series([False] * len(series))

    def _format_dataframe(
        self, dataframe: pd.DataFrame, max_rows: int = 8, max_cols: int = 8
    ) -> str:
        if dataframe.empty:
            return "No rows to display."

        truncated = dataframe.copy()
        row_limit_reached = False
        col_limit_reached = False

        if len(truncated) > max_rows:
            truncated = truncated.head(max_rows)
            row_limit_reached = True

        if truncated.shape[1] > max_cols:
            truncated = truncated.iloc[:, :max_cols]
            col_limit_reached = True

        truncated = truncated.convert_dtypes()
        truncated = truncated.where(pd.notnull(truncated), None)

        markdown = truncated.to_markdown(index=False)

        notes: List[str] = []
        if row_limit_reached:
            notes.append(f"Showing first {max_rows} rows out of {len(dataframe)}.")
        if col_limit_reached:
            notes.append(
                f"Showing first {max_cols} columns out of {dataframe.shape[1]} total."
            )
        if notes:
            markdown += "\n\n" + " ".join(notes)
        return markdown

    def get_dataset_metadata(self, dataset_id: str) -> Dict[str, Any]:
        return self._load_metadata(dataset_id)

    def get_dataset_path(self, dataset_id: str) -> Path:
        dataset_dir = self.storage_dir / dataset_id
        csv_path = dataset_dir / "data.csv"
        if not csv_path.exists():
            raise CSVAgentError("CSV dataset could not be found on the server.")
        return csv_path

    def list_session_datasets(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        index = self._load_index()
        dataset_ids = index.get(session_id, [])
        datasets: List[Dict[str, Any]] = []
        for dataset_id in dataset_ids:
            try:
                metadata = self._load_metadata(dataset_id)
            except CSVAgentError:
                continue
            if metadata.get("user_id") != user_id:
                continue
            datasets.append(
                {
                    "dataset_id": dataset_id,
                    "filename": metadata.get("filename"),
                    "rows": metadata.get("rows"),
                    "columns": metadata.get("columns"),
                    "created_at": metadata.get("created_at"),
                }
            )
        return datasets

    def _register_dataset(self, session_id: str, dataset_id: str) -> None:
        index = self._load_index()
        dataset_ids = index.setdefault(session_id, [])
        if dataset_id not in dataset_ids:
            dataset_ids.append(dataset_id)
            self._save_index(index)

    def _load_index(self) -> Dict[str, List[str]]:
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_index(self, index: Dict[str, List[str]]) -> None:
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    def _load_metadata(self, dataset_id: str) -> Dict[str, Any]:
        meta_path = (self.storage_dir / dataset_id) / "meta.json"
        if not meta_path.exists():
            raise CSVAgentError("Dataset metadata is missing.")
        return json.loads(meta_path.read_text(encoding="utf-8"))

    def _safe_remove_dir(self, directory: Path) -> None:
        try:
            for child in directory.glob("*"):
                child.unlink(missing_ok=True)
            directory.rmdir()
        except Exception:
            pass


_INTENT_PROMPT = textwrap.dedent(
    """
    You are Echo, an AI agent that plans how to work with CSV datasets.
    You specialise in understanding CSV structure, performing mathematical operations, creating visualisations, and updating data when asked.
    The dataset profile is provided below to help you understand available columns.

    Dataset Profile:
    {{$dataset_profile}}

    Optional pre-processing hints (may be blank):
    - Hint intent: {{$hint_intent}}
    - Hint parameters (JSON): {{$hint_parameters}}
    - Hint confidence: {{$hint_confidence}}
    Treat the hints as authoritative when the confidence is "certain".

    Your task is to analyse the user's request and respond with a JSON object only,
    no additional commentary. The JSON must follow this schema:

    {
      "intent": one of ["dataset_overview", "list_columns", "describe_column",
                        "filter_rows", "aggregate", "value_counts", "top_n",
                        "set_cell_value", "add_row", "add_column", "row_math", "delete_row", "delete_rows",
                        "plot_line", "plot_bar", "raw_answer"],
      "parameters": { ... }  // optional details required for the operation
    }

    Parameter expectations:
      - describe_column: {"column": "<column name>"}
      - filter_rows: {"conditions": [{"column": "...", "operator": ">, <, >=, <=, =, !=", "value": "..."}], "limit": Optional[int]}
      - aggregate: {"group_by": ["col1", ...], "metrics": [{"column": "...", "operation": "sum|max|min|avg|count|median|std|var"}]}
      - value_counts: {"column": "...", "limit": Optional[int]}
      - top_n: {"column": "...", "limit": Optional[int], "ascending": Optional[bool]}
      - set_cell_value: {"row": <1-based row number>, "column": "<column name>" OR "column_index": <1-based index>, "value": "<new value or blank>"}
      - add_row: {"row_data": {"<column name>": "<value>", ...}}
      - add_column: {"column": "<new column name>", "values": ["...", ...] OR "default_value": "..."}
      - row_math: {"operation": "sum|mean|difference|product|ratio", "source_columns": ["col1", "col2", ...], "target_column": Optional["new column name"]}
      - delete_row: {"row": <1-based row number>}
      - delete_rows: {"conditions": [{"column": "...", "operator": ">, <, >=, <=, =, !=, contains, not_contains", "value": "..."}]}
      - plot_line / plot_bar: {"y_column": "<column to plot>", "x_column": Optional["<x-axis column>"], "title": Optional["Chart title"]}

    If you cannot confidently map the request, use the "raw_answer" intent.

    User request:
    {{$input}}
    """
).strip()


_RESPONSE_PROMPT = textwrap.dedent(
    """
    You are Echo, an AI agent summarising the results of a CSV operation for the user.
    You can manage CSV files end-to-end: perform mathematical operations, visualise the data, and add or remove rows and columns.
    When the user asks about your identity or capabilities, introduce yourself as "Echo, the CSV AI agent" and describe these skills.
    Never claim to be built by Google or to run on Google systems.

    Dataset Profile:
    {{$dataset_profile}}

    Plan executed (JSON):
    {{$plan_json}}

    Execution notes:
    {{$analysis_notes}}

    Table preview (if any):
    {{$table_preview}}

    Craft a concise answer (2-4 sentences) that addresses the user's request.
    Refer to key metrics and highlight trends when applicable.
    If the table preview is relevant, mention what it shows and advise on next steps.
    """
).strip()
