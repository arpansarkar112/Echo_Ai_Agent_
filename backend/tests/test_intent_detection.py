import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.csv_agent import CSVAgent


def test_detect_set_cell_value() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        agent = CSVAgent(storage_dir=Path(tmp_dir))
        df = pd.DataFrame(
            {
                "Year": [2020, 2021, 2022],
                "Value": [1.0, 2.0, 3.0],
            }
        )
        detection = agent._detect_user_intent("Set row 2 column Value to 4.5", df)
        assert detection is not None
        assert detection["intent"] == "set_cell_value"
        assert detection["parameters"]["row"] == 2
        assert detection["parameters"]["value"] == "4.5"
        assert detection["confidence"] == "certain"


def test_detect_plot_line() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        agent = CSVAgent(storage_dir=Path(tmp_dir))
        df = pd.DataFrame(
            {
                "Year": [2020, 2021, 2022],
                "Value": [1.0, 2.0, 3.0],
            }
        )
        detection = agent._detect_user_intent("plot a line chart of Value over Year", df)
        assert detection is not None
        assert detection["intent"] == "plot_line"
        assert detection["parameters"]["y_column"] == "Value"
        assert detection["parameters"].get("x_column") in {None, "Year"}


def test_detect_row_math_difference() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        agent = CSVAgent(storage_dir=Path(tmp_dir))
        df = pd.DataFrame(
            {
                "Revenue": [100, 200],
                "Cost": [40, 80],
            }
        )
        prompt = "Add a profit column that subtracts Cost from Revenue for each row."
        detection = agent._detect_user_intent(prompt, df)
        assert detection is not None
        assert detection["intent"] == "row_math"
        assert detection["parameters"]["operation"] == "difference"
        assert detection["parameters"]["source_columns"][:2] == ["Revenue", "Cost"]


def test_detect_aggregate_with_filter() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        agent = CSVAgent(storage_dir=Path(tmp_dir))
        df = pd.DataFrame(
            {
                "gender": ["female", "male", "female"],
                "math score": [88, 76, 94],
            }
        )
        prompt = "give me the sum of math score only for the female gender"
        detection = agent._detect_user_intent(prompt, df)
        assert detection is not None
        assert detection["intent"] == "aggregate"
        metrics = detection["parameters"]["metrics"]
        assert metrics[0]["column"] == "math score"
        conditions = detection["parameters"].get("conditions")
        assert conditions is not None
        assert conditions[0]["column"] == "gender"
        assert conditions[0]["value"] == "female"

        prompt = "give me the sum of math score only for the male gender"
        detection = agent._detect_user_intent(prompt, df)
        assert detection is not None
        assert detection["intent"] == "aggregate"
        metrics = detection["parameters"]["metrics"]
        assert metrics[0]["column"] == "math score"
        conditions = detection["parameters"].get("conditions")
        assert conditions is not None
        assert conditions[0]["column"] == "gender"
        assert conditions[0]["value"] == "male"


def test_normalize_plan_uses_hints() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        agent = CSVAgent(storage_dir=Path(tmp_dir))
        df = pd.DataFrame(
            {
                "Amount": [10, 20, 30],
                "Category": ["A", "B", "C"],
            }
        )
        plan = {
            "intent": "set_cell_value",
            "parameters": {
                "row": "2",
                "column": "amount",
                "value": "99",
            },
        }
        hints = {"parameters": {"column_name": "Amount"}}
        normalized = agent._normalize_plan(plan, hints=hints, df=df)
        assert normalized["parameters"]["column"] == "Amount"
        assert normalized["parameters"]["row"] == 2


def test_execute_row_math_difference() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_dir = Path(tmp_dir)
        agent = CSVAgent(storage_dir=storage_dir)
        df = pd.DataFrame(
            {
                "Revenue": [100.0, 150.0],
                "Cost": [30.0, 55.0],
            }
        )
        dataset_id = "dataset"
        dataset_dir = storage_dir / dataset_id
        dataset_dir.mkdir()
        df.to_csv(dataset_dir / "data.csv", index=False)

        metadata = {
            "dataset_id": dataset_id,
            "session_id": "session",
            "user_id": "user",
            "filename": "data.csv",
        }
        result = agent._execute_row_math(
            df,
            metadata,
            {
                "operation": "difference",
                "source_columns": ["Revenue", "Cost"],
                "target_column": "Profit",
            },
        )
        assert "difference" in result.summary
        saved = pd.read_csv(dataset_dir / "data.csv")
        assert "Profit" in saved.columns
        assert saved["Profit"].tolist() == [70.0, 95.0]


def test_execute_aggregate_with_filter() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        agent = CSVAgent(storage_dir=Path(tmp_dir))
        df = pd.DataFrame(
            {
                "gender": ["female", "male", "female"],
                "math score": [88, 76, 94],
            }
        )
        result = agent._execute_aggregate(
            df,
            {
                "metrics": [{"column": "math score", "operation": "sum"}],
                "conditions": [{"column": "gender", "operator": "=", "value": "female"}],
            },
        )
        assert "filtering on gender" in result.summary.lower()
        assert "math score" in result.table_markdown.lower()
        assert "182" in result.table_markdown


def main() -> None:
    test_detect_set_cell_value()
    test_detect_plot_line()
    test_detect_row_math_difference()
    test_detect_aggregate_with_filter()
    test_normalize_plan_uses_hints()
    test_execute_row_math_difference()
    test_execute_aggregate_with_filter()
    print("Intent detection tests passed")


if __name__ == "__main__":
    main()
