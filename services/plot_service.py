import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio


def build_2d_plot(drones: list, title: str) -> str:
    palette = px.colors.qualitative.Plotly  # Paleta cíclica
    fig = go.Figure()

    for i, dron in enumerate(drones):
        color = palette[i % len(palette)]
        x, y, _ = dron.generate_points(height=0, num_points=200)
        fig.add_trace(
            go.Scatter(
                x=x.tolist(),
                y=y.tolist(),
                mode="lines",
                name=f"Dron {i+1}",
                line=dict(color=color, width=2),
                hovertemplate=(
                    f"Dron {i+1}<br>h={dron.h}, k={dron.k}<br>"
                    f"a={dron.a}, b={dron.b}<br>"
                    f"x=%{{x:.2f}}, y=%{{y:.2f}}<extra></extra>"
                )
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[dron.h],
                y=[dron.k],
                mode="markers+text",
                marker=dict(color=color, size=6),
                text=[f"({dron.h},{dron.k})"],
                textposition="top center",
                showlegend=False
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="X",
        yaxis_title="Y",
        legend=dict(x=0.85, y=0.95, bgcolor="rgba(255,255,255,0.5)"),
        width=600,
        height=600,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


def build_3d_plot(drones: list, title: str, height_z: float = 50) -> str:
    palette = px.colors.qualitative.Plotly
    fig = go.Figure()

    for i, dron in enumerate(drones):
        color = palette[i % len(palette)]
        x, y, z = dron.generate_points(height=height_z, num_points=200)
        fig.add_trace(
            go.Scatter3d(
                x=x.tolist(),
                y=y.tolist(),
                z=z.tolist(),
                mode="lines",
                name=f"Dron {i+1}",
                line=dict(color=color, width=3),
                hovertemplate=(
                    f"Dron {i+1}<br>h={dron.h}, k={dron.k}, z={height_z}<br>"
                    f"a={dron.a}, b={dron.b}<br>"
                    f"x=%{{x:.2f}}, y=%{{y:.2f}}, z=%{{z:.2f}}<extra></extra>"
                )
            )
        )
        fig.add_trace(
            go.Scatter3d(
                x=[dron.h],
                y=[dron.k],
                z=[height_z],
                mode="markers+text",
                marker=dict(color=color, size=4),
                text=[f"({dron.h},{dron.k},{height_z})"],
                textposition="top center",
                showlegend=False
            )
        )

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="auto"
        ),
        width=600,
        height=600,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs=False)
