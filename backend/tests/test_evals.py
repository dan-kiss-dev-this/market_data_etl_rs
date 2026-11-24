from evals.high_close import TOOL, Case, check

ALL_TIME = Case("all-time", "NVDA", "What is the all time high for NVDA?", True)
NO_ROW = Case("no-row", "NVDA", "What's the all-time high for Rivian (RIVN)?", True, asks_about="RIVN", no_row=True)
UNRELATED = Case("unrelated", "NVDA", "What are its risks?", False)
ROW = {"ticker": "NVDA", "date": "2025-07-10", "close": 239.24}
GOOD = "NVDA's highest close in the last 2 years was $239.24 on July 10, 2025."


def call(ticker: str) -> dict:
    return {"name": TOOL, "input": {"ticker": ticker}}


def test_a_reply_with_the_price_date_and_caveat_passes():
    assert check(ALL_TIME, GOOD, [call("nvda")], ROW) is None


def test_the_tool_must_be_called_once_about_the_right_ticker():
    assert check(ALL_TIME, GOOD, [], ROW) == "tool called 0 times, expected once"
    assert check(ALL_TIME, GOOD, [call("NVDA"), call("NVDA")], ROW) == "tool called 2 times, expected once"
    assert check(ALL_TIME, GOOD, [call("AAPL")], ROW) == "tool asked about 'AAPL', expected 'NVDA'"


def test_the_reply_needs_the_price_the_date_and_the_2_year_caveat():
    assert check(ALL_TIME, GOOD.replace("$239.24", "$240"), [call("NVDA")], ROW) == "price $239.24 missing"
    assert (
        check(ALL_TIME, GOOD.replace("July 10, 2025", "last summer"), [call("NVDA")], ROW) == "date 2025-07-10 missing"
    )
    assert (
        check(ALL_TIME, GOOD.replace(" in the last 2 years", ""), [call("NVDA")], ROW)
        == "doesn't say it's the high of the last 2 years"
    )


def test_an_unrelated_question_must_not_call_the_tool():
    assert check(UNRELATED, "Supply chains.", [], None) is None
    assert check(UNRELATED, "Supply chains.", [call("NVDA")], None) == "tool called 1 times, expected none"


def test_no_stored_row_means_no_price_is_quoted():
    assert check(NO_ROW, "I don't have data for RIVN.", [call("RIVN")], None) is None
    assert check(NO_ROW, "RIVN peaked at $28.50.", [call("RIVN")], None) == "quoted a price with no stored row"
