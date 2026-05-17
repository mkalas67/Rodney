"""GA4 Data API helpers."""

from datetime import date, timedelta

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.oauth2.credentials import Credentials


def make_client(creds: Credentials) -> BetaAnalyticsDataClient:
    return BetaAnalyticsDataClient(credentials=creds)


def fetch_weekly_metrics(client: BetaAnalyticsDataClient, property_id: str) -> dict:
    """Pull sessions, users, pageviews, engagement for the last 7 and prior 7 days."""
    today = date.today()
    this_week_end = today - timedelta(days=1)
    this_week_start = this_week_end - timedelta(days=6)
    prev_week_end = this_week_start - timedelta(days=1)
    prev_week_start = prev_week_end - timedelta(days=6)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[
            DateRange(
                start_date=this_week_start.isoformat(),
                end_date=this_week_end.isoformat(),
                name="this_week",
            ),
            DateRange(
                start_date=prev_week_start.isoformat(),
                end_date=prev_week_end.isoformat(),
                name="prev_week",
            ),
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="screenPageViews"),
            Metric(name="newUsers"),
            Metric(name="averageSessionDuration"),
            Metric(name="bounceRate"),
        ],
    )

    response = client.run_report(request)

    result = {"this_week": {}, "prev_week": {}}
    metric_names = ["sessions", "activeUsers", "screenPageViews", "newUsers",
                    "averageSessionDuration", "bounceRate"]

    for row in response.rows:
        period = row.dimension_values[0].value
        values = [v.value for v in row.metric_values]
        result[period] = dict(zip(metric_names, values))

    return result


def pct_change(current: float, previous: float) -> str:
    if previous == 0:
        return "N/A"
    change = (current - previous) / previous * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    return f"{m}m {s:02d}s"
