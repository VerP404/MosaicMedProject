import subprocess

import fdb
from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.query import query_api_month, query_api_dd
from apps.api.serializers import PatientRegistrySerializer
from apps.data.models.registry.nothospitalized import PatientRegistry
from apps.home.models import MainSettings
from apps.organization.models import MedicalOrganization


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


class MISKAUZLPUAPIView(APIView):
    def get(self, request):
        try:
            # Подключение к базе данных Firebird
            settings = MainSettings.objects.first()
            organization = MedicalOrganization.objects.first()
            if not settings:
                return Response({"error": "Настройки подключения не найдены."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            dsn = f"{settings.kauz_server_ip}:{settings.kauz_database_path}"
            code = organization.code_mo
            with fdb.connect(
                    dsn=dsn,
                    user=settings.kauz_user,
                    password=settings.kauz_password,
                    charset='WIN1251',
                    port=settings.kauz_port
            ) as con:
                cursor = con.cursor()
                cursor.execute(f"SELECT NAME FROM LPU WHERE CODE = '{code}'")
                rows = cursor.fetchall()

            # Формируем список имен
            names = [{"name": row[0]} for row in rows]
            return Response(names, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MISKAUZTalonAPIView(APIView):
    def get(self, request, year):
        try:
            # Подключение к Firebird
            settings = MainSettings.objects.first()
            if not settings:
                return Response({"error": "Настройки подключения не найдены."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            dsn = f"{settings.kauz_server_ip}:{settings.kauz_database_path}"
            with fdb.connect(
                    dsn=dsn,
                    user=settings.kauz_user,
                    password=settings.kauz_password,
                    charset='WIN1251',
                    port=settings.kauz_port
            ) as con:
                cursor = con.cursor()

                # Формируем SQL-запрос с использованием года из URL
                query = f"""
                SELECT
                    "Цель",
                    COUNT(*)                                                                         AS "Всего",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 1 THEN 1 ELSE 0 END)  AS "01",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 2 THEN 1 ELSE 0 END)  AS "02",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 3 THEN 1 ELSE 0 END)  AS "03",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 4 THEN 1 ELSE 0 END)  AS "04",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 5 THEN 1 ELSE 0 END)  AS "05",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 6 THEN 1 ELSE 0 END)  AS "06",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 7 THEN 1 ELSE 0 END)  AS "07",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 8 THEN 1 ELSE 0 END)  AS "08",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 9 THEN 1 ELSE 0 END)  AS "09",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 10 THEN 1 ELSE 0 END) AS "10",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 11 THEN 1 ELSE 0 END) AS "11",
                    SUM(CASE WHEN EXTRACT(MONTH FROM DerivedTable.DATENDVST) = 12 THEN 1 ELSE 0 END) AS "12"
                FROM (
                    SELECT
                        CASE
                            WHEN ca.IDTARGET = 1 AND ca.IDTYPEDOCUMENTCASE = 3 AND
                                 TYPESACCOUNTS.NAME = 'ДНЕВНОЙ СТАЦИОНАР, СТАЦИОНАР НА ДОМУ, ЦАПХ (БЕЗ ОНКО)' THEN 'В дневном стационаре'
                            WHEN ca.IDTARGET = 1 AND ca.IDTYPEDOCUMENTCASE = 4 AND
                                 TYPESACCOUNTS.NAME = 'ДНЕВНОЙ СТАЦИОНАР, СТАЦИОНАР НА ДОМУ, ЦАПХ (БЕЗ ОНКО)' THEN 'На дому'
                            WHEN ca.IDTARGET = 502 THEN '55'
                            WHEN ca.IDTARGET = 38 THEN 'ДВ4'
                            WHEN ca.IDTARGET = 39 THEN 'ДВ2'
                            WHEN ca.IDTARGET = 35 THEN 'ОПВ'
                            WHEN ca.IDTARGET = 382 THEN 'УД1'
                            WHEN ca.IDTARGET = 392 THEN 'УД2'
                            WHEN ca.IDTARGET = 383 THEN 'ДР1'
                            WHEN ca.IDTARGET = 393 THEN 'ДР2'
                            WHEN ca.IDTARGET = 43 THEN 'ПН1'
                            WHEN ca.IDTARGET = 44 THEN 'ПН1'
                            WHEN ca.IDTARGET = 40 THEN 'ДС1'
                            WHEN ca.IDTARGET = 49 THEN 'ДС2'
                            ELSE CAST(ca.IDTARGET AS VARCHAR(50))
                        END AS "Цель",
                        ca.DATENDVST
                    FROM CASESAMB AS ca
                    LEFT JOIN TYPESACCOUNTS ON (ca.IDTYPEACCOUNT = TYPESACCOUNTS.ID)
                    WHERE EXTRACT(YEAR FROM ca.DATENDVST) = {year}
                ) AS DerivedTable
                GROUP BY "Цель"
                ORDER BY "Цель" DESC;
                """
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

            # Преобразуем результат в список словарей
            result = [dict(zip(columns, row)) for row in rows]
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PatientRegistryAPI(APIView):
    """
    API для получения всех записей из PatientRegistry.
    """

    def get(self, request):
        try:
            patients = PatientRegistry.objects.all()
            serializer = PatientRegistrySerializer(patients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateRegistryAPIView(APIView):
    """
    Вьюха для запуска команды обновления реестра пациентов
    """

    def get(self, request):
        try:
            # Запускаем Django-команду через subprocess
            result = subprocess.run(
                ["python", "manage.py", "update_registry_not_hospitalize"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return Response({"status": "success", "message": result.stdout}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "error", "message": result.stderr},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
