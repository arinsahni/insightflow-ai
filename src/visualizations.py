"""Safe, consistent Plotly charts for the Phase 4 dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


COLORS = {"primary": "#4F46E5", "negative": "#DC2626", "positive": "#16A34A", "neutral": "#64748B"}


def _empty(title: str, message: str = "No data available for this view.") -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    return _style(figure, title)


def _style(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(
        title=title, template="plotly_white", height=360, margin=dict(l=30, r=20, t=60, b=35),
        font=dict(family="Arial, sans-serif", color="#1E293B"), hoverlabel=dict(namelength=-1),
    )
    return figure


def feedback_volume_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty or "date" not in dataframe:
        return _empty("Feedback Volume Over Time")
    dates = pd.to_datetime(dataframe["date"], errors="coerce").dropna()
    if dates.empty:
        return _empty("Feedback Volume Over Time", "Trend analysis is unavailable because the dataset has no usable dates.")
    daily = dates.dt.normalize().value_counts().sort_index().rename_axis("date").reset_index(name="feedback")
    coverage = (daily["date"].max() - daily["date"].min()).days + 1
    if coverage > 180:
        prepared = daily.set_index("date")["feedback"].resample("W-MON").sum().reset_index()
        aggregation = "Weekly"
    else:
        prepared, aggregation = daily, "Daily"
    figure = px.line(prepared, x="date", y="feedback", labels={"feedback": "Feedback items", "date": "Date"})
    figure.update_traces(line_color=COLORS["primary"], hovertemplate="%{x|%Y-%m-%d}<br>Feedback: %{y}<extra></extra>")
    if aggregation == "Daily" and coverage >= 14 and len(daily) >= 10:
        rolling = daily.set_index("date")["feedback"].asfreq("D", fill_value=0).rolling(7, min_periods=7).mean().dropna()
        figure.add_scatter(x=rolling.index, y=rolling.values, mode="lines", name="7-day average", line=dict(color="#94A3B8", dash="dot"))
    figure.update_layout(legend_title_text="")
    return _style(figure, "Feedback Volume Over Time")


def negative_sentiment_trend_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty or not {"date", "sentiment"}.issubset(dataframe.columns):
        return _empty("Weekly Negative Feedback Rate")
    prepared = dataframe.assign(date=pd.to_datetime(dataframe["date"], errors="coerce")).dropna(subset=["date"])
    if prepared.empty:
        return _empty("Weekly Negative Feedback Rate", "Trend analysis is unavailable because the dataset has no usable dates.")
    prepared["period"] = prepared["date"].dt.to_period("W-MON").dt.start_time
    grouped = prepared.groupby("period").agg(total_feedback=("sentiment", "size"), negative_count=("sentiment", lambda values: values.eq("Negative").sum())).reset_index()
    grouped["negative_percentage"] = grouped["negative_count"].div(grouped["total_feedback"]).mul(100)
    if len(grouped) < 2:
        return _empty("Weekly Negative Feedback Rate", "At least two calendar periods are needed for a meaningful trend.")
    figure = px.line(grouped, x="period", y="negative_percentage", labels={"negative_percentage": "Negative feedback (%)", "period": "Week starting"}, custom_data=["total_feedback", "negative_count"])
    figure.update_traces(line_color=COLORS["negative"], mode="lines+markers", marker_size=6, hovertemplate="Week: %{x|%Y-%m-%d}<br>Total feedback: %{customdata[0]}<br>Negative: %{customdata[1]}<br>Rate: %{y:.1f}%<extra></extra>")
    figure.update_yaxes(range=[0, 100])
    return _style(figure, "Weekly Negative Feedback Rate")


def top_themes_chart(dataframe: pd.DataFrame, limit: int = 10) -> go.Figure:
    if dataframe.empty or "primary_theme" not in dataframe:
        return _empty("Most Reported Product Themes")
    counts = dataframe.loc[dataframe["primary_theme"].ne("Other"), "primary_theme"].dropna().value_counts().head(limit)
    prepared = counts.rename_axis("theme").reset_index(name="mentions")
    prepared["share"] = prepared["mentions"] / len(dataframe) * 100
    if prepared.empty:
        return _empty("Top themes")
    figure = px.bar(prepared, x="mentions", y="theme", orientation="h", labels={"mentions": "Mentions", "theme": "Theme"}, custom_data=["share"])
    figure.update_traces(marker_color=COLORS["primary"])
    figure.update_traces(hovertemplate="%{y}<br>Mentions: %{x}<br>Share: %{customdata[0]:.1f}%<extra></extra>")
    figure.update_yaxes(categoryorder="total ascending", automargin=True)
    return _style(figure, "Most Reported Product Themes")


def sentiment_distribution_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty or "sentiment" not in dataframe:
        return _empty("Customer Sentiment Distribution")
    order = ["Negative", "Neutral", "Positive"]
    counts = dataframe["sentiment"].dropna().value_counts().reindex(order, fill_value=0)
    prepared = counts.rename_axis("sentiment").reset_index(name="count")
    prepared["percentage"] = prepared["count"] / max(len(dataframe), 1) * 100
    if prepared.empty:
        return _empty("Sentiment distribution")
    figure = px.bar(prepared, x="sentiment", y="count", color="sentiment", labels={"count": "Feedback items", "sentiment": "Sentiment"}, color_discrete_map={"Negative": COLORS["negative"], "Positive": COLORS["positive"], "Neutral": COLORS["neutral"]}, category_orders={"sentiment": order}, custom_data=["percentage"])
    figure.update_traces(hovertemplate="%{x}<br>Count: %{y}<br>Share: %{customdata[0]:.1f}%<extra></extra>")
    figure.update_layout(showlegend=False)
    return _style(figure, "Customer Sentiment Distribution")


def rating_distribution_chart(dataframe: pd.DataFrame) -> go.Figure:
    if dataframe.empty or "rating" not in dataframe:
        return _empty("Rating Distribution")
    ratings = pd.to_numeric(dataframe["rating"], errors="coerce").dropna()
    if ratings.empty:
        return _empty("Rating Distribution", "Rating analysis is unavailable because the dataset has no usable ratings.")
    counts = ratings.round().astype(int).value_counts().reindex(range(1, 6), fill_value=0)
    prepared = counts.rename_axis("rating").reset_index(name="count")
    prepared["percentage"] = prepared["count"] / max(len(ratings), 1) * 100
    figure = px.bar(prepared, x="rating", y="count", labels={"count": "Feedback items", "rating": "Rating"}, custom_data=["percentage"])
    figure.update_traces(marker_color=COLORS["primary"])
    figure.update_traces(hovertemplate="Rating %{x}<br>Count: %{y}<br>Share: %{customdata[0]:.1f}%<extra></extra>")
    figure.update_xaxes(tickmode="array", tickvals=[1, 2, 3, 4, 5])
    return _style(figure, "Rating Distribution")


def frequency_severity_chart(theme_summary: pd.DataFrame) -> go.Figure:
    required = {"theme", "frequency", "severity_score"}
    if theme_summary.empty or not required.issubset(theme_summary.columns):
        return _empty("Frequency versus severity")
    prepared = theme_summary.dropna(subset=["frequency", "severity_score"]).copy()
    if prepared.empty:
        return _empty("Frequency versus severity")
    figure = px.scatter(prepared, x="frequency", y="severity_score", text="theme", hover_name="theme", size="frequency", labels={"frequency": "Mentions", "severity_score": "Severity score"})
    figure.update_traces(marker_color=COLORS["primary"], textposition="top center")
    return _style(figure, "Frequency versus severity")


def theme_by_segment_heatmap(dataframe: pd.DataFrame, segment: str = "platform") -> go.Figure:
    if dataframe.empty or segment not in dataframe or "primary_theme" not in dataframe:
        return _empty(f"Theme by {segment.replace('_', ' ')}")
    prepared = dataframe.dropna(subset=[segment, "primary_theme"])
    if prepared.empty:
        return _empty(f"Theme by {segment.replace('_', ' ')}")
    matrix = pd.crosstab(prepared["primary_theme"], prepared[segment])
    figure = px.imshow(matrix, text_auto=True, aspect="auto", labels={"x": segment.replace("_", " ").title(), "y": "Theme", "color": "Mentions"}, color_continuous_scale="Blues")
    return _style(figure, f"Theme by {segment.replace('_', ' ')}")


def theme_trend_chart(dataframe: pd.DataFrame, themes: list[str] | None = None) -> go.Figure:
    if dataframe.empty or not {"date", "primary_theme"}.issubset(dataframe.columns):
        return _empty("Theme trends")
    prepared = dataframe.assign(date=pd.to_datetime(dataframe["date"], errors="coerce")).dropna(subset=["date", "primary_theme"])
    if themes:
        prepared = prepared[prepared["primary_theme"].isin(themes)]
    if prepared.empty:
        return _empty("Theme trends")
    grouped = prepared.groupby([prepared["date"].dt.normalize(), "primary_theme"]).size().rename("mentions").reset_index()
    figure = px.line(grouped, x="date", y="mentions", color="primary_theme", markers=True, labels={"date": "Date", "mentions": "Mentions", "primary_theme": "Theme"})
    return _style(figure, "Theme Trends Over Time")


def top_feature_requests_chart(summary: pd.DataFrame) -> go.Figure:
    if summary.empty or not {"feature_request_group", "mentions"}.issubset(summary.columns):
        return _empty("Top Requested Product Features")
    prepared = summary.sort_values("mentions").tail(10)
    figure = px.bar(prepared, x="mentions", y="feature_request_group", orientation="h", labels={"mentions": "Mentions", "feature_request_group": "Request"})
    figure.update_traces(marker_color=COLORS["primary"])
    return _style(figure, "Top Requested Product Features")


def priority_matrix_chart(theme_summary: pd.DataFrame) -> go.Figure:
    required = {"theme", "frequency", "severity_score", "priority_score"}
    if theme_summary.empty or not required.issubset(theme_summary.columns):
        return _empty("Issue Priority Matrix")
    prepared = theme_summary.dropna(subset=["frequency", "severity_score", "priority_score"]).copy()
    if prepared.empty:
        return _empty("Issue priority matrix")
    for column, default in (("share_percentage", 0.0), ("priority_label", "Not available"), ("business_risk", "Not available")):
        if column not in prepared:
            prepared[column] = default
    label_candidates = (
        prepared.loc[~prepared["theme"].isin(["Positive Feedback", "Other"])]
        .sort_values(["priority_score", "severity_score", "frequency"], ascending=False)
        .head(5)
    )
    figure = px.scatter(prepared, x="frequency", y="severity_score", size="frequency", color="priority_score", hover_name="theme", custom_data=["share_percentage", "priority_score", "priority_label", "business_risk"], color_continuous_scale=[[0, "#C4B5FD"], [1, "#6D28D9"]], range_color=[0, 100], labels={"frequency": "Mentions", "severity_score": "Severity score", "priority_score": "Priority score"})
    figure.update_traces(mode="markers")
    figure.update_traces(hovertemplate="<b>%{hovertext}</b><br>Mentions: %{x}<br>Share: %{customdata[0]:.1f}%<br>Severity: %{y:.1f}<br>Priority: %{customdata[1]:.1f}<br>%{customdata[2]}<br>%{customdata[3]}<extra></extra>")
    annotation_offsets = ((0, 28), (0, -30), (35, 18), (-45, 18), (35, -22))
    for (_, row), (ax, ay) in zip(label_candidates.iterrows(), annotation_offsets, strict=False):
        figure.add_annotation(
            x=row["frequency"],
            y=row["severity_score"],
            text=str(row["theme"]),
            showarrow=True,
            arrowhead=0,
            arrowwidth=1,
            arrowcolor="rgba(226, 232, 240, 0.70)",
            ax=ax,
            ay=ay,
            font=dict(color="#F8FAFC", size=12),
            bgcolor="rgba(15, 23, 42, 0.88)",
            bordercolor="rgba(226, 232, 240, 0.45)",
            borderwidth=1,
            borderpad=4,
        )
    figure = _style(figure, "Issue Priority Matrix")
    figure.update_layout(
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        margin=dict(l=70, r=90, t=85, b=70),
        title_font=dict(color="#F8FAFC"),
        coloraxis_colorbar=dict(
            title=dict(text="Priority score", font=dict(color="#F8FAFC")),
            tickfont=dict(color="#CBD5E1"),
        ),
    )
    figure.update_xaxes(
        title_font=dict(color="#F8FAFC"),
        tickfont=dict(color="#CBD5E1"),
        gridcolor="rgba(148, 163, 184, 0.18)",
        zerolinecolor="rgba(148, 163, 184, 0.28)",
    )
    figure.update_yaxes(
        title_font=dict(color="#F8FAFC"),
        tickfont=dict(color="#CBD5E1"),
        gridcolor="rgba(148, 163, 184, 0.18)",
        zerolinecolor="rgba(148, 163, 184, 0.28)",
    )
    return figure
