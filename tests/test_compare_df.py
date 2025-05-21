import pytest

pd = pytest.importorskip("pandas")

from bellman_tools import sql_tools


def test_basic_comparison_returns_new_rows():
    df_incoming = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})
    df_existing = pd.DataFrame({"id": [1], "value": ["a"]})

    df_diff = sql_tools.compare_df_with_existing_and_get_only_new_rows(
        df_incoming=df_incoming,
        df_existing=df_existing,
    )

    expected = pd.DataFrame({"id": [2], "value": ["b"]})
    pd.testing.assert_frame_equal(
        df_diff.reset_index(drop=True),
        expected,
        check_dtype=False,
    )


def test_ignored_columns_are_not_compared():
    df_incoming = pd.DataFrame(
        {
            "id": [1, 2],
            "value": ["foo", "bar"],
            "ignore": [2, 3],
        }
    )
    df_existing = pd.DataFrame(
        {
            "id": [1],
            "value": ["foo"],
            "ignore": [1],
        }
    )

    df_diff = sql_tools.compare_df_with_existing_and_get_only_new_rows(
        df_incoming=df_incoming,
        df_existing=df_existing,
        ignored_columns=["ignore"],
    )

    expected = pd.DataFrame(
        {
            "id": [2],
            "value": ["bar"],
            "ignore": [3],
        }
    )

    pd.testing.assert_frame_equal(
        df_diff.reset_index(drop=True).sort_index(axis=1),
        expected.sort_index(axis=1),
        check_dtype=False,
    )


def test_cast_to_existing_dtypes():
    df_incoming = pd.DataFrame({"id": [1, 2], "amount": ["10", "20"]})
    df_existing = pd.DataFrame({"id": [1], "amount": pd.Series([10], dtype="int64")})

    diff_no_cast = sql_tools.compare_df_with_existing_and_get_only_new_rows(
        df_incoming=df_incoming,
        df_existing=df_existing,
        cast_to_existing_dtypes=False,
    )

    diff_cast = sql_tools.compare_df_with_existing_and_get_only_new_rows(
        df_incoming=df_incoming,
        df_existing=df_existing,
        cast_to_existing_dtypes=True,
    )

    expected_no_cast = df_incoming
    expected_cast = pd.DataFrame({"id": [2], "amount": pd.Series([20], dtype="int64")})

    pd.testing.assert_frame_equal(
        diff_no_cast.reset_index(drop=True).sort_index(axis=1),
        expected_no_cast.reset_index(drop=True).sort_index(axis=1),
        check_dtype=False,
    )

    pd.testing.assert_frame_equal(
        diff_cast.reset_index(drop=True).sort_index(axis=1),
        expected_cast.reset_index(drop=True).sort_index(axis=1),
        check_dtype=False,
    )

