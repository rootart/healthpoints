'use strict';

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
});