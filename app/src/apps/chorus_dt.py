import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Output, Input, State
import pandas as pd
import numpy as np

from app import app
from utils.organization_chart import oc
from utils.chorus_dt_handler import ch
from components.html_components import build_figure_container, build_card_indicateur
from components.figures_templates import xaxis_format

# TODO: move get figure function to chorus_dt_components.py in components
# TODO:
# - List of top trips based on emissions
# - Emissions
# - Nombre des trajets train vs avions


def get_kpi_emissions(df):
    return "{:,} kg".format(int(np.round(df["CO2e/trip"].sum(), 0))).replace(",", " ")


def get_kpi_emissions_example(df, example_ec02=0.11):
    return "{:,}".format(int(np.round((df["CO2e/trip"].sum() / example_ec02), 0))).replace(",", " ")


def get_kpi_distance(df):
    return "{:,} km".format(int(np.round(df["distance"].sum(), 0))).replace(",", " ")  # In km


def get_kpi_trips_count(df):
    return "{:,}".format(int(np.round(df["distance"].count(), 0))).replace(",", " ")


def get_donut_by_prestation_type(df):
    """
        Render and update a donut figure to show emissions distribution by prestation type
    """
    prestation_df = df.groupby(["prestation"])["CO2e/trip"].sum().reset_index()
    fig = go.Figure(data=[go.Pie(labels=prestation_df.prestation, values=prestation_df["CO2e/trip"], hole=0.3)])
    fig.update_layout(plot_bgcolor="white", template="plotly_white", margin={"t": 30, "r": 30, "l": 30})
    return fig


def get_hist_by_distance_group(df):
    """
        Render and update a donut figure to show emissions distribution by prestation type
    """
    distance_df = df.groupby(["distance_group", "prestation"])["CO2e/trip"].sum().reset_index()
    distance_df = distance_df.pivot(index="distance_group", columns="prestation", values="CO2e/trip")
    fig = go.Figure()
    for col in distance_df.columns:
        fig.add_trace(go.Bar(x=distance_df.index, y=distance_df[col], name=col))
    fig.update_layout(plot_bgcolor="white", template="plotly_white", margin={"t": 30, "r": 30, "l": 30})
    return fig


def get_emissions_timeseries(df):
    """
        Render and update a scatter plot figure to show emissions evolution with time
    """
    timeseries_df = df.groupby(["year_month"])["CO2e/trip"].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=timeseries_df["year_month"].astype(str),
            y=timeseries_df["CO2e/trip"].values,
            mode="lines+markers",
            line=dict(width=3),
        )
    )
    fig.update_layout(
        plot_bgcolor="white", template="plotly_white", margin={"t": 30, "r": 30, "l": 30}, xaxis=xaxis_format
    )
    return fig


def get_scatter_by_emission(df):
    """
        Render and update a bubble chart figure to show emissions distribution by prestation type/distance
    """
    df["slug"] = df["lieu_depart"] + " | " + df["lieu_arrivee"]
    df["count"] = 1
    distance_df = df.groupby(["slug", "prestation", "distance"])["CO2e/trip", "count"].sum().reset_index()
    distance_df["avg_CO2e"] = distance_df["CO2e/trip"] / distance_df["count"]
    fig = px.scatter(
        distance_df,
        x="distance",
        y="count",
        size="CO2e/trip",
        color="prestation",
        hover_name="slug",
        log_x=True,
        size_max=60,
    )
    return fig


def get_scatter_by_emission(df):
    """
        Render and update a bubble chart figure to show emissions distribution by prestation type/distance
    """
    distance_df = df.groupby(["prestation", "trajet", "distance"])[["CO2e/trip", "count"]].sum().reset_index()
    distance_df["avg_CO2e"] = distance_df["CO2e/trip"] / distance_df["count"]
    fig = px.scatter(
        distance_df,
        x="distance",
        y="count",
        size="CO2e/trip",
        color="prestation",
        hover_name="trajet",
        log_x=True,
        size_max=60,
    )
    fig.update_layout(
        plot_bgcolor="white", template="plotly_white", margin={"t": 30, "r": 30, "l": 30}, xaxis=xaxis_format
    )
    return fig


