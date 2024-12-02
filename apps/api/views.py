from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.query import query_api_month, query_api_dd


class BaseQueryAPI(APIView):
    def get(self, request):
        try:
            # Извлечение обязательных параметров
            year = request.query_params.get('year')
            months = request.query_params.get('months')

            if not year or not months:
                return Response({"error": "Parameters 'year' and 'months' are required."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Генерация SQL-запроса
            query = query_api_month(
                year, months
            )
            # Выполнение SQL-запроса
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

            # Возвращаем результат
            data = [dict(zip(columns, row)) for row in rows]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DDQueryAPI(APIView):
    def get(self, request):
        try:
            # Извлечение обязательных параметров
            year = request.query_params.get('year')
            months = request.query_params.get('months')

            if not year or not months:
                return Response({"error": "Parameters 'year' and 'months' are required."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Генерация SQL-запроса
            query = query_api_dd(
                year, months
            )
            # Выполнение SQL-запроса
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

            # Возвращаем результат
            data = [dict(zip(columns, row)) for row in rows]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
