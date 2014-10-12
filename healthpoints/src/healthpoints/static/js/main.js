$(function () {
  /*$("#slider-level").slider({
    value: 0,
    min: 0,
    max: 600,
    step: 100
  });*/

 var select = $( "#level-definition" );
 //$( "#level-definition" ).selectmenu();
 var slider = $( "#slider-level" ).slider({
   min: 0,
   max: 6,
   step: 1,
   range: "min",
   value: select[ 0 ].selectedIndex,
     slide: function( event, ui ) {
     select[ 0 ].selectedIndex = ui.value;
   }
 });
 $( "#level-definition" ).change(function() {
   slider.slider( "value", this.selectedIndex );
 });


  $('.btn-f-share').click(function(event){
    var _this = $(this);

    var request = $.ajax({
      url: '/share/fb/',
      type: 'POST',
      data: 'id='+_this.attr('data-id')
    })
    request.done(function(data){
      _this.removeClass('btn-f-share')
          .addClass('btn-f-link')
          .attr('target', '_blank')
          .attr('href', '#');
    });
  });

  $('.btn-ev-share').click(function(event){
    var _this = $(this);

    var request = $.ajax({
      url: '/share/evernote/',
      type: 'POST',
      data: 'id='+_this.attr('data-id')
    })
    request.done(function(data){
      window.open(data.link);
    });
  });

});