def get_hist_top_emission(df):
    """
    Render and update a histogram showing top routes with most emissions.
    """
    n = 10  # Max number of top trips to show
    hist_df = (
        df.groupby(["trajet", "prestation"], as_index=False)[["CO2e/trip", "count"]]
        .sum()
        .sort_values("CO2e/trip", ascending=False)
    )
    hist_df["cumul_emission"] = hist_df["CO2e/trip"].cumsum()
    hist_df["cumul_emission%"] = 100 * hist_df["cumul_emission"] / hist_df["CO2e/trip"].sum()
    top_hist_df = hist_df.head(n)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=top_hist_df["trajet"], y=top_hist_df["CO2e/trip"], name="Trajets effectués"))
    fig.add_trace(
        go.Scatter(
            x=top_hist_df["trajet"],
            y=top_hist_df["cumul_emission%"],
            name="Trajets effectués",
            yaxis="y2",
            marker={"color": "orange"},
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        template="plotly_white",
        margin={"t": 30, "r": 30, "l": 30},
        xaxis=xaxis_format,
        yaxis={"range": [0, 100], "title": "Defect Frequency", "ticksuffix": "%"},
        yaxis2={
            "side": "right",
            "range": [0, 100],
            "title": "Cumulative Percentage",
            "tickfont": {"color": "rgb(148, 103, 189)"},
            "titlefont": {"color": "rgb(148, 103, 189)"},
            "overlaying": "y",
            "ticksuffix": "%",
        },
    )
    return fig


def get_dashtable_by_emission(df):
    """
    Render a dashtable listing top offending connexions by CO2 emissions
    """
    # TODO: Follow instructions in https://stackoverflow.com/questions/58804477/plotly-dash-table-callback
    distance_df = df.groupby(["trajet", "prestation", "distance"])[["CO2e/trip", "count"]].sum().reset_index()
    distance_df["avg_CO2e"] = distance_df["CO2e/trip"] / distance_df["count"]
    distance_df["distance"] = distance_df["distance"].round(0)
    distance_df[["CO2e/trip", "avg_CO2e"]] = distance_df[["CO2e/trip", "avg_CO2e"]].round(2)
    distance_df = distance_df.sort_values(["CO2e/trip"], ascending=False)
    table = dash_table.DataTable(
        id="datatable-row-ids",
        columns=[
            {"name": i, "id": i, "deletable": True}
            for i in distance_df.columns
            # omit the id column
            if i != "id"
        ],
        data=distance_df.to_dict("rows"),
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        # row_selectable="multi",
        # row_deletable=True,
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=20,
    )
    return table


select_prestation_type = dcc.Dropdown(
    id="select-prestation_type", options=[{"label": "Train", "value": "T"}, {"label": "Avion", "value": "A"}]
)


cards = dbc.CardDeck(
    [
        build_card_indicateur("Emissions (kg eqCO2)", "0", "kpi-emissions"),
        build_card_indicateur("Nombre de trajets", "0", "kpi-trips"),
        build_card_indicateur("Distance totale (km)", "0", "kpi-distance"),
    ]
)

layout = html.Div(
    [
        dbc.Row(html.P("", id="values-selected")),
        # Cards row
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H3("Filtres"),
                                    html.Br(),
                                    dbc.FormGroup([dbc.Label("Type de prestation"), select_prestation_type]),
                                ]
                            ),
                            className="pretty_container",
                        ),
                        html.Br(),
                        dbc.Jumbotron("Explications sur les graphiques et leur fonctionnement..."),
                    ]
                ),
                dbc.Col(
                    [
                        cards,
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        build_figure_container(
                                            title="Répartition des émissions par type de déplacement",
                                            id="donut-by-prestation",
                                            footer="Explications..",
                                        )
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        build_figure_container(
                                            title="Évolution temporelles des émissions",
                                            id="timeseries-chorus-dt",
                                            footer="Explications..",
                                        )
                                    ]
                                ),
                            ]
                                        )
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        build_figure_container(
                                            title="Évolution temporelles des émissions",
                                            id="timeseries-chorus-dt",
                                            footer="Explications..",
                                        )
                                    ]
                                ),
                            ]
                        ),
                    ],
                    width=9,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        build_figure_container(
                            title="Répartition des émissions par distance de trajet",
                            id="scatter-by-emission",
                            footer="Explications..",
                        )
                    ],
                    width=12,
                ),
                # dbc.Col(
                #     [
                #         dbc.Card(
                #             dbc.CardBody(
                #                 [
                #                     html.H3("Filtres"),
                #                     html.Br(),
                #                     dbc.FormGroup([dbc.Label("Type de prestation"), select_prestation_type]),
                #                 ]
                #             ),
                #             className="pretty_container",
                #         ),
                #     ],
                #     width=4,
                # ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        build_figure_container(
                            title="Histogramme des iasons avec les plus gros volumns d'émissions",
                            id="hist-by-emission",
                            footer="Explications..",
                        )
                    ],
                    width=6,
                ),
                dbc.Col([html.Div(id="table-by-emission"),], width=6,),
            ]
        ),
    ],
    id="div-data-chorus-dt",
)


