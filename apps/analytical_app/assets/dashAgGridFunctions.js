var dagfuncs = window.dashAgGridFunctions = window.dashAgGridFunctions || {};

dagfuncs.percentValueGetter = function (params, param1, param2) {
  if (!(params.node && params.node.group)) {
    return percentCreatValueObject(params.data[param1], params.data[param2]);
  }
}

dagfuncs.percentAggFunc = function (params, param1, param2) {
  let plan = 0;
  let fact = 0;
  params.values.forEach((value) => {
    if (value && value[param1]) {
      plan += value[param1];
    }
    if (value && value[param2]) {
      fact += value[param2];
    }
  });
  return percentCreatValueObject(plan, fact);
}

function percentCreatValueObject(param1, param2) {
  return {
    cumulative_plan: param1,
    январь_план: param1,
    февраль_план: param1,
    март_план: param1,
    апрель_план: param1,
    май_план: param1,
    июнь_план: param1,
    июль_план: param1,
    август_план: param1,
    сентябрь_план: param1,
    октябрь_план: param1,
    ноябрь_план: param1,
    декабрь_план: param1,
    year_exposed: param2,
    январь_выставлено: param2,
    февраль_выставлено: param2,
    март_выставлено: param2,
    апрель_выставлено: param2,
    май_выставлено: param2,
    июнь_выставлено: param2,
    июль_выставлено: param2,
    август_выставлено: param2,
    сентябрь_выставлено: param2,
    октябрь_выставлено: param2,
    ноябрь_выставлено: param2,
    декабрь_выставлено: param2,
    год_оплачено: param2,
    январь_оплачено: param2,
    февраль_оплачено: param2,
    март_оплачено: param2,
    апрель_оплачено: param2,
    май_оплачено: param2,
    июнь_оплачено: param2,
    июль_оплачено: param2,
    август_оплачено: param2,
    сентябрь_оплачено: param2,
    октябрь_оплачено: param2,
    ноябрь_оплачено: param2,
    декабрь_оплачено: param2,
    toString: () => `${param1 && param2 ? (param2 / param1) : 0}`,
  };
}

dagfuncs.percentFormatter = function (params) {
  if (!params.value || params.value === 0) return '0%';
  return '' + Math.round(params.value * 100) + '%';
}