import pandas as pd
from apps.chief_app.components.cards.graphs.graph_utils import create_bar_chart, create_stacked_bar_chart, \
    create_pie_chart

# Данные для графика
disp = {
    'Корпус': ['Корпус 1', 'Корпус 2', 'Корпус 3', 'Корпус 6'],
    'ДВ4': [3880, 1635, 3880, 825],
    'ОПВ': [1686, 588, 1433, 299],
    'УД1': [656, 70, 830, 175]
}

df_disp = pd.DataFrame(disp)
df_disp = pd.melt(df_disp, id_vars=['Корпус'], var_name='Тип', value_name='Количество')

# Создание графика
bar_chart1 = create_bar_chart(df_disp, 'Корпус', 'Количество', 'Тип',
                              'corpus-bar-chart-1')

# Данные для второго графика
remd_semd = {
    'ЭМД': ['РЭМД', 'СЭМД', 'РЭМД', 'СЭМД', 'РЭМД', 'СЭМД', 'РЭМД', 'СЭМД'],
    'Корпус': ['Корпус 1', 'Корпус 1', 'Корпус 2', 'Корпус 2', 'Корпус 3', 'Корпус 3', 'Корпус 6', 'Корпус 6'],
    'count': [492, 43, 108, 22, 284, 109, 15, 44]
}

df_remd_semd = pd.DataFrame(remd_semd)
df_remd_semd['percent'] = df_remd_semd.groupby('Корпус')['count'].transform(lambda x: round(x / x.sum() * 100, 2))

# Создание второго графика
stacked_bar_chart1 = create_stacked_bar_chart(df_remd_semd, 'Корпус', 'count', 'ЭМД',
                                              'corpus-bar-chart-2')

# Данные для третьего графика
data_mortality = {
    'Корпус': ['Корпус 1', 'Корпус 2', 'Корпус 3', 'Корпус 6'],
    'всего': [116, 58, 127, 43],
    'за 7 дней': [11, 6, 13, 8],
    'вчера': [2, 1, 4, 1]
}

df_mortality = pd.DataFrame(data_mortality)

# Создание третьего графика
pie_chart1 = create_pie_chart(df_mortality, 'всего', 'Корпус', 'corpus-pie-1')

# Данные для четвертого графика
morbidity = {
    'Группа': ['БСК', 'ХОБЛ', 'БСК', 'ХОБЛ', 'БСК', 'ХОБЛ', 'БСК', 'ХОБЛ'],
    'Корпус': ['Корпус 1', 'Корпус 1', 'Корпус 2', 'Корпус 2', 'Корпус 3', 'Корпус 3', 'Корпус 6', 'Корпус 6'],
    'count': [342, 13, 124, 5, 167, 16, 102, 2]
}
df_morbidity = pd.DataFrame(morbidity)
df_morbidity['percent'] = df_morbidity.groupby('Корпус')['count'].transform(lambda x: round(x / x.sum() * 100, 2))


# Создание четвертого графика
bar_chart2 = create_stacked_bar_chart(df_morbidity, 'Корпус', 'count', 'Группа',  'corpus-bar-chart-3')