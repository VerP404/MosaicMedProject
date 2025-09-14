import pandas as pd


def data_patient(_file: str, _korpus='Корпус 1'):
    """
    Возвращаем дату обновления и датафрейм с информацией о записи на прием
    :param _korpus: str
    :param _file: str
    :return: date_update, df_patient
    """
    df_pat = pd.read_csv(_file, delimiter=';', dtype=str)
    date_upd = df_pat.loc[0]['Время обновления']
    df_pat = df_pat[df_pat['Корпус'] == _korpus]
    return date_upd, df_pat