@app.callback(
    [
        Output("kpi-emissions", "children"),
        Output("kpi-trips", "children"),
        Output("kpi-distance", "children"),
        Output("donut-by-prestation", "figure"),
        Output("scatter-by-emission", "figure"),
        Output("timeseries-chorus-dt", "figure"),
    ],
    [Input("dashboard-selected-entity", "children")],
)
def update_graphs(selected_entity):
    service = oc.get_entity_by_id(selected_entity)
    chorus_dt_df = ch.get_structure_data(service.code_chorus).copy()

    return [
        get_kpi_emissions(chorus_dt_df),
        get_kpi_trips_count(chorus_dt_df),
        get_kpi_distance(chorus_dt_df),
        get_donut_by_prestation_type(chorus_dt_df),
        get_scatter_by_emission(chorus_dt_df),
        get_emissions_timeseries(chorus_dt_df),
    ]


@app.callback(
    Output("hist-by-emission", "figure"), [Input("dashboard-selected-entity", "children")],
)
def update_graphs_by_connexion(selected_entity):
    service = oc.get_entity_by_id(selected_entity)
    chorus_dt_df = ch.get_structure_data(service.code_chorus).copy()

    return get_scatter_by_emission(chorus_dt_df)


import pandas as pd

df = pd.read_csv(
    "https://gist.githubusercontent.com/chriddyp/"
    "c78bf172206ce24f77d6363a2d754b59/raw/"
    "c353e8ef842413cae56ae3920b8fd78468aa4cb2/"
    "usa-agricultural-exports-2011.csv"
)


@app.callback(
    Output("table-by-emission", "children"), [Input("dashboard-selected-entity", "children")],
)
def update_graphs_by_connexion(selected_entity):
    service = oc.get_entity_by_id(selected_entity)
    chorus_dt_df = ch.get_structure_data(service.code_chorus).copy()

    return [get_hist_top_emission(chorus_dt_df), get_dashtable_by_emission(chorus_dt_df)]


# @app.callback(
#     Output("table-by-emission", "children"), [Input("dashboard-selected-entity", "children")],
# )
# def update_graphs_by_connexion(selected_entity):
#     service = oc.get_entity_by_id(selected_entity)
#     chorus_dt_df = ch.get_structure_data(service.code_chorus).copy()
#
#     return get_dashtable_by_emission(chorus_dt_df)
#     # dfgb = df.groupby(['state']).sum()
#     # data = df.to_dict('rows')
#     # columns = [{"name": i, "id": i, } for i in (df.columns)]
#     # return dash_table.DataTable(data=data, columns=columns)
