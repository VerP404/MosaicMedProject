from dash import dcc
import plotly.express as px


def create_bar_chart(df, x_col, y_col, color_col, graph_id):
    figure = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        barmode='group',
        labels={y_col: y_col, x_col: '', color_col: color_col}
    ).update_layout(
        plot_bgcolor='#1f2c56',  # Цвет фона области построения графика
        paper_bgcolor='#1f2c56',  # Цвет фона за пределами области построения графика
        title_x=0.5,  # Горизонтальное положение заголовка по центру
        font=dict(color='white'),  # Цвет шрифта
        title_font=dict(color='coral'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=0, b=0)  # Убираем отступы
    )

    return dcc.Graph(
        id=graph_id,
        figure=figure,
        style={'height': '200px'}
    )


def create_stacked_bar_chart(df, x_col, y_col, color_col, graph_id):
    figure = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        text=df[y_col].astype(str) + ' (' + df['percent'].astype(str) + '%)',
        barmode='stack',
        labels={y_col: 'Количество', x_col: '', color_col: 'Тип документа'}
    ).update_layout(
        plot_bgcolor='#1f2c56',  # Цвет фона области построения графика
        paper_bgcolor='#1f2c56',  # Цвет фона за пределами области построения графика
        title_x=0.5,  # Горизонтальное положение заголовка по центру
        font=dict(color='white'),  # Цвет шрифта
        title_font=dict(color='coral'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=0, b=0)  # Убираем отступы
    )

    return dcc.Graph(
        id=graph_id,
        figure=figure,
        style={'height': '200px'}
    )


def create_pie_chart(df, values_col, names_col, graph_id):
    figure = px.pie(
        df,
        values=values_col,
        names=names_col,
        hole=0.3
    ).update_layout(
        plot_bgcolor='#1f2c56',  # Цвет фона области построения графика
        paper_bgcolor='#1f2c56',  # Цвет фона за пределами области построения графика
        title_x=0.5,  # Горизонтальное положение заголовка по центру
        font=dict(color='white'),  # Цвет шрифта
        title_font=dict(color='coral')
    ).update_traces(
        textinfo='label+percent+value',
        showlegend=False
    )

    return dcc.Graph(
        id=graph_id,
        figure=figure,
        style={'height': '200px'}
    )