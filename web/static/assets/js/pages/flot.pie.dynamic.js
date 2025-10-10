// static/assets/js/pages/flot.pie.dynamic.js
// --------------------------------------------------------------
// Красивый "пирог" -> донат: подписи СНАРУЖИ, мелкие сегменты в "Другие",
// своя подсказка по ховеру, перерисовка при изменении размеров.
// Код максимально простой, с комментариями.
// --------------------------------------------------------------
(function ($) {
  'use strict';

  $(function () {
    var $el = $('#pie-chart');       // jQuery-объект контейнера
    var el  = $el.get(0);            // сам DOM-элемент (для ResizeObserver)
    if (!$el.length) return;         // если блока нет — выходим
    if (typeof $.plot !== 'function') return; // Flot не подключён — выходим

    // Берём палитру из data-colors (как у темы UBold)
    var colorsAttr = ($el.attr('data-colors') || '').toString();
    var colors = colorsAttr ? colorsAttr.split(',') : ['#4a81d4','#f672a7','#f7b84b','#4fc6e1','#1abc9c'];

    // Безопасный JSON → массив
    function parseArray(str) {
      try { var arr = JSON.parse(str || '[]'); return Array.isArray(arr) ? arr : []; }
      catch (e) { return []; }
    }

    // Данные из атрибутов
    var labels = parseArray($el.attr('data-labels'));
    var values = parseArray($el.attr('data-values'));

    // Выравниваем длины
    var n = Math.min(labels.length, values.length);
    if (!n) return;
    labels = labels.slice(0, n);
    values = values.slice(0, n);

    // Готовим базовые данные для Flot Pie
    var baseSeries = [];
    for (var i = 0; i < n; i++) {
      var val = Number(values[i]);
      baseSeries.push({ label: labels[i] || ('№'+(i+1)), data: Number.isFinite(val) ? val : 0 });
    }

    // Красивые подписи на секторе (короткие): «Категория — 10.5%»
    function labelFormatter(label, series) {
      return '' +
        '<div style="font-size:12px;padding:4px 6px;white-space:nowrap;' +
        'background:#fff;border:1px solid #e3e6ef;border-radius:6px;box-shadow:0 1px 2px rgba(0,0,0,.05)">' +
          '<span style="font-weight:600">'+ label +'</span>' +
          ' — ' + series.percent.toFixed(1) + '%' +
        '</div>';
    }

    // Настройки доната с подписями СНАРУЖИ и объединением мелких
    var baseOptions = {
      series: {
        pie: {
          show: true,
          radius: 0.92,
          innerRadius: 0.55,
          startAngle: -Math.PI/2,
          label: {
            show: false   // <<< подписи отключены
          },
          combine: {
            threshold: 0.055,
            label: 'Others'
          }
        }
      },
      legend: { show: false },   // можно включить легенду, если нужно
      grid:   { hoverable: true, clickable: true },
      colors: colors
    };


    // Рендер и перерисовка
    var plot = null;
    function renderPie() {
      $el.empty(); // чистим контейнер на всякий случай
      plot = $.plot($el, baseSeries, baseOptions);
    }
    renderPie();

    // Перерисовка при ресайзе / коллапсе / изменении размеров контейнера
    var resizeTimer = null;
    $(window).on('resize', function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(renderPie, 120);
    });
    $(document).on('shown.bs.collapse hidden.bs.collapse', function (e) {
      if ($(e.target).find('#pie-chart').length || $(e.target).is('#pie-chart')) {
        setTimeout(renderPie, 50);
      }
    });
    if (window.ResizeObserver && el) {
      var ro = new ResizeObserver(function () {
        clearTimeout(el.__pieROTimeout);
        el.__pieROTimeout = setTimeout(renderPie, 120);
      });
      ro.observe(el);
    }

    // Свой аккуратный tooltip (название + проценты + количество)
    var $tip = $('<div />').css({
      position:'absolute', zIndex:10000, display:'none', pointerEvents:'none',
      padding:'6px 8px', borderRadius:'6px', background:'#1f2937', color:'#fff',
      border:'1px solid rgba(0,0,0,.15)', boxShadow:'0 2px 6px rgba(0,0,0,.12)', fontSize:'12px', lineHeight:'1.25'
    }).appendTo('body');

    $el.on('plothover', function (event, pos, obj) {
      if (!obj) { $tip.hide(); return; }
      var label = obj.series.label || '';
      var percent = (obj.series.percent || 0).toFixed(1) + '%';
      var count = 0;
      try { count = Number(obj.series.data[0][1]) || 0; } catch(e) { count = 0; }
      $tip.html(
        '<div style="font-weight:600;margin-bottom:2px">'+label+'</div>'+
        '<div><span style="opacity:.85">Slice:</span> '+percent+'</div>'+
        '<div><span style="opacity:.85">Total:</span> '+count.toLocaleString('ru-RU')+'</div>'
      ).css({ top: pos.pageY + 12, left: pos.pageX + 12 }).fadeIn(80);
    });
    $el.on('mouseleave', function(){ $tip.hide(); });
  });

})(window.jQuery);
