
`Амбулаторная помощь`

`goal` -  `in`
``` sql
'1','2','3','5','7','9','10','13','14','140','15','17','18','21','22','26','27','28','29','30','32','320','34','340','52','54','540','541','543','301','55','550','551','56','561','57','58','60','61','610','62','63','64','640','65','305','307'
```


`Амбулаторная помощь` - `Посещения`

`goal` -  `in`
``` sql
'1','2','3','5','7','9','10','13','14','140','15','17','18','21','26','27','28','29','32','320','34','340','52','54','540','541','543','55','550','551','56','561','57','58','60','61','610','62','63','64','640','65'
```


`Амбулаторная помощь` - `Посещения` - `Диспансерное наблюдение`

`goal` -  `=`
``` sql
'3'
```

`Амбулаторная помощь` - `Посещения` - `Диспансерное наблюдение`

`goal` -  `=`
``` sql
'3'
```
`Амбулаторная помощь` - `Посещения` - `Диспансерное наблюдение` - `БСК`

`goal` -  `=`
``` sql
'3'
```
`main_diagnosis_code` -  `like`
``` sql
'I%'
```
`Амбулаторная помощь` - `Посещения` - `Диспансерное наблюдение` - `ОНКО`

`goal` -  `=`
``` sql
'3'
```
`main_diagnosis_code` -  `like`
``` sql
'C%'
```
`Амбулаторная помощь` - `Посещения` - `Диспансерное наблюдение` - `СД`

`goal` -  `=`
``` sql
'3'
```
`main_diagnosis_code` -  `like`
``` sql
'E11%'
```


`Амбулаторная помощь` - `Неотложка`

`goal` -  `=`
``` sql
'22'
```
`Амбулаторная помощь` - `Неотложка` - `Неотложка на дому`

`goal` -  `=`
``` sql
'22'
```
`home_visits` -  `=`
``` sql
'1'
```

`Амбулаторная помощь` - `Неотложка` - `Неотложка в МО`

`goal` -  `=`
``` sql
'22'
```
`mo_visits` -  `=`
``` sql
'1'
```
`Амбулаторная помощь` - `Обращения`

`goal` -  `in`
``` sql
'30','301','305','307'
```
`Амбулаторная помощь` - `Обращения` - `Школа СД (307)`

`goal` -  `=`
``` sql
'307'
```

`Диспансеризация`

`goal` -  `in`
``` sql
'ДВ4','ДВ2','ОПВ','УД1','УД2','ДР1','ДР2','ПН1','ДС1','ДС2'
```

`Диспансеризация` - `Взрослые`

`goal` -  `in`
``` sql
'ДВ4','ДВ2','ОПВ','УД1','УД2','ДР1','ДР2'
```

`Диспансеризация` - `Взрослые` - `1 этап - ДВ4`

`goal` -  `=`
``` sql
'ДВ4'
```
`Диспансеризация` - `Взрослые` - `2 этап - ДВ2`

`goal` -  `=`
``` sql
'ДВ2'
```
`Диспансеризация` - `Взрослые` - `ПМО - ОПВ`

`goal` -  `=`
``` sql
'ОПВ'
```

`Диспансеризация` - `Взрослые` - `Углубленная - УД1`

`goal` -  `=`
``` sql
'УД1'
```
`Диспансеризация` - `Взрослые` - `Углубленная - УД2`

`goal` -  `=`
``` sql
'УД2'
```
`Диспансеризация` - `Взрослые` - `Репродуктивное - ДР1`

`goal` -  `=`
``` sql
'ДР1'
```
`Диспансеризация` - `Взрослые` - `Репродуктивное - ДР2`

`goal` -  `=`
``` sql
'ДР2'
```
`Диспансеризация` - `Дети`

`goal` -  `=`
``` sql
'ПН1','ДС1','ДС2'
```

`Диспансеризация` - `Дети` - `Профосмотр (талоны) - ПН1`

`goal` -  `=`
``` sql
'ПН1'
```
`Диспансеризация` - `Дети` - `Диспансеризация сирот в стац. (талоны) - ДС1`

`goal` -  `=`
``` sql
'ДС1'
```

`Диспансеризация` - `Дети` - `Диспансеризация сирот (талоны) - ДС2`

`goal` -  `=`
``` sql
'ДС2'
```


