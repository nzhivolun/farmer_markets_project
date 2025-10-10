// static/assets/js/pages/apexcharts.dynamic.js
// --------------------------------------------------------------
// Цель файла: НЕ ломая vendor-скрипт темы, аккуратно перерисовать
// график #apex-bar-1, подставив реальные данные из data-* атрибутов.
// --------------------------------------------------------------
(function () {
  
  // Находим контейнер графика
  var el = document.querySelector("#apex-bar-1");
  if (!el || typeof ApexCharts === "undefined") return;

  // 1) Цвета: тема кладёт их в data-colors, оставим ту же механику
  var colors = ["#6658dd"];
  var dataColors = el.getAttribute("data-colors");
  if (dataColors && dataColors.length) {
    colors = dataColors.split(",");
  }

  // 2) Читаем данные, которые пришли из Django в data-атрибутах
  //    Значения заранее сериализованы во views.py через json.dumps(...)
  var seriesData = [];
  var categories = [];
  try {
    var s = el.getAttribute("data-series");      // например: "[542, 380, ...]"
    var c = el.getAttribute("data-categories");  // например: ["CA","TX",...]
    if (s) seriesData = JSON.parse(s);
    if (c) categories = JSON.parse(c);
  } catch (e) {
    // Если вдруг данные в неверном формате — просто залогируем, чтобы не падать
    console.warn("apex-bar-1: eror parsing data-series/categories", e);
  }

  // 3) Фолбэк: если по какой-то причине пусто, используем демо-набор,
  //    чтобы страница не была пустой
  if (!seriesData || !seriesData.length) {
    seriesData = [400, 430, 448, 470, 540, 580, 690, 1100, 1200, 1380];
  }
  if (!categories || !categories.length) {
    categories = ["South Korea","Canada","United Kingdom","Netherlands","Italy","France","Japan","United States","China","Germany"];
  }

  // 4) Перед повторным рендером очищаем контейнер, чтобы не наслаивались
  //    две SVG/канваса от vendor-инициализации
  el.innerHTML = "";

  // 5) Опции графика — ровно как в теме, только вместо захардкоженных
  //    массивов подставляем seriesData и categories
  // Этот объект options полностью заменяет прежний.
// Комментарии — как будто их писал новичок.

var options = {
  chart: {
    type: "bar",          // тип графика — столбики
    height: 380,          // высота графика
    toolbar: { show: false } // панель инструментов нам не нужна
  },
  colors: colors,         // цвет берём из data-colors (или дефолтный)
  plotOptions: {
    bar: { horizontal: true } // горизонтальные столбики, как в демо
  },
  dataLabels: { enabled: false }, // надписей прямо на столбиках не рисуем
  series: [
    {
      name: "Total",     // имя ряда данных — будет видно в подсказке
      data: seriesData    // наши числа из БД
    }
  ],
  // В Apex при horizontal категории визуально оказываются слева (ось Y),
  // но задаются всё равно через xaxis.categories — это особенность Apex.
  xaxis: {
    categories: categories,            // подписи (штаты)
    title: { text: "Total Markets" }, // подпись оси X
    labels: {
      // Красиво форматируем числа с пробелами по-русски
      formatter: function (val) {
        var n = Number(val);
        return Number.isFinite(n) ? n.toLocaleString("ru-RU") : val;
      }
    }
  },
  yaxis: {
    title: { text: "Stats" }           // подпись оси Y (для ясности)
  },
  tooltip: { enabled: false },

  grid: { borderColor: "#f1f3fa" },    // лёгкая сетка как в теме
  states: { hover: { filter: "none" } } // без затемнения при ховере
};


  // 6) Рендерим наш график
  var chart = new ApexCharts(el, options);
  chart.render();
  
  // Создаём div-tooltip и добавляем в body
var tip = document.createElement('div');
tip.style.position = 'absolute';
tip.style.zIndex = '10000';
tip.style.display = 'none';
tip.style.pointerEvents = 'none';
tip.style.padding = '6px 8px';
tip.style.borderRadius = '6px';
tip.style.background = '#1f2937';
tip.style.color = '#fff';
tip.style.border = '1px solid rgba(0,0,0,.15)';
tip.style.boxShadow = '0 2px 6px rgba(0,0,0,.12)';
tip.style.fontSize = '12px';
tip.style.lineHeight = '1.25';
document.body.appendChild(tip);

// Подписываемся на событие dataPointMouseEnter
chart.addEventListener("dataPointMouseEnter", function(event, chartContext, config) {
  var label = config.w.globals.labels[config.dataPointIndex] || '';
  var val = config.w.config.series[config.seriesIndex].data[config.dataPointIndex] || 0;
  tip.innerHTML = '<div style="font-weight:600;margin-bottom:2px">'+label+'</div>'+
                  '<div>Total: '+val.toLocaleString("ru-RU")+' Markets</div>';
  tip.style.display = 'block';
});

// Следим за движением мыши
el.addEventListener('mousemove', function(e) {
  if (tip.style.display !== 'none') {
    tip.style.left = (e.pageX + 12) + 'px';
    tip.style.top  = (e.pageY + 12) + 'px';
  }
});

// Скрываем при уходе
chart.addEventListener("dataPointMouseLeave", function() {
  tip.style.display = 'none';
});

})();

