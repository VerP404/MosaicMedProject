from django.db import models


class ISZLSettings(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "ИСЗЛ: Настройка"
        verbose_name_plural = "ИСЗЛ: Настройки"


class ISZLPeople(models.Model):
    pid = models.CharField(max_length=255, verbose_name="PID")
    fio = models.CharField(max_length=255, verbose_name="FIO")
    dr = models.CharField(max_length=255, verbose_name="DR")
    smo = models.CharField(max_length=255, verbose_name="SMO")
    enp = models.CharField(max_length=255, verbose_name="ENP")
    lpu = models.CharField(max_length=255, verbose_name="LPU")
    ss_doctor = models.CharField(max_length=255, verbose_name="SS_DOCTOR")
    lpuuch = models.CharField(max_length=255, verbose_name="LPUUCH")
    upd = models.CharField(max_length=255, verbose_name="Upd")
    closed = models.CharField(max_length=255, verbose_name="CLOSED")
    column1 = models.CharField(max_length=255, verbose_name="Column1", default="-")

    def __str__(self):
        return f"{self.fio} {self.dr} {self.enp} {self.lpuuch}"

    class Meta:
        verbose_name = "ИСЗЛ: Прикрепленные"
        verbose_name_plural = "ИСЗЛ: Прикрепленных"


class ISZLDisNab(models.Model):
    pid = models.CharField(max_length=255, verbose_name="pid", default='-')
    ldwid = models.CharField(max_length=255, verbose_name="ldwID")
    pdwid = models.CharField(max_length=255, verbose_name="pdwID")
    fio = models.CharField(max_length=255, verbose_name="FIO")
    dr = models.CharField(max_length=255, verbose_name="DR")
    ds = models.CharField(max_length=255, verbose_name="DS")
    datebegin = models.CharField(max_length=255, verbose_name="DateBegin")
    dateend = models.CharField(max_length=255, verbose_name="DateEnd")
    idreason = models.CharField(max_length=255, verbose_name="idReason")
    namereason = models.CharField(max_length=255, verbose_name="nameReason")
    planmonth = models.CharField(max_length=255, verbose_name="PlanMonth")
    planyear = models.CharField(max_length=255, verbose_name="PlanYear")
    fam_d = models.CharField(max_length=255, verbose_name="FAM_D")
    im_d = models.CharField(max_length=255, verbose_name="IM_D")
    ot_d = models.CharField(max_length=255, verbose_name="OT_D")
    ss_d = models.CharField(max_length=255, verbose_name="SS_D")
    spec_d = models.CharField(max_length=255, verbose_name="SPEC_D")
    specv015 = models.CharField(max_length=255, verbose_name="SpecV015")
    dateinfo = models.CharField(max_length=255, verbose_name="DateInfo")
    wayinfo = models.CharField(max_length=255, verbose_name="WayInfo")
    resinfo = models.CharField(max_length=255, verbose_name="ResInfo")
    factdn = models.CharField(max_length=255, verbose_name="FactDN")
    rezultdn = models.CharField(max_length=255, verbose_name="RezultDN")
    adr = models.CharField(max_length=255, verbose_name="ADR")
    enp = models.CharField(max_length=255, verbose_name="ENP")
    lpu = models.CharField(max_length=255, verbose_name="LPU")
    fio_doctor = models.CharField(max_length=255, verbose_name="FIO_DOCTOR")
    ss_doctor = models.CharField(max_length=255, verbose_name="SS_DOCTOR")
    lpuuch = models.CharField(max_length=255, verbose_name="LPUUCH")
    smo = models.CharField(max_length=255, verbose_name="SMO")
    lpuauto = models.CharField(max_length=255, verbose_name="LPUAUTO")
    lpudt = models.CharField(max_length=255, verbose_name="LPUDT")
    userupdatelist = models.CharField(max_length=255, verbose_name="UserUpdateList")
    dateupdatelist = models.CharField(max_length=255, verbose_name="DateUpdateList")
    userupdateplan = models.CharField(max_length=255, verbose_name="UserUpdatePlan")
    dateupdateplan = models.CharField(max_length=255, verbose_name="DateUpdatePlan")
    periodw = models.CharField(max_length=255, verbose_name="PeriodW")
    dateprev = models.CharField(max_length=255, verbose_name="DatePrev")
    placew = models.CharField(max_length=255, verbose_name="PlaceW")
    w = models.CharField(max_length=255, verbose_name="w")
    column1 = models.CharField(max_length=255, verbose_name="Column1", default="-")

    def __str__(self):
        return f"{self.fio} - {self.dr} - {self.enp} - {self.ds}"

    class Meta:
        verbose_name = "ИСЗЛ: ДН"
        verbose_name_plural = "ИСЗЛ: ДН"


class ISZLDisNabJob(models.Model):
    id_iszl = models.CharField(max_length=255, verbose_name="id")
    mo_prof = models.CharField(max_length=255, verbose_name="МО проф.м.")
    mo_pri = models.CharField(max_length=255, verbose_name="МО прикрепления")
    organization = models.CharField(max_length=255, verbose_name="Организация Проф.м.")
    address = models.CharField(max_length=255, verbose_name="Адрес")
    fio = models.CharField(max_length=255, verbose_name="Ф.И.О.")
    birth_date = models.CharField(max_length=255, verbose_name="Д.Р.")
    enp = models.CharField(max_length=255, verbose_name="ЕНП")
    ds = models.CharField(max_length=255, verbose_name="DS")
    date = models.CharField(max_length=255, verbose_name="Дата")
    time = models.CharField(max_length=255, verbose_name="Время")
    info = models.CharField(max_length=255, verbose_name="Инф.")
    fact = models.CharField(max_length=255, verbose_name="Факт")
    smo = models.CharField(max_length=255, verbose_name="СМО")
    modification_date_operator = models.CharField(max_length=255, verbose_name="Дата изм./Оператор")
    column1 = models.CharField(max_length=255, verbose_name="Column1", default="-")

    def __str__(self):
        return f'{self.fio} - {self.birth_date} - {self.enp}'

    class Meta:
        verbose_name = "ИСЗЛ: ДН работающих"
        verbose_name_plural = "ИСЗЛ: ДН работающих"


class CategoryDN(models.Model):
    name = models.CharField(max_length=250, verbose_name="Категория")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория ДН"
        verbose_name_plural = "Категории ДН"


class DS168n(models.Model):
    ds = models.CharField(max_length=250, verbose_name="Диагноз")
    profile = models.CharField(max_length=250, verbose_name="Профиль")
    speciality = models.CharField(max_length=250, verbose_name="Специальность")
    joint_speciality = models.CharField(max_length=250, verbose_name="Совместная специальность")
    category = models.ForeignKey(CategoryDN, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Категория ДН")

    def __str__(self):
        return self.ds

    class Meta:
        verbose_name = "Справочник: Диагноз по 168н"
        verbose_name_plural = "Справочник: Диагнозы по 168н"
