# Приёмка: два периода матрицы в dash_dn

1. При необходимости задать `DASH_DN_MATRIX_BEFORE` и `DASH_DN_MATRIX_AFTER` (по умолчанию `matrix_before_20260401` и `matrix_after_20260401`).
2. Импорт «до 01.04»: из корня `MosaicMedProject`, `PYTHONPATH` = корень репозитория — полный контур `dn_reference` (168н, свод услуг, `apps/dn_reference/data/usl_spec`):

   `py -m apps.dash_dn.build_catalog_from_excel --apply-sqlite --target-catalog matrix_before_20260401 --catalog-title "До 01.04.2026" --effective-to 2026-03-31`

3. Матрица «после»: разбить CELP в отдельную папку (не смешивать с «до»):

   `py -m apps.dash_dn.split_celp_to_usl_spec --input "apps/dash_dn/CELP_3 Приложение по соответствию услуги и диагноза +тариф с 01.04.2026(1).xlsx" --out apps/dash_dn/usl_spec_after`

4. Импорт «с 01.04»: тот же `build_catalog_from_excel`, но `--usl-spec apps/dash_dn/usl_spec_after` и `--target-catalog matrix_after_20260401` (или значение `DASH_DN_MATRIX_AFTER`):

   `py -m apps.dash_dn.build_catalog_from_excel --apply-sqlite --target-catalog matrix_after_20260401 --usl-spec apps/dash_dn/usl_spec_after --catalog-title "С 01.04.2026" --effective-from 2026-04-01`

5. В шапке три пункта: до / после / правки (user). Проверить «Подбор», «Справочники», «Анализ», «ИСЗЛ».
6. Регрессия: пароль администратора разрешает копирование выбранной базовой матрицы в `user` и запись связей в `matrix_before` / `matrix_after` и `user` при разблокировке на «Подбор услуг». Цены: приоритет `user` → «после» → «до».
