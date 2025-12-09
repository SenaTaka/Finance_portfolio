"""
Chart Utilities Module

Reusable chart creation and styling utilities for the UI.
"""

import plotly.express as px
import plotly.graph_objects as go


def apply_mobile_layout(fig, show_legend: bool = True):
    """
    Apply mobile-friendly layout settings to a Plotly figure.
    
    Args:
        fig: Plotly figure object
        show_legend: Whether to show legend
        
    Returns:
        Modified figure
    """
    layout_config = dict(margin=dict(l=10, r=10, t=40, b=100))
    if show_legend:
        layout_config["legend"] = dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            itemsizing="constant"
        )
    fig.update_layout(**layout_config)
    return fig


def create_pie_chart(
    data,
    values_col: str,
    names_col: str,
    title: str,
    hole: float = 0.4
):
    """
    Create a pie chart with standard styling.
    
    Args:
        data: DataFrame with data
        values_col: Column name for values
        names_col: Column name for labels
        title: Chart title
        hole: Size of hole in center (0-1)
        
    Returns:
        Plotly figure
    """
    fig = px.pie(
        data,
        values=values_col,
        names=names_col,
        title=title,
        hole=hole
    )
    fig.update_traces(
        textposition='none',
        hovertemplate='%{label}<br>%{value:,.0f}<br>%{percent}<extra></extra>'
    )
    apply_mobile_layout(fig)
    return fig


def create_bar_chart(
    data,
    x_col: str,
    y_col: str,
    title: str,
    color_col: str = None,
    tick_angle: int = -45
):
    """
    Create a bar chart with standard styling.
    
    Args:
        data: DataFrame with data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        color_col: Column name for color grouping
        tick_angle: Angle for x-axis tick labels
        
    Returns:
        Plotly figure
    """
    fig = px.bar(
        data,
        x=x_col,
        y=y_col,
        title=title,
        color=color_col
    )
    apply_mobile_layout(fig)
    fig.update_layout(xaxis_tickangle=tick_angle)
    return fig


def create_scatter_chart(
    data,
    x_col: str,
    y_col: str,
    title: str,
    size_col: str = None,
    color_col: str = None,
    hover_data: dict = None,
    labels: dict = None
):
    """
    Create a scatter plot with standard styling.
    
    Args:
        data: DataFrame with data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        size_col: Column name for bubble size
        color_col: Column name for color
        hover_data: Dictionary for hover data configuration
        labels: Dictionary for axis labels
        
    Returns:
        Plotly figure
    """
    fig = px.scatter(
        data,
        x=x_col,
        y=y_col,
        size=size_col,
        color=color_col,
        hover_data=hover_data,
        title=title,
        labels=labels
    )
    
    # Optimize for mobile: hide legend and increase chart area
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=40),
        showlegend=False,
        xaxis=dict(title=dict(font=dict(size=12))),
        yaxis=dict(title=dict(font=dict(size=12))),
    )
    
    return fig


def create_line_chart(
    data,
    x_col: str,
    y_cols: list,
    title: str,
    labels: dict = None
):
    """
    Create a line chart with standard styling.
    
    Args:
        data: DataFrame with data
        x_col: Column name for x-axis
        y_cols: List of column names for y-axis lines
        title: Chart title
        labels: Dictionary for axis labels
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    for col in y_cols:
        fig.add_trace(go.Scatter(
            x=data[x_col],
            y=data[col],
            mode='lines',
            name=col
        ))
    
    fig.update_layout(
        title=title,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=10, r=10, t=40, b=80),
        hovermode='x unified'
    )
    
    if labels:
        fig.update_xaxes(title_text=labels.get('x', ''))
        fig.update_yaxes(title_text=labels.get('y', ''))
    
    return fig


def create_heatmap(
    data,
    title: str,
    text_auto: bool = True
):
    """
    Create a heatmap (e.g., for correlation matrix).
    
    Args:
        data: DataFrame with data
        title: Chart title
        text_auto: Whether to show text automatically
        
    Returns:
        Plotly figure
    """
    fig = px.imshow(
        data,
        text_auto=text_auto,
        title=title
    )
    apply_mobile_layout(fig, show_legend=False)
    return fig
